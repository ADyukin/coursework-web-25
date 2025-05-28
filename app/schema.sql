DROP TABLE IF EXISTS reviews;
DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS games;
DROP TABLE IF EXISTS genres;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS purchases;

CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('buyer', 'author', 'admin') NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE INNODB;

CREATE TABLE genres (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(255) NOT NULL
) ENGINE INNODB;

CREATE TABLE games (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    title VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    system TEXT,
    price DECIMAL(10,2) NOT NULL,
    status ENUM('pending', 'approved', 'rejected') NOT NULL DEFAULT 'pending',
    genre_id INTEGER,
    author_id INTEGER,
    file_path VARCHAR(255),
    image_url VARCHAR(255),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (genre_id) REFERENCES genres(id),
    FOREIGN KEY (author_id) REFERENCES users(id)
) ENGINE INNODB;

CREATE TABLE orders (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    buyer_id INTEGER,
    status ENUM('pending', 'paid', 'canceled') NOT NULL,
    total_amount DECIMAL(10,2) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (buyer_id) REFERENCES users(id)
) ENGINE INNODB;

CREATE TABLE order_items (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    order_id INTEGER,
    game_id INTEGER,
    price DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(id),
    FOREIGN KEY (game_id) REFERENCES games(id)
) ENGINE INNODB;

CREATE TABLE reviews (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    user_id INTEGER,
    game_id INTEGER,
    rating INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
    comment TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (game_id) REFERENCES games(id)
) ENGINE INNODB;

-- Insert data into users table
INSERT INTO users (name, email, password_hash, role, created_at) VALUES 
('admin', 'admin.doe@example.com', SHA2('qwerty', 256), 'buyer', '2025-01-01 10:00:00'),
('John Doe', 'john.doe@example.com', SHA2('qwerty', 256), 'buyer', '2025-01-01 10:00:00'),
('Jane Smith', 'jane.smith@example.com', SHA2('qwerty', 256), 'author', '2025-01-02 12:00:00'),
('Alex Brown', 'alex.brown@example.com', SHA2('qwerty', 256), 'admin', '2025-01-03 14:00:00'),
('Emily Davis', 'emily.davis@example.com', SHA2('qwerty', 256), 'buyer', '2025-01-04 16:00:00'),
('Michael Lee', 'michael.lee@example.com', SHA2('qwerty', 256), 'author', '2025-01-05 18:00:00');

-- Insert data into genres table
INSERT INTO genres (name) VALUES 
('Action'),
('Adventure'),
('Puzzle'),
('Strategy'),
('RPG');

-- Insert data into games table
INSERT INTO games (title, description, price, genre_id, author_id, file_path, image_url, created_at) VALUES 
('Space Quest', 'An exciting space adventure', 19.99, 1, 2, '/files/space_quest.zip', '/images/space_quest.jpg', '2025-02-01 09:00:00'),
('Mystery Manor', 'Solve puzzles in a haunted manor', 14.99, 3, 2, '/files/mystery_manor.zip', '/images/mystery_manor.jpg', '2025-02-02 11:00:00'),
('Dragon Realm', 'Epic RPG adventure', 29.99, 5, 5, '/files/dragon_realm.zip', '/images/dragon_realm.jpg', '2025-02-03 13:00:00'),
('Battle Tactics', 'Strategic warfare game', 24.99, 4, 5, '/files/battle_tactics.zip', '/images/battle_tactics.jpg', '2025-02-04 15:00:00'),
('Jungle Escape', 'Survive the jungle', 9.99, 2, 2, '/files/jungle_escape.zip', '/images/jungle_escape.jpg', '2025-02-05 17:00:00');

-- Insert data into orders table
INSERT INTO orders (buyer_id, status, total_amount, created_at) VALUES 
(1, 'paid', 34.98, '2025-03-01 10:30:00'),
(4, 'pending', 29.99, '2025-03-02 12:30:00'),
(1, 'canceled', 9.99, '2025-03-03 14:30:00'),
(4, 'paid', 44.98, '2025-03-04 16:30:00'),
(1, 'pending', 19.99, '2025-03-05 18:30:00');

-- Insert data into order_items table
INSERT INTO order_items (order_id, game_id, price) VALUES 
(1, 1, 19.99),
(1, 2, 14.99),
(2, 3, 29.99),
(4, 4, 24.99),
(4, 1, 19.99);

-- Insert data into reviews table
INSERT INTO reviews (user_id, game_id, rating, comment, created_at) VALUES 
(1, 1, 4, 'Really fun game!', '2025-04-01 09:00:00'),
(4, 2, 3, 'Good but a bit short.', '2025-04-02 11:00:00'),
(1, 3, 5, 'Best RPG ever!', '2025-04-03 13:00:00'),
(4, 4, 4, 'Great strategy game.', '2025-04-04 15:00:00'),
(1, 5, 2, 'Too difficult for me.', '2025-04-05 17:00:00');

-- Обновляем существующие записи в games
UPDATE games SET status = 'approved' WHERE status IS NULL;