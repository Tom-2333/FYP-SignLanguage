

-- Create database
CREATE DATABASE SL_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Use the database
USE SL_db;

-- Drop tables if they exist
DROP TABLE IF EXISTS categories;
DROP TABLE IF EXISTS words;

-- Create tables
CREATE TABLE categories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    key_name VARCHAR(10) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL
);

CREATE TABLE words (
    id VARCHAR(10) PRIMARY KEY,
    word VARCHAR(255) NOT NULL,
    category_key VARCHAR(10) NOT NULL,
    FOREIGN KEY (category_key) REFERENCES categories(key_name)
);

-- Insert categories
INSERT INTO categories (key_name, name) VALUES
('A', '情感 / 態度 / 感覺'),
('B', '人物 / 家庭 / 社會角色'),
('C', '動作 / 動詞 / 活動'),
('D', '物品 / 東西 / 實體物件'),
('E', '抽象 / 概念 / 關係'),
('F', '地點 / 位置'),
('G', '時間 / 日子 / 單位 / 季節'),
('H', '顏色 / 外觀 / 外貌特徵'),
('I', '食物 / 味道'),
('J', '健康 / 醫療 / 殘疾'),
('K', '量詞 / 數字 / 限定詞 / 疑問詞'),
('L', '設備 / 科技 / 媒體'),
('M', '事件 / 意外 / 慶典'),
('N', '變體 / 重複 / 不確定');

-- Insert words for category A
INSERT INTO words (id, word, category_key) VALUES
('5', '盲', 'A'),
('539', '鐘意', 'A'),
('540', '唔鐘意', 'A'),
('457', '謝謝', 'A'),
('438', '開心', 'A'),
('341', '懲罰', 'A'),
('791', '緊張', 'A'),
('1658', '噓', 'A');

-- Insert words for category B
INSERT INTO words (id, word, category_key) VALUES
('1248', '我', 'B'),
('1495', '你', 'B'),
('491', '同學', 'B'),
('249', '屋企人', 'B'),
('62', '爸爸', 'B'),
('80', '媽媽', 'B'),
('189', '父母', 'B'),
('51', '哥哥', 'B'),
('52', '弟弟', 'B'),
('1547', '姐姐', 'B'),
('1548', '妹妹', 'B'),
('100', '爺爺', 'B'),
('331', '嫲嫲', 'B'),
('146', '兒子', 'B'),
('1665', '女兒', 'B'),
('1449', '老公', 'B'),
('1528', '老婆', 'B'),
('2355', '義工', 'B'),
('492', '同事', 'B');

-- Insert words for category C
INSERT INTO words (id, word, category_key) VALUES
('695', '學習', 'C'),
('184', '睡覺', 'C'),
('772', '幫忙', 'C'),
('2345', '講粗口', 'C'),
('201', '工作', 'C'),
('830', '出糧', 'C'),
('301', '運動', 'C'),
('897', '運動場', 'C'),
('1852', '劍擊', 'C'),
('1171', '鋼琴', 'C');

-- Insert words for category D
INSERT INTO words (id, word, category_key) VALUES
('95', '鑰匙', 'D'),
('2763', '護照', 'D'),
('2125', '紙巾', 'D'),
('569', '摩托車', 'D');

-- Insert words for category E
INSERT INTO words (id, word, category_key) VALUES
('2222', '是', 'E'),
('1643', '不是', 'E'),
('2001', '需要', 'E'),
('2315', '不需要', 'E'),
('274', '願望', 'E'),
('541', '點解', 'E'),
('208', '類別', 'E'),
('629', '句子', 'E'),
('2298', '詞語', 'E'),
('2571', '標籤', 'E'),
('498', '現在', 'E');

-- Insert words for category F
INSERT INTO words (id, word, category_key) VALUES
('446', '學校', 'F'),
('2104', '香港', 'F'),
('1401', '日本', 'F'),
('215', '戰爭', 'F'),
('2560', '衝突', 'F');

-- Insert words for category G
INSERT INTO words (id, word, category_key) VALUES
('1536', '零', 'G'),
('1952', '一', 'G'),
('313', '二', 'G'),
('32', '三', 'G'),
('253', '四', 'G'),
('2195', '六', 'G'),
('2007', '七', 'G'),
('2567', '八', 'G'),
('1732', '九', 'G');

-- Insert words for category H
INSERT INTO words (id, word, category_key) VALUES
('552', '彩虹', 'H');

-- Insert words for category I
INSERT INTO words (id, word, category_key) VALUES
('731', '麵', 'I'),
('743', '咖啡', 'I');

-- Insert words for category J
INSERT INTO words (id, word, category_key) VALUES
('15', '頭痛', 'J'),
('929', '腹瀉', 'J');

-- Insert words for category K
INSERT INTO words (id, word, category_key) VALUES
('464', '什麼', 'K');

-- Insert words for category L
INSERT INTO words (id, word, category_key) VALUES
('4', '助聽器', 'L'),
('2554', '網絡', 'L');