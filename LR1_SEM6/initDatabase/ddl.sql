DROP TABLE IF EXISTS lessons CASCADE;
DROP TABLE IF EXISTS reviews CASCADE;
DROP TABLE IF EXISTS tutors CASCADE;
DROP TABLE IF EXISTS clients CASCADE;
DROP TABLE IF EXISTS subjects CASCADE;

CREATE TABLE subjects (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL
);

CREATE TABLE clients (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    phone_number VARCHAR(50) NOT NULL
);

CREATE TABLE tutors (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    phone_number VARCHAR(50) NOT NULL,
    rating NUMERIC(2,1),
    subject_id INT REFERENCES subjects(id)
);

CREATE TABLE reviews (
    id SERIAL PRIMARY KEY,
    tutor_id INT,
    client_id INT,
    text TEXT NOT NULL,
    rating INT CHECK (rating >= 1 AND rating <= 5)
);

CREATE TABLE lessons (
    id SERIAL PRIMARY KEY,
    tutor_id INT NOT NULL REFERENCES tutors(id),
    client_id INT NOT NULL REFERENCES clients(id),
    start_time TIMESTAMP NOT NULL,
    duration_minutes INT NOT NULL
);
