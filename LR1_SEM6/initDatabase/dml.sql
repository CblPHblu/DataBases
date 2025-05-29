TRUNCATE TABLE lessons, reviews, tutors, clients, subjects RESTART IDENTITY CASCADE;

\copy subjects(id, name) FROM 'data/subjects.csv' DELIMITER ',' CSV HEADER;
\copy clients(id, name, email, phone_number) FROM 'data/clients.csv' DELIMITER ',' CSV HEADER;
\copy tutors(id, name, email, phone_number, rating, subject_id) FROM 'data/tutors.csv' DELIMITER ',' CSV HEADER;
\copy reviews(id, tutor_id, client_id, text, rating) FROM 'data/reviews.csv' DELIMITER ',' CSV HEADER;
\copy lessons(id, tutor_id, client_id, start_time, duration_minutes) FROM 'data/lessons.csv' DELIMITER ',' CSV HEADER;

SELECT COUNT(*) FROM subjects;
SELECT COUNT(*) FROM clients;
SELECT COUNT(*) FROM tutors;
SELECT COUNT(*) FROM reviews;
SELECT COUNT(*) FROM lessons;
