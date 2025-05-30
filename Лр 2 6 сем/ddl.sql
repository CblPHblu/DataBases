CREATE TABLE Users (
    user_id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    first_name VARCHAR(255) NOT NULL,
    last_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE Subject (
    subject_id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    subject_name VARCHAR(255) NOT NULL,
    description TEXT
);

CREATE TABLE Tutors (
    tutor_id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    user_id BIGINT REFERENCES Users(user_id) ON DELETE CASCADE,
    description TEXT,
    rating DECIMAL(3, 2) DEFAULT 0.0,
    hourly_rate DECIMAL(10, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    subject_id BIGINT REFERENCES Subject(subject_id) ON DELETE SET NULL
);

CREATE TABLE Responses (
    response_id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    request_id BIGINT,
    tutor_id BIGINT REFERENCES Tutors(tutor_id),
    message TEXT,
    response_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE Requests (
    request_id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    client_id BIGINT REFERENCES Users(user_id),
    subject_id BIGINT REFERENCES Subject(subject_id),
    description TEXT,
    budget DECIMAL(10, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    selected_response_id BIGINT REFERENCES Responses(response_id)
);

ALTER TABLE Responses
ADD CONSTRAINT fk_request
FOREIGN KEY (request_id)
REFERENCES Requests(request_id);


CREATE TABLE Reviews (
    review_id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    client_id BIGINT REFERENCES Users(user_id) ON DELETE CASCADE,
    tutor_id BIGINT REFERENCES Tutors(tutor_id) ON DELETE CASCADE,
    review_text TEXT NOT NULL,
    rating DECIMAL(3, 2) NOT NULL,
    review_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE Schedules (
    schedule_id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    tutor_id BIGINT REFERENCES Tutors(tutor_id) ON DELETE CASCADE,
    day_of_week VARCHAR(50) NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL
);
