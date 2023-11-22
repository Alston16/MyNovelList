from flask import Flask, render_template, request, redirect, url_for, session
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re
from flask_bcrypt import Bcrypt 


app = Flask(__name__)


app.secret_key = 'your secret key'

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'mysql'
app.config['MYSQL_DB'] = 'MyNovelList'
app.config['TEMPLATES_AUTO_RELOAD'] = True

mysql = MySQL(app)
bcrypt = Bcrypt(app) 

@app.route('/')
def base():
	if 'id' in session:
		return redirect(url_for('home'))
	return redirect(url_for('login'))

@app.route('/login', methods =['GET', 'POST'])
def login():
	msg = ''
	admin=False
	if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
		username = request.form['username']
		if(len(username)>6 and username.startswith('admin@')):
			admin=True
			username=username[6:]
		password = request.form['password'] 
		cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
		if(admin):
			cursor.execute('SELECT * FROM admin_ WHERE admin_name = % s', (username, ))
		else:
			cursor.execute('SELECT * FROM user WHERE username = % s', (username, ))
		account = cursor.fetchone()
		if account and bcrypt.check_password_hash(account['passwd'], password):
			session['loggedin'] = True
			if(admin):
				session['id'] = account['admin_id']
				session['username'] = account['admin_name']
			else:
				session['id'] = account['user_id']
				session['username'] = account['UserName']
			msg = 'Logged in successfully !'
			if(admin):
				session['admin']=True
				return redirect(url_for('admin'))
			return redirect(url_for('home'))
		else:
			msg = 'Incorrect username / password !'
	return render_template('login.html', msg = msg)

@app.route('/logout')
def logout():
	session.pop('loggedin', None)
	session.pop('id', None)
	session.pop('username', None)
	return redirect(url_for('login'))

@app.route('/register', methods =['GET', 'POST'])
def register():
	msg = ''
	success=False
	if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form :
		username = request.form['username']
		password = request.form['password']
		hashed_password = bcrypt.generate_password_hash (password).decode('utf-8') 
		email = request.form['email']
		cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
		cursor.execute('SELECT * FROM user WHERE UserName = % s', (username, ))
		account = cursor.fetchone()
		if not username or not password or not email:
			msg = 'Please enter values in all the fields!'
		elif account:
			msg = 'Account already exists !'
		elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
			msg = 'Invalid email address !'
		elif not re.match(r'[A-Za-z0-9]+', username):
			msg = 'Username must contain only characters and numbers !'
		else:
			cursor.execute('INSERT INTO user VALUES (NULL , % s, % s, % s)', (username, email, hashed_password, ))
			mysql.connection.commit()
			success=True
			msg = 'You have successfully registered !'
	elif request.method == 'POST':
		msg = 'Please fill out the form !'
	return render_template('register.html', msg = msg, success=success)

@app.route('/home')
def home():
	if 'id' not in session:
		return redirect(url_for('login'))
	search_query=''
	if 'search' in request.args:
		search_query=request.args.get('search')
	pgno=1
	if 'pgno' in request.args:
		pgno=int(request.args.get('pgno'))
	cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
	cursor.execute(f"""
SELECT name,
    img,
    author_name,
    rating,
    authortype
FROM (
        SELECT novel.novel_name AS name,
            novel.novel_image AS img,
            author.author_name,
            GetAverageRatingForNovel(novel.novel_id) AS rating,
            author.author_type as authortype
        FROM novel
            INNER JOIN author ON author.author_id = novel.author_id
        WHERE author.author_type = 'Novel'
		AND novel.novel_name LIKE "%{search_query}%"
        UNION ALL
        SELECT webnovel.webnovel_name AS name,
            webnovel.webnovel_image AS img,
            author.author_name,
            GetAverageRatingForWebNovel(webnovel.webnovel_id) AS rating,
            author.author_type as authortype
        FROM webnovel
            INNER JOIN author ON author.author_id = webnovel.author_id
        WHERE author.author_type = 'WebNovel'
		AND webnovel.webnovel_name LIKE "%{search_query}%"
    ) AS combined_results
ORDER BY rating DESC
LIMIT 10 OFFSET {(pgno-1)*10};
""")
	results = cursor.fetchall()
	return render_template('home.html',search_query=search_query,results=results,pgno=pgno)

@app.route('/lists/<type>/<status>')
def lists(type='Novels',status='All'):
	if 'id' not in session:
		return redirect(url_for('login'))
	search_query=''
	if 'search' in request.args:
		search_query=request.args.get('search')
	cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
	if type=='Novels':
		cursor.execute(f"""
select novel.novel_id,
novel_image as img,
novel_name as name,
author_name as author,
Rating as rating,
pages_read as progress,
total_pages as total
from novel,author,user_reads_novel
where user_id={session['id']}
and user_reads_novel.novel_id=novel.novel_id
and novel.author_id=author.author_id
and novel_name like "%{search_query}%"
{'' if status=='All' else "and user_status='"+status+"'"}
;
""")
	else:
		cursor.execute(f"""
select webnovel.webnovel_id,
webnovel_image as img,
webnovel_name as name,
author_name as author,
Rating as rating,
chapters_read as progress,
total_chapters as total
from webnovel,author,user_reads_webnovel
where user_id={session['id']}
and user_reads_webnovel.webnovel_id=webnovel.webnovel_id
and webnovel.author_id=author.author_id
and webnovel_name like "%{search_query}%"
{'' if status=='All' else "and user_status='"+status+"'"}
;
""")
	results=cursor.fetchall()
	return render_template('lists.html',type=type,status=status,results=results)

@app.route('/social')
def social():
	if 'id' not in session:
		return redirect(url_for('login'))
	search_query=''
	if 'search' in request.args:
		search_query=request.args.get('search')
	pgno=1
	if 'pgno' in request.args:
		pgno=int(request.args.get('pgno'))
	cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
	cursor.execute(f"""
select UserName,isFriend({session['id']},user_id) as isFriend
from user
where user_id!={session['id']}
and UserName like "%{search_query}%"
order by isFriend desc
limit 10 offset {(pgno-1)*10}
;
""")
	results=cursor.fetchall()
	return render_template('social.html',results=results,pgno=pgno)

@app.route('/profile/<username>')
def profile(username='Guest'):
	if 'id' not in session:
		return redirect(url_for('login'))
	cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
	cursor.execute(f"""
select a.user_id,a.username,
(select count(*) from user b where isFriend(a.user_id,b.user_id)=1) as numf,
(select count(*) from user_reads_novel c where c.user_id=a.user_id) as numn,
(select count(*) from user_reads_webnovel d where d.user_id=a.user_id) as numw,
isFriend(a.user_id,{session['id']}) as isf
from user as a
where a.username='{username}'
;
""")
	user=cursor.fetchone()
	return render_template('profile.html',user=user)

@app.route('/novel/<novel_type>/<name>')
def novel(name,novel_type):
	if 'id' not in session:
		return redirect(url_for('login'))
	cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
	if novel_type=='Novel':
		cursor.execute(f"SELECT user_id,novel.novel_id FROM user_reads_novel,novel where user_id={session['id']} AND novel_name='{name}' AND user_reads_novel.novel_id=novel.novel_id")
		inList=bool(cursor.fetchone())
	else:
		cursor.execute(f"SELECT user_id,webnovel.webnovel_id FROM user_reads_webnovel,webnovel where user_id={session['id']} AND webnovel_name='{name}' AND user_reads_webnovel.webnovel_id=webnovel.webnovel_id")
		inList=bool(cursor.fetchone())
	if novel_type=='Novel':
		cursor.execute(f"""
select novel.novel_id,
novel_image as img,
novel_name as name,
author_name as author,
group_concat(genre) as genres,
GetAverageRatingForNovel(novel.novel_id) as rating,
total_pages as pages,
summary
from novel,novel_genre,author
where novel_name='{name}'
and novel.author_id=author.author_id
and novel.novel_id=novel_genre.novel_id
group by novel.novel_id
;
""")
		result=cursor.fetchone()
	else:
		cursor.execute(f"""
select webnovel.webnovel_id,
webnovel_image as img,
webnovel_name as name,
status_ as status,
author_name as author,
group_concat(genre) as genres,
GetAverageRatingForWebNovel(webnovel.webnovel_id) as rating,
total_chapters as chapters,
summary
from webnovel,webnovel_genre,author
where webnovel_name='{name}'
and webnovel.author_id=author.author_id
and webnovel.webnovel_id=webnovel_genre.webnovel_id
group by webnovel.webnovel_id
;
""")
		result=cursor.fetchone()
	return render_template('novel.html',novel_type=novel_type,name=name,result=result,inList=inList)

@app.route('/admin',methods=['GET','POST'])
def admin():
	if 'admin' not in session:
		return redirect(url_for('login'))
	search_query=''
	if 'search' in request.args:
		search_query=request.args.get('search')
	cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
	cursor.execute(f"""
select id,name,img,type
from(
select novel_id as id,novel_name as name,novel_image as img,'Novel' as type
from novel
where novel_name like "%{search_query}%"
union all
select webnovel_id as id,webnovel_name as name,webnovel_image as img,'Webnovel' as type
from webnovel
where webnovel_name like "%{search_query}%"
) as T
limit 100;
""")
	results = cursor.fetchall()
	cursor = mysql.connection.cursor()
	if request.method=='POST':
		custom_query=request.form.get('query')
		cursor.execute(custom_query)
		cust_res=cursor.fetchall()
		print(cust_res)
	else:
		cust_res=[]
	return render_template('admin.html',results=results,cust_res=cust_res)

@app.route('/addtoList/<novel_type>/<name>/<id>',methods=['GET','POST'])
def addToList(novel_type,name,id):
	cursor = mysql.connection.cursor()
	if novel_type=='Novel':
		cursor.execute("INSERT INTO user_reads_novel VALUES(%s,%s,%s,%s,%s)",(session['id'],id,request.form['score'] if request.form['score'] else None,request.form['status'].replace('-',' '),request.form['progress']))
		mysql.connection.commit()
	else:
		cursor.execute("INSERT INTO user_reads_webnovel VALUES(%s,%s,%s,%s,%s)",(session['id'],id,request.form['score'] if request.form['score'] else None,request.form['status'].replace('-',' '),request.form['progress']))
		mysql.connection.commit()
	return redirect(url_for('novel',novel_type=novel_type,name=name))

@app.route('/removeFromList/<novel_type>/<name>/<id>')
def removeFromList(novel_type,name,id):
	cursor = mysql.connection.cursor()
	if novel_type=='Novel':
		cursor.execute("DELETE FROM user_reads_novel WHERE user_id=%s AND novel_id=%s",(session['id'],id))
		mysql.connection.commit()
	else:
		cursor.execute("DELETE FROM user_reads_webnovel WHERE user_id=%s AND webnovel_id=%s",(session['id'],id))
		mysql.connection.commit()
	return redirect(url_for('novel',novel_type=novel_type,name=name))

@app.route('/addProgress/<type>/<status>/<id>')
def addProgress(type,status,id):
	cursor = mysql.connection.cursor()
	if type=='Novels':
		cursor.execute("UPDATE user_reads_novel SET pages_read=pages_read+1 WHERE user_id=%s AND novel_id=%s",(session['id'],id))
		mysql.connection.commit()
	else:
		cursor.execute("UPDATE user_reads_webnovel SET chapters_read=chapters_read+1 WHERE user_id=%s AND webnovel_id=%s",(session['id'],id))
		mysql.connection.commit()
	return redirect(url_for('lists',type=type,status=status))

@app.route('/addAdmin', methods =['GET', 'POST'])
def addAdmin():
	msg = ''
	success=False
	if request.method == 'POST' and 'adminUsername' in request.form and 'password' in request.form and 'adminEmail' in request.form :
		username = request.form['adminUsername']
		password = request.form['password']
		hashed_password = bcrypt.generate_password_hash (password).decode('utf-8') 
		email = request.form['adminEmail']
		cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
		cursor.execute('SELECT * FROM admin_ WHERE admin_name = % s', (username, ))
		account = cursor.fetchone()
		if not username or not password or not email:
			msg = 'Please enter values in all the fields!'
		elif account:
			msg = 'Account already exists !'
		elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
			msg = 'Invalid email address !'
		elif not re.match(r'[A-Za-z0-9]+', username):
			msg = 'Username must contain only characters and numbers !'
		else:
			cursor.execute('INSERT INTO admin_ VALUES (NULL , % s, % s, % s)', (username, email, hashed_password, ))
			mysql.connection.commit()
			success=True
			msg = 'You have successfully registered !'
	elif request.method == 'POST':
		msg = 'Please fill out the form !'
	return render_template('admin.html', msg = msg, success=success)

@app.route('/addFriend/<username>/<id>')
def addFriend(username,id):
	cursor = mysql.connection.cursor()
	cursor.execute("INSERT INTO user_friends VALUES(%s,%s)",(session['id'],id))
	mysql.connection.commit()
	return redirect(url_for('profile',username=username))

@app.route('/removeFriend/<username>/<id>')
def removeFriend(username,id):
	cursor = mysql.connection.cursor()
	cursor.execute("DELETE FROM user_friends WHERE (user1_id=%s AND user2_id=%s) OR (user2_id=%s AND user1_id=%s)",(session['id'],id,session['id'],id))
	mysql.connection.commit()
	return redirect(url_for('profile',username=username))

@app.route('/addNovel',methods=['GET','POST'])
def addNovel():
	cursor = mysql.connection.cursor()
	cursor.execute("call GetNovelAuthorId(%s,@aid)",(request.form['novelAuthor'],))
	cursor.execute("SELECT @aid")
	aid=cursor.fetchone()[0]
	cursor.execute("INSERT INTO novel VALUES(NULL,%s,%s,%s,%s,%s)",(request.form['novelName'],request.form['novelImage'],request.form['novelDescription'],request.form['novelPages'],aid))
	mysql.connection.commit()
	cursor.execute("SELECT * FROM novel WHERE novel_name=%s",(request.form['novelName'],))
	nid=cursor.fetchone()[0]
	for genre in request.form.getlist('novelGenre'):
		cursor.execute('INSERT INTO novel_genre VALUES(%s,%s)',(nid,genre))
		mysql.connection.commit()
	return redirect(url_for('admin'))

@app.route('/addWebnovel',methods=['GET','POST'])
def addWebnovel():
	cursor = mysql.connection.cursor()
	cursor.execute("call GetWebNovelAuthorId(%s,@aid)",(request.form['webNovelAuthor'],))
	cursor.execute("SELECT @aid")
	aid=cursor.fetchone()[0]
	cursor.execute("INSERT INTO webnovel VALUES(NULL,%s,%s,%s,%s,%s,%s)",(request.form['webNovelName'],request.form['webNovelImage'],request.form['webNovelDescription'],request.form['webNovelChapters'],request.form['webNovelStatus'],aid))
	mysql.connection.commit()
	cursor.execute("SELECT * FROM webnovel WHERE webnovel_name=%s",(request.form['webNovelName'],))
	wid=cursor.fetchone()[0]
	for genre in request.form.getlist('webNovelGenre'):
		cursor.execute('INSERT INTO webnovel_genre VALUES(%s,%s)',(wid,genre))
		mysql.connection.commit()
	return redirect(url_for('admin'))

@app.route('/deleteNovel/<novel_type>/<id>')
def deleteNovel(novel_type,id):
	cursor = mysql.connection.cursor()
	if novel_type=='Novel':
		cursor.execute("DELETE FROM novel WHERE novel_id=%s",(id,))
		mysql.connection.commit()
	else:
		cursor.execute("DELETE FROM webnovel WHERE webnovel_id=%s",(id,))
		mysql.connection.commit()
	return redirect(url_for('admin'))

@app.route('/addChapters/<id>')
def addChapters(id):
	cursor = mysql.connection.cursor()
	cursor.execute("UPDATE webnovel SET total_chapters=total_chapters+1 WHERE webnovel_id=%s",(id,))
	mysql.connection.commit()
	return redirect(url_for('admin'))

if __name__=='__main__':
	app.run()
