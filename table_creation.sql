drop database if exists MyNovelList;
create database MyNovelList;
use MyNovelList;
create table author(
    author_id int primary key auto_increment,
    author_name varchar(255) not null,
    author_type enum ('Novel', 'WebNovel') not null,
    UNIQUE KEY unique_author_name_type (author_name, author_type)
);
create table user(
    user_id int primary key auto_increment,
    UserName varchar(30) unique not null,
    email varchar(40) unique not null,
    passwd varchar(70) not null
);
create table admin_(
    admin_id int primary key auto_increment,
    admin_name varchar(30) unique not null,
    email varchar(40) unique not null,
    passwd varchar(70) not null
);
create table Novel(
    novel_id int primary key auto_increment,
    novel_name varchar(255) not null,
    novel_image varchar(255) not null,
    summary mediumtext not null,
    total_pages int not null,
    author_id int not null,
    foreign key (author_id) references author(author_id) on update cascade on delete cascade,
    UNIQUE KEY unique_novel_name (novel_name, author_id)
);
create table WebNovel(
    webnovel_id int primary key auto_increment,
    webnovel_name varchar(255) not null,
    webnovel_image varchar(255) not null,
    summary mediumtext not null,
    total_chapters int not null,
    status_ enum ('Ongoing', 'Complete', 'Hiatus', 'Dropped') not null,
    author_id int not null,
    foreign key (author_id) references author(author_id) on update cascade on delete cascade,
    UNIQUE KEY unique_webnovel_name (webnovel_name, author_id)
);
create table user_friends(
    user1_id int,
    user2_id int,
    primary key (user1_id, user2_id),
    foreign key (user1_id) references user(user_id) on update cascade on delete cascade,
    foreign key (user2_id) references user(user_id) on update cascade on delete cascade
);
create table novel_genre(
    novel_id int,
    genre enum (
        'Romance',
        'Fantasy',
        'Fiction',
        'Nonfiction',
        'Historical',
        'Childrens',
        'Mystery',
        'Religion',
        'Cultural',
        'Literature',
        'Young Adult',
        'Paranormal',
        'Science Fiction',
        'Thriller',
        'Adventure',
        'Humor',
        'Erotica',
        'Classics',
        'Horror',
        'Crime',
        'Sports',
        'Action',
        'Comedy'
    ),
    primary key(novel_id, genre),
    foreign key (novel_id) references Novel(novel_id) on update cascade on delete cascade
);
create table webnovel_genre(
    webnovel_id int,
    genre enum (
        'Fantasy',
        'Science Fiction',
        'Romance',
        'Mystery',
        'Slice of Life',
        'Adventure',
        'Xianxia',
        'Isekai',
        'Gaming',
        'Horror',
        'Harem',
        'Superhero',
        'Supernatural',
        'Historical',
        'Drama',
        'Comedy',
        'Tragedy',
        'Sports',
        'Martial Arts',
        'Gender Bender',
        'Psychological',
        'Cultivation',
        'Time Travel',
        'Political',
        'Action',
        'Ecchi',
        'Reincarnation',
        'Thriller',
        'School',
        'Revenge',
        'Anti-Hero'
    ),
    primary key(webnovel_id, genre),
    foreign key (webnovel_id) references WebNovel(webnovel_id) on update cascade on delete cascade
);
create table user_reads_novel(
    user_id int,
    novel_id int,
    Rating int default NULL,
    user_status enum (
        'Reading',
        'Completed',
        'Plan to Read',
        'Dropped',
        'On Hold'
    ) not null,
    pages_read int default 0,
    primary key(user_id, novel_id),
    foreign key (user_id) references user(user_id) on update cascade on delete cascade,
    foreign key (novel_id) references novel(novel_id) on update cascade on delete cascade
);
create table user_reads_webnovel(
    user_id int,
    webnovel_id int,
    Rating int default NULL,
    user_status enum (
        'Reading',
        'Completed',
        'Plan to Read',
        'Dropped',
        'On Hold'
    ) not null,
    chapters_read int default 0,
    primary key(user_id, webnovel_id),
    foreign key (user_id) references user(user_id) on update cascade on delete cascade,
    foreign key (webnovel_id) references webnovel(webnovel_id) on update cascade on delete cascade
);