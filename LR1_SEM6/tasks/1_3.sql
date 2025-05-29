
-- 1. Индекс GIN + pg_trgm

DO $$
BEGIN
  RAISE NOTICE 'Создание GIN-индекса для pg_trgm';
END
$$;
DROP INDEX IF EXISTS idx_reviews_text_trgm;
CREATE INDEX idx_reviews_text_trgm ON reviews USING GIN (text gin_trgm_ops);

DO $$
BEGIN
  RAISE NOTICE '->Подсчёт отзывов, похожих на great';
END
$$;
SELECT count(*) AS similar_trgm_count
FROM reviews
WHERE text % 'great';

-- Показать несколько таких отзывов
SELECT id, similarity(text, 'great') AS sim
FROM reviews
WHERE text % 'great'
ORDER BY sim DESC
LIMIT 3;


-- 2. Индекс GIN + pg_bigm для LIKE

DO $$
BEGIN
  RAISE NOTICE '->Создание GIN-индекса для pg_bigm';
END
$$;
DROP INDEX IF EXISTS idx_reviews_text_bigram;
CREATE INDEX idx_reviews_text_bigram ON reviews USING GIN (text gin_bigm_ops);

DO $$
BEGIN
  RAISE NOTICE '->Подсчёт отзывов с подстрокой learn';
END
$$;
SELECT count(*) AS like_count
FROM reviews
WHERE text LIKE '%learn%';

-- Показать несколько таких отзывов
SELECT id, text
FROM reviews
WHERE text LIKE '%learn%'
LIMIT 3;


-- 3. Шифрование email клиентов (pgcrypto) — DEMO 1000 строк

DO $$
BEGIN
  RAISE NOTICE '-> Удаляю таблицу secure_clients';
  EXECUTE 'DROP TABLE IF EXISTS secure_clients';

  RAISE NOTICE '-> Создаю secure_clients (1000 строк)';
  EXECUTE $sql$
    CREATE TABLE secure_clients AS
    SELECT id,
           name,
           phone_number,
           pgp_sym_encrypt(email, 'secret_key') AS email_encrypted
    FROM clients
    ORDER BY id
    LIMIT 1000
  $sql$;

  RAISE NOTICE '-> Подсчёт строк в secure_clients';
  RAISE NOTICE '% rows in secure_clients', (SELECT COUNT(*) FROM secure_clients);
END
$$;

-- Пример расшифровки 5 строк
SELECT id,
       name,
       pgp_sym_decrypt(email_encrypted, 'secret_key') AS decrypted_email
FROM secure_clients
LIMIT 5;
