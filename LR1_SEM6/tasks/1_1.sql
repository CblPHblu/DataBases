
-- Анализ запросов ДО индексации

-- По дате начала занятий (до индекса)
EXPLAIN ANALYZE
SELECT * FROM lessons WHERE start_time BETWEEN '2024-01-01' AND '2025-01-01';

-- По email клиента (до индекса)
EXPLAIN ANALYZE
SELECT * FROM clients WHERE email = 'shaneandersen@example.org';

-- По части имени преподавателя (до индекса)
EXPLAIN ANALYZE
SELECT * FROM tutors WHERE name ILIKE '%Katherine%';

-- По ключевому слову в отзыве (до индекса)
EXPLAIN ANALYZE
SELECT * FROM reviews WHERE text ILIKE '%laugh%';

-- По рейтингу преподавателя (до индекса)
EXPLAIN ANALYZE
SELECT * FROM tutors WHERE rating > 4.5;

-- Создание индексов


-- B-TREE индексы
CREATE INDEX IF NOT EXISTS idx_clients_email ON clients(email);
CREATE INDEX IF NOT EXISTS idx_tutors_rating ON tutors(rating);

-- GIN индексы (через pg_trgm)
CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE INDEX IF NOT EXISTS idx_tutors_name_trgm
    ON tutors USING GIN(name gin_trgm_ops);

CREATE INDEX IF NOT EXISTS idx_reviews_text_trgm
    ON reviews USING GIN(text gin_trgm_ops);

-- Анализ таблиц для обновления статистики
ANALYZE;


-- Повторный анализ запросов ПОСЛЕ индексации


-- По дате начала занятий (после индекса) — всё ещё Seq Scan без BRIN/Btree
EXPLAIN ANALYZE
SELECT * FROM lessons WHERE start_time BETWEEN '2024-01-01' AND '2025-01-01';

-- По email клиента (после индекса)
EXPLAIN ANALYZE
SELECT * FROM clients WHERE email = 'shaneandersen@example.org';

-- По части имени преподавателя (после индекса)
EXPLAIN ANALYZE
SELECT * FROM tutors WHERE name ILIKE '%Katherine%';

-- По ключевому слову в отзыве (после индекса)
EXPLAIN ANALYZE
SELECT * FROM reviews WHERE text ILIKE '%laugh%';

-- По рейтингу преподавателя (после индекса)
EXPLAIN ANALYZE
SELECT * FROM tutors WHERE rating > 4.5;
