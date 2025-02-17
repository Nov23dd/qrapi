CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE
);

CREATE TABLE qr_codes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    text TEXT NOT NULL,
    qr_code TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    FOREIGN KEY (username) REFERENCES users (username)
);

CREATE TABLE user_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    qr_data TEXT NOT NULL,
    FOREIGN KEY (username) REFERENCES users (username)
);