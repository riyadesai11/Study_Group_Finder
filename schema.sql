DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS subjects;
DROP TABLE IF EXISTS user_subjects;
DROP TABLE IF EXISTS groups;
DROP TABLE IF EXISTS group_members;

CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    prn TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    skill_level TEXT NOT NULL
);

CREATE TABLE subjects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL
);

CREATE TABLE user_subjects (
    user_id INTEGER NOT NULL,
    subject_id INTEGER NOT NULL,
    PRIMARY KEY (user_id, subject_id),
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
    FOREIGN KEY (subject_id) REFERENCES subjects (id) ON DELETE CASCADE
);

CREATE TABLE groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    subject_id INTEGER NOT NULL,
    creator_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (subject_id) REFERENCES subjects (id),
    FOREIGN KEY (creator_id) REFERENCES users (id)
);

CREATE TABLE group_members (
    group_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (group_id, user_id),
    FOREIGN KEY (group_id) REFERENCES groups (id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);

-- Pre-populate some predefined subjects
INSERT INTO subjects (name) VALUES 
('SQL'), ('Python'), ('Java'), ('Linux'), 
('AWS'), ('Big Data'), ('R'), ('Aptitude'),
('Data Visualisation'), ('Statistics');

