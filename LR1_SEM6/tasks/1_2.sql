
-- Явная ТРАНЗАКЦИЯ: регистрация клиента и добавление отзыва
BEGIN;


INSERT INTO clients (name, email, phone_number)
VALUES ('Иван Иванов', 'ivan.ivanov@example.com', '+7-900-123-45-67');


INSERT INTO reviews (client_id, text)
SELECT id, 'Очень доволен занятием!'
FROM clients
WHERE email = 'ivan.ivanov@example.com';

COMMIT;


-- ТРАНЗАКЦИЯ с ОТКАТОМ: попытка добавить дублирующий email

BEGIN;


INSERT INTO clients (name, email, phone_number)
VALUES ('Дубль Иван', 'ivan.ivanov@example.com', '+7-900-765-43-21');

ROLLBACK;


-- ТРАНЗАКЦИЯ с SAVEPOINT: частичный откат

BEGIN;

INSERT INTO clients (name, email, phone_number)
VALUES ('Анна Смирнова', 'anna.smirnova@example.com', '+7-999-111-22-33');


SAVEPOINT sp1;


INSERT INTO clients (name, email, phone_number)
VALUES ('Другая Анна', 'anna.smirnova@example.com', '+7-999-444-55-66');


ROLLBACK TO sp1;


INSERT INTO reviews (client_id, text)
SELECT id, 'Отличный преподаватель!'
FROM clients
WHERE email = 'anna.smirnova@example.com';

COMMIT;
