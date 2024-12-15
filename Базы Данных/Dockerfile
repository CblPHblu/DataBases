# Используем официальный образ PostgreSQL
FROM postgres:latest

# Копируем файлы ddl.sql и init_subjects.sql в контейнер
COPY ddl.sql /docker-entrypoint-initdb.d/
COPY init_data.sql /docker-entrypoint-initdb.d/

# Устанавливаем переменные окружения для базы данных
ENV POSTGRES_DB=tutoring_service
ENV POSTGRES_USER=postgres
ENV POSTGRES_PASSWORD=yourpassword

# Открываем порт 5432 для доступа к базе данных
EXPOSE 5432
