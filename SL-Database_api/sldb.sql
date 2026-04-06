-- Drop database if exists
DROP DATABASE IF EXISTS SL_db;

-- Create database
CREATE DATABASE SL_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Use the database
USE SL_db;

-- Drop tables if they exist
DROP TABLE IF EXISTS user_progress;
DROP TABLE IF EXISTS chat_history;
DROP TABLE IF EXISTS words;
DROP TABLE IF EXISTS categories;
DROP TABLE IF EXISTS users;

-- Create tables
CREATE TABLE categories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    key_name VARCHAR(10) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    name_en VARCHAR(255) NOT NULL
);

CREATE TABLE words (
    id VARCHAR(10) PRIMARY KEY,
    word VARCHAR(255) NOT NULL,
    engword VARCHAR(255) NOT NULL,
    category_key VARCHAR(10) NOT NULL,
    FOREIGN KEY (category_key) REFERENCES categories(key_name)
);

-- Users table
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert a test user (email: abc@gmail.com, password: 123456)
-- Password stored as bcrypt hash so PHP `password_verify` works with this entry
INSERT INTO users (email, username, password_hash) VALUES
('abc@gmail.com', 'abc', '$2y$10$yqCC0l.aqSfwhiXKgBt8C.PXACaoK9E8SLEyqUMyqPARkkbsQuIi2');

-- Learning progress (e.g., word recognition confidence)
CREATE TABLE user_progress (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    word_id VARCHAR(10) NOT NULL,
    confidence INT DEFAULT 0,  -- e.g., 85 for 85%
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (word_id) REFERENCES words(id) ON DELETE CASCADE
);

-- Chat history
CREATE TABLE chat_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    session_id VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    role ENUM('user', 'assistant') NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Insert categories
INSERT INTO categories (key_name, name, name_en) VALUES
('A', '情感 / 態度 / 感覺', 'Emotions / Attitudes / Feelings'),
('B', '人物 / 家庭 / 社會角色', 'People / Family / Social Roles'),
('C', '動作 / 動詞 / 活動', 'Actions / Verbs / Activities'),
('D', '物品 / 東西 / 實體物件', 'Objects / Things / Physical Items'),
('E', '抽象 / 概念 / 關係', 'Abstract Concepts / Relations'),
('F', '地點 / 位置', 'Places / Locations'),
('G', '時間 / 日子 / 單位 / 季節', 'Time / Days / Units / Seasons'),
('H', '顏色 / 外觀 / 外貌特徵', 'Colors / Appearance / Physical Features'),
('I', '食物 / 味道', 'Food / Taste'),
('J', '健康 / 醫療 / 殘疾', 'Health / Medical / Disability'),
('K', '量詞 / 數字 / 限定詞 / 疑問詞', 'Classifiers / Numbers / Determiners / Question Words'),
('L', '設備 / 科技 / 媒體', 'Equipment / Technology / Media');

-- Insert words for category A (情感 / 態度 / 感覺)
INSERT INTO words (id, word, engword, category_key) VALUES
('451', '你好', 'hello', 'A'),
('539', '鐘意', 'to like', 'A'),
('540', '唔鐘意', 'dislike', 'A'),
('457', '謝謝', 'thank you', 'A'),
('239', '對不起', 'sorry', 'A'),
('438', '開心', 'happy', 'A'),
('1620', '再見', 'bye', 'A'),
('2001', 'ok', 'ok', 'A'),
('40', '好', 'good', 'A'),
('860', '想', 'want', 'A'),
('1656', '不想', 'dont want', 'A'),
('3108', '厲害', 'impressive', 'A'),
('791', '緊張', 'nervous', 'A'),
('231', '肚餓', 'hungry', 'A'),
('739', '渴', 'thirsty', 'A'),
('608', '飽', 'full', 'A'),
('2073', '愛', 'love', 'A'),
('1', '傷心', 'sad', 'A'),
('56', '生氣', 'angry', 'A'),
('945', '害怕', 'scared', 'A'),
('448', '累', 'tired', 'A'),
('810', '舒服', 'comfortable', 'A'),
('365', '冷', 'cold', 'A'),
('558', '熱', 'hot', 'A'),
('12', '最鍾意', 'favorite', 'A'),
('309', '感覺', 'feel', 'A'),
('110', '溫暖', 'warm', 'A'),
('112', '不開心', 'unhappy', 'A');

-- Insert words for category B (人物 / 家庭 / 社會角色)
INSERT INTO words (id, word, engword, category_key) VALUES
('491', '同學', 'classmate', 'B'),
('249', '屋企人', 'family', 'B'),
('1248', '我', 'me', 'B'),
('429', '護士', 'nurse', 'B'),
('53', '人', 'person', 'B'),
('640', '醫生', 'doctor', 'B'),
('62', '爸爸', 'father', 'B'),
('80', '媽媽', 'mother', 'B'),
('189', '父母', 'parents', 'B'),
('51', '哥哥', 'brother', 'B'),
('52', '弟弟', 'brother', 'B'),
('1547', '姐姐', 'sister', 'B'),
('1548', '妹妹', 'sister', 'B'),
('100', '爺爺', 'grandfather', 'B'),
('146', '兒子', 'son', 'B'),
('1665', '女兒', 'daughter', 'B'),
('1449', '老公', 'husband', 'B'),
('1528', '老婆', 'wife', 'B'),
('2185', '我們', 'we', 'B'),
('1495', '你', 'you', 'B'),
('492', '同事', 'colleague', 'B'),
('634', '文職', 'office admin', 'B'),
('2355', '義工', 'volunteer', 'B'),
('476', '朋友', 'friend', 'B'),
('489', '老師', 'teacher', 'B');

-- Insert words for category C (動作 / 動詞 / 活動)
INSERT INTO words (id, word, engword, category_key) VALUES
('085', '等等', 'wait', 'C'),
('626', '見面', 'meet', 'C'),
('341', '懲罰', 'punish', 'C'),
('772', '幫忙', 'help', 'C'),
('201', '工作', 'work', 'C'),
('830', '出糧', 'pay salary', 'C'),
('1852', '劍擊', 'fencing', 'C'),
('301', '運動', 'exercise', 'C'),
('695', '學習', 'study', 'C'),
('184', '睡覺', 'sleep', 'C'),
('82', '喝', 'drink', 'C'),
('1438', '介紹', 'introduce', 'C'),
('1565', '買', 'buy', 'C'),
('474', '教', 'teach', 'C'),
('1300', '睇', 'see', 'C'),
('76', '吃', 'eat', 'C'),
('2505', '會去', 'will go', 'C'),
('1945', '帶', 'bring', 'C'),
('97', '嘗試', 'try', 'C');

-- Insert words for category D (物品 / 東西 / 實體物件)
INSERT INTO words (id, word, engword, category_key) VALUES
('2125', '紙巾', 'tissue', 'D'),
('1478', '頭盔', 'helmet', 'D'),
('1171', '鋼琴', 'piano', 'D'),
('569', '摩托車', 'motorcycle', 'D'),
('1146', '功課', 'homework', 'D');

-- Insert words for category E (抽象 / 概念 / 關係)
INSERT INTO words (id, word, engword, category_key) VALUES
('458', '手語', 'sign language', 'E'),
('3154', '高級', 'advanced', 'E'),
('199', '有', 'have', 'E'),
('274', '願望', 'wish', 'E'),
('208', '類別', 'class', 'E'),
('2222', '是', 'yes', 'E'),
('1643', '不是', 'not', 'E'),
('1301', '需要', 'need', 'E'),
('2315', '不需要', 'dont need', 'E'),
('629', '句子', 'sentence', 'E'),
('2298', '詞語', 'vocabulary', 'E'),
('2571', '標籤', 'label', 'E'),
('586', '平', 'cheap', 'E'),
('286', '貴', 'expensive', 'E'),
('7', '責任', 'responsibility', 'E'),
('2097', '齊', 'together', 'E'),
('2295', '失敗', 'fail', 'E'),
('602', '成功', 'success', 'E');

-- Insert words for category F (地點 / 位置)
INSERT INTO words (id, word, engword, category_key) VALUES
('446', '學校', 'school', 'F'),
('2104', '香港', 'hongkong', 'F'),
('597', '遠', 'far', 'F'),
('598', '近', 'near', 'F'),
('883', '左', 'left', 'F'),
('884', '右', 'right', 'F'),
('1729', '上面', 'on', 'F'),
('882', '下', 'beneath', 'F'),
('263', '前', 'front', 'F'),
('886', '後', 'back', 'F'),
('90', '醫院', 'hospital', 'F');

-- Insert words for category G (時間 / 日子 / 單位 / 季節)
INSERT INTO words (id, word, engword, category_key) VALUES
('498', '現在', 'now', 'G'),
('165', '假期', 'vacation', 'G'),
('431', '星期一', 'monday', 'G'),
('87', '星期五', 'friday', 'G'),
('2311', '上個星期', 'last week', 'G'),
('3021', '星期日', 'Sunday', 'G'),
('3061', '星期二', 'tuesday', 'G'),
('26', '最後', 'last', 'G'),
('60', '分鐘', 'minute', 'G');

-- Insert words for category H (顏色 / 外觀 / 外貌特徵)
INSERT INTO words (id, word, engword, category_key) VALUES
('552', '彩虹', 'rainbow', 'H'),
('594', '大', 'big', 'H'),
('595', '小', 'small', 'H'),
('393', '快', 'fast', 'H'),
('105', '慢', 'slow', 'H'),
('128', '新', 'new', 'H'),
('612', '舊', 'old', 'H'),
('240', '美麗', 'pretty', 'H'),
('776', '聰明', 'clever', 'H'),
('2190', '強壯', 'strong', 'H'),
('362', '弱', 'weak', 'H');

-- Insert words for category I (食物 / 味道)
INSERT INTO words (id, word, engword, category_key) VALUES
('731', '麵', 'noodle', 'I'),
('743', '咖啡', 'coffee', 'I'),
('1844', '早餐', 'breakfast', 'I'),
('1100', '茶', 'tea', 'I'),
('1006', '牛奶', 'milk', 'I'),
('555', '水', 'water', 'I'),
('68', '美味', 'delicious', 'I');

-- Insert words for category J (健康 / 醫療 / 殘疾)
INSERT INTO words (id, word, engword, category_key) VALUES
('452', '聾人', 'deaf', 'J'),
('327', '健聽', 'hearing', 'J'),
('15', '頭痛', 'headache', 'J'),
('929', '腹瀉', 'diarrhea', 'J'),
('5', '盲', 'blind', 'J'),
('58', '病', 'sick', 'J'),
('403', '痛', 'pain', 'J');

-- Insert words for category K (量詞 / 數字 / 限定詞 / 疑問詞)
INSERT INTO words (id, word, engword, category_key) VALUES
('541', '點解', 'why', 'K'),
('464', '什麼', 'what', 'K'),
('1536', '零', 'zero', 'K'),
('1952', '一', 'one', 'K'),
('313', '二', 'two', 'K'),
('32', '三', 'three', 'K'),
('253', '四', 'four', 'K'),
('2195', '六', 'six', 'K'),
('2007', '七', 'seven', 'K'),
('1732', '九', 'nine', 'K'),
('98', '哪裡', 'where', 'K');

-- Insert words for category L (設備 / 科技 / 媒體)
INSERT INTO words (id, word, engword, category_key) VALUES
('1088', '電話', 'telephone', 'L'),
('25', '電影', 'film', 'L'),
('2554', '網絡', 'network', 'L'),
('4', '助聽器', 'hearing aid', 'L');