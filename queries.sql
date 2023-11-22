-- Function to get rating for novel
DELIMITER && 
CREATE FUNCTION GetAverageRatingForNovel(novelid INT) RETURNS float(4, 2) DETERMINISTIC BEGIN
DECLARE total_rating INT;
DECLARE rating_count INT;
DECLARE average_rating FLOAT(4, 2);
SELECT SUM(rating),
    COUNT(*) INTO total_rating,
    rating_count
FROM user_reads_novel
WHERE novel_id = novelid
    AND rating is not null;
IF rating_count > 0 THEN
SET average_rating = total_rating / rating_count;
ELSE
SET average_rating = 5;
END IF;
RETURN average_rating;
END;
&& 
DELIMITER ;
--
-- Function to get rating for webnovel
DELIMITER && 
CREATE FUNCTION GetAverageRatingForWebNovel(webnovelid INT) RETURNS float(4, 2) DETERMINISTIC BEGIN
DECLARE total_rating INT;
DECLARE rating_count INT;
DECLARE average_rating FLOAT(4, 2);
SELECT SUM(rating),
    COUNT(*) INTO total_rating,
    rating_count
FROM user_reads_webnovel
WHERE webnovel_id = webnovelid
    AND rating is not null;
IF rating_count > 0 THEN
SET average_rating = total_rating / rating_count;
ELSE
SET average_rating = 5;
END IF;
RETURN average_rating;
END;
&& 
DELIMITER ;
--
DELIMITER && 
CREATE FUNCTION isFriend(userid INT,friendid INT) RETURNS INT DETERMINISTIC BEGIN
DECLARE friend INT;
SELECT COUNT(*) INTO friend
FROM user_friends
WHERE (user1_id=userid AND user2_id=friendid) 
OR (user1_id=friendid AND user2_id=userid);
RETURN friend;
END;
&& 
DELIMITER ;
-- Query to fetch 10 rows from novel
SELECT novel.novel_name,
    novel.novel_image,
    author.author_name,
    GetAverageRatingForNovel(novel.novel_id) AS rating
FROM novel
    INNER JOIN author ON author.author_id = novel.author_id
WHERE author.author_type = 'Novel'
ORDER BY rating DESC
LIMIT 10;
--
-- Query to fetch 10 rows from webnovel
SELECT webnovel.webnovel_name,
    webnovel.webnovel_image,
    author.author_name,
    GetAverageRatingForWebNovel(webnovel.webnovel_id) AS rating
FROM webnovel
    INNER JOIN author ON author.author_id = webnovel.author_id
WHERE author.author_type = 'WebNovel'
ORDER BY rating DESC
LIMIT 10;
--
-- Query to fetch top 10 novels and webnovels
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
        UNION ALL
        SELECT webnovel.webnovel_name AS name,
            webnovel.webnovel_image AS img,
            author.author_name,
            GetAverageRatingForWebNovel(webnovel.webnovel_id) AS rating,
            author.author_type as authortype
        FROM webnovel
            INNER JOIN author ON author.author_id = webnovel.author_id
        WHERE author.author_type = 'WebNovel'
    ) AS combined_results
ORDER BY rating DESC
LIMIT 10;
--
-- Update user status to completed
DELIMITER && 
CREATE TRIGGER UpdateUserStatusToCompleted
BEFORE
UPDATE ON user_reads_webnovel FOR EACH ROW BEGIN
DECLARE total INT;
SELECT webnovel.total_chapters INTO total
FROM webnovel
WHERE webnovel_id=OLD.webnovel_id;
IF OLD.chapters_read+1 >= total THEN
SET NEW.user_status = 'Completed';
END IF;
END;
&& 
DELIMITER ;
--

DELIMITER && 
CREATE TRIGGER UpdateUserStatusToCompletedForNovel
BEFORE
UPDATE ON user_reads_novel FOR EACH ROW BEGIN
DECLARE total INT;
SELECT novel.total_pages INTO total
FROM novel where novel_id = NEW.novel_id;
IF NEW.pages_read >= total THEN
SET NEW.user_status = 'Completed', NEW.pages_read = total;
END IF;
END;
&& 
DELIMITER ;
-- Update user status to ongoing
DELIMITER && 
CREATE TRIGGER UpdateUserStatusToReading
AFTER
UPDATE ON webnovel FOR EACH ROW BEGIN IF NEW.total_chapters > OLD.total_chapters THEN
UPDATE user_reads_webnovel
SET user_status = 'Reading'
WHERE webnovel_id = NEW.webnovel_id;
END IF;
END;
&& 
DELIMITER ;
--
-- Insert new novel author
DELIMITER &&
CREATE PROCEDURE GetNovelAuthorId(
    IN p_author_name VARCHAR(255),
    OUT p_author_id INT
)
BEGIN
    DECLARE author_id_exist INT;
    SELECT author_id INTO author_id_exist
    FROM author
    WHERE author_name = p_author_name and author_type = 'Novel';
    IF author_id_exist IS NOT NULL THEN
        SET p_author_id = author_id_exist;
    ELSE
        INSERT INTO author (author_name, author_type) VALUES (p_author_name, 'Novel');
        SET p_author_id = LAST_INSERT_ID();
    END IF;
END;
&&
DELIMITER ;
--
-- Insert new webnovel author
DELIMITER &&
CREATE PROCEDURE GetWebNovelAuthorId(
    IN p_author_name VARCHAR(255),
    OUT p_author_id INT
)
BEGIN
    DECLARE author_id_exist INT;
    SELECT author_id INTO author_id_exist
    FROM author
    WHERE author_name = p_author_name and author_type = 'WebNovel';
    IF author_id_exist IS NOT NULL THEN
        SET p_author_id = author_id_exist;
    ELSE
        INSERT INTO author (author_name, author_type) VALUES (p_author_name, 'WebNovel');
        SET p_author_id = LAST_INSERT_ID();
    END IF;
END;
&&
DELIMITER ;