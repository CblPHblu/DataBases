import streamlit as st
import psycopg2
from psycopg2 import sql
import redis
import uuid
from werkzeug.security import generate_password_hash, check_password_hash
import os
import subprocess
import json

redis_client = redis.StrictRedis(host='localhost', port=6379, db=0, decode_responses=True)

def create_backup():
    backup_dir = "backups"
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    backup_file = os.path.join(backup_dir, "backup.sql")
    container_name = "tutoring_service_db"

    # Создаем директорию /backups внутри контейнера
    create_dir_command = f"docker exec {container_name} mkdir -p /backups"
    subprocess.run(create_dir_command, shell=True)

    command = f"docker exec -i {container_name} pg_dump -U postgres -F c -b -v -f /backups/backup.sql tutoring_service"
    result = subprocess.run(command, shell=True, input=b'yourpassword\n', stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    if result.returncode == 0:
        # Копируем архивную копию из контейнера на хост
        copy_command = f"docker cp {container_name}:/backups/backup.sql {backup_file}"
        subprocess.run(copy_command, shell=True)
        st.success("Архивная копия базы данных создана успешно!")
    else:
        error_message = result.stderr.decode() if result.stderr else "Нет информации об ошибке"
        st.error(f"Ошибка при создании архивной копии базы данных: {error_message}")

def restore_backup():
    backup_file = "backups/backup.sql"
    container_name = "tutoring_service_db"

    # Копируем архивную копию в контейнер
    copy_command = f"docker cp {backup_file} {container_name}:/backups/backup.sql"
    subprocess.run(copy_command, shell=True)

    # Проверяем существование базы данных и удаляем её, если она существует
    drop_db_command = f"docker exec -i {container_name} psql -U postgres -c \"DROP DATABASE IF EXISTS tutoring_service_restored;\""
    drop_db_result = subprocess.run(drop_db_command, shell=True, input=b'yourpassword\n', stderr=subprocess.PIPE, stdout=subprocess.PIPE)

    if drop_db_result.returncode != 0:
        drop_db_error_message = drop_db_result.stderr.decode() if drop_db_result.stderr else "Нет информации об ошибке"
        st.error(f"Ошибка при удалении базы данных: {drop_db_error_message}")
        return

    # Создаем пустую базу данных
    create_db_command = f"docker exec -i {container_name} psql -U postgres -c \"CREATE DATABASE tutoring_service_restored;\""
    create_db_result = subprocess.run(create_db_command, shell=True, input=b'yourpassword\n', stderr=subprocess.PIPE, stdout=subprocess.PIPE)

    if create_db_result.returncode != 0:
        create_db_error_message = create_db_result.stderr.decode() if create_db_result.stderr else "Нет информации об ошибке"
        st.error(f"Ошибка при создании базы данных: {create_db_error_message}")
        return

    # Восстанавливаем базу данных из архивной копии без использования опции --clean
    restore_command = f"docker exec -i {container_name} pg_restore -U postgres -d tutoring_service_restored --no-owner -v /backups/backup.sql"
    restore_result = subprocess.run(restore_command, shell=True, input=b'yourpassword\n', stderr=subprocess.PIPE, stdout=subprocess.PIPE)

    if restore_result.returncode == 0:
        st.success("База данных восстановлена успешно!")
    else:
        restore_error_message = restore_result.stderr.decode() if restore_result.stderr else "Нет информации об ошибке"
        st.error(f"Ошибка при восстановлении базы данных: {restore_error_message}")

# Функция для подключения к базе данных
def get_connection():
    return psycopg2.connect(
        dbname="tutoring_service",
        user="postgres",
        password="yourpassword",
        host="localhost",
        port="5432"
    )

# Функция для инициализации базы данных
def initialize_database():
    with get_connection() as conn:
        with conn.cursor() as cursor:
            # Создание представления
            cursor.execute("""
            CREATE OR REPLACE VIEW TutorRatings AS
            SELECT
                t.user_id,
                u.first_name,
                u.last_name,
                t.rating,
                t.hourly_rate,
                s.subject_name
            FROM
                Tutors t
            JOIN
                Users u ON t.user_id = u.user_id
            JOIN
                Subject s ON t.subject_id = s.subject_id;
            """)

            # Создание триггера
            cursor.execute("""
            CREATE OR REPLACE FUNCTION update_tutor_rating_after_review()
            RETURNS TRIGGER AS $$
            BEGIN
                UPDATE Tutors
                SET rating = (
                    SELECT AVG(rating)
                    FROM Reviews
                    WHERE tutor_id = NEW.tutor_id
                )
                WHERE tutor_id = NEW.tutor_id;
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;

            CREATE OR REPLACE TRIGGER update_tutor_rating_trigger
            AFTER INSERT OR UPDATE ON Reviews
            FOR EACH ROW
            EXECUTE FUNCTION update_tutor_rating_after_review();
            """)

            # Создание функции
            cursor.execute("""
            CREATE OR REPLACE FUNCTION get_average_tutor_rating(tutor_id INT)
            RETURNS FLOAT AS $$
            DECLARE
                avg_rating FLOAT;
            BEGIN
                SELECT AVG(rating) INTO avg_rating
                FROM Reviews
                WHERE tutor_id = tutor_id;
                RETURN avg_rating;
            END;
            $$ LANGUAGE plpgsql;
            """)

            # Создание хранимой процедуры
            cursor.execute("""
            CREATE OR REPLACE PROCEDURE add_tutor_with_schedule(
                IN p_user_id INT,
                IN p_subject_id INT,
                IN p_description TEXT,
                IN p_hourly_rate FLOAT,
                IN p_day_of_week TEXT,
                IN p_start_time TIME,
                IN p_end_time TIME
            )
            LANGUAGE plpgsql
            AS $$
            BEGIN
                INSERT INTO Tutors (user_id, subject_id, description, hourly_rate)
                VALUES (p_user_id, p_subject_id, p_description, p_hourly_rate);

                INSERT INTO Schedules (tutor_id, day_of_week, start_time, end_time)
                VALUES (
                    (SELECT tutor_id FROM Tutors WHERE user_id = p_user_id),
                    p_day_of_week,
                    p_start_time,
                    p_end_time
                );
            END;
            $$;
            """)

            conn.commit()


def email_exists(email):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1 FROM Users WHERE email = %s", [email])
            return cursor.fetchone() is not None

def register_user(first_name, last_name, email, password, role):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            hashed_password = generate_password_hash(password)
            cursor.execute(
                "INSERT INTO Users (first_name, last_name, email, password_hash, role) VALUES (%s, %s, %s, %s, %s)",
                (first_name, last_name, email, hashed_password, role)
            )
            conn.commit()

def authenticate_user(email, password):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM Users WHERE email = %s", [email])
            user = cursor.fetchone()
            if user and check_password_hash(user[4], password):
                return user
    return None

def get_user_info(user_id):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT first_name, last_name, email, role FROM Users WHERE user_id = %s", [user_id])
            return cursor.fetchone()

def get_tutors():
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT t.user_id, u.first_name, u.last_name, t.description, t.rating, t.hourly_rate FROM Tutors t JOIN Users u ON t.user_id = u.user_id")
            tutors = cursor.fetchall()
            for tutor in tutors:
                tutor_id = tutor[0]
                update_tutor_rating(tutor_id)
            return tutors

def get_subjects():
    cached_subjects = redis_client.get("subjects_cache")
    if cached_subjects:
        return json.loads(cached_subjects)

    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT subject_id, subject_name FROM Subject")
            subjects = cursor.fetchall()
            redis_client.setex("subjects_cache", 300, json.dumps(subjects))  # кэш на 5 минут
            return subjects

def create_request(client_id, subject_id, description, budget):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO Requests (client_id, subject_id, description, budget) VALUES (%s, %s, %s, %s)",
                (client_id, subject_id, description, budget)
            )
            # Уведомление о новой заявке
            redis_client.publish("events", f"Новая заявка от клиента {client_id} на предмет {subject_id}")
            conn.commit()

def get_user_requests(client_id):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM Requests WHERE client_id = %s", [client_id])
            return cursor.fetchall()

def get_tutor_info(tutor_id):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT t.description, t.rating, t.hourly_rate, t.subject_id FROM Tutors t WHERE t.user_id = %s", [tutor_id])
            return cursor.fetchone()

def add_tutor_info(tutor_id, subject_id, description, hourly_rate):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO Tutors (user_id, subject_id, description, hourly_rate) VALUES (%s, %s, %s, %s)",
                (tutor_id, subject_id, description, hourly_rate)
            )
            conn.commit()

def get_requests_by_subject(subject_id):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM Requests WHERE subject_id = %s", [subject_id])
            return cursor.fetchall()

def create_response(request_id, tutor_user_id, message):
    tutor_id = get_tutor_id_by_user_id(tutor_user_id)
    if tutor_id is None:
        st.error("Информация о репетиторе не найдена.")
        return

    if response_exists(request_id, tutor_id):
        st.error("Вы уже откликнулись на эту заявку.")
        return

    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO Responses (request_id, tutor_id, message) VALUES (%s, %s, %s)",
                (request_id, tutor_id, message)
            )
            conn.commit()
            st.success("Отклик создан успешно!")

def edit_user_profile(user_id, first_name, last_name, email):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "UPDATE Users SET first_name = %s, last_name = %s, email = %s WHERE user_id = %s",
                (first_name, last_name, email, user_id)
            )
            conn.commit()

def delete_request(request_id):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM Requests WHERE request_id = %s", [request_id])
            conn.commit()

def get_responses_for_request(request_id):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT r.response_id, u.first_name, u.last_name, r.message, r.response_date, r.tutor_id
                FROM Responses r
                JOIN Tutors t ON r.tutor_id = t.tutor_id
                JOIN Users u ON t.user_id = u.user_id
                WHERE r.request_id = %s
                """,
                [request_id]
            )
            return cursor.fetchall()

def add_review(client_id, tutor_user_id, review_text, rating):
    tutor_id = get_tutor_id_by_user_id(tutor_user_id)
    if tutor_id is None:
        st.error("Репетитор с данным user_id не существует.")
        return False

    if review_exists(client_id, tutor_id):
        st.error("Вы уже оставили отзыв для этого репетитора.")
        return False

    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO Reviews (client_id, tutor_id, review_text, rating, review_date) VALUES (%s, %s, %s, %s, NOW())",
                (client_id, tutor_id, review_text, rating)
            )
            conn.commit()

            remove_duplicate_reviews()

            update_tutor_rating(tutor_id)

    return True

def add_schedule(tutor_user_id, day_of_week, start_time, end_time):
    tutor_id = tutor_user_id
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO Schedules (tutor_id, day_of_week, start_time, end_time) VALUES (%s, %s, %s, %s)",
                (tutor_id, day_of_week, start_time, end_time)
            )
            conn.commit()

def tutor_exists(tutor_id):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1 FROM Tutors WHERE tutor_id = %s", [tutor_id])
            return cursor.fetchone() is not None

def get_tutor_id_by_user_id(user_id):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT tutor_id FROM Tutors WHERE user_id = %s", [user_id])
            tutor_id = cursor.fetchone()
            return tutor_id[0] if tutor_id else None

def get_tutor_rating(tutor_id):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT rating FROM Tutors WHERE tutor_id = %s", [tutor_id])
            rating = cursor.fetchone()
            return rating[0] if rating else None

def update_tutor_rating(tutor_id):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT AVG(r.rating) as avg_rating
                FROM Reviews r
                WHERE r.tutor_id = %s
                """,
                [tutor_id]
            )
            result = cursor.fetchone()
            if result:
                avg_rating = result[0]
                if avg_rating is not None:
                    cursor.execute(
                        "UPDATE Tutors SET rating = %s WHERE tutor_id = %s",
                        (avg_rating, tutor_id)
                    )
                    conn.commit()

def get_tutor_reviews(tutor_id):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT r.review_id, u.first_name, u.last_name, r.review_text, r.rating, r.review_date
                FROM Reviews r
                JOIN Users u ON r.client_id = u.user_id
                WHERE r.tutor_id = %s
                ORDER BY r.review_date DESC
                """,
                [tutor_id]
            )
            return cursor.fetchall()

def get_tutor_schedule(tutor_id):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT schedule_id, day_of_week, start_time, end_time
                FROM Schedules
                WHERE tutor_id = %s
                ORDER BY day_of_week, start_time
                """,
                [tutor_id]
            )
            schedule = cursor.fetchall()
            return schedule

def review_exists(client_id, tutor_id):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT 1 FROM Reviews WHERE client_id = %s AND tutor_id = %s",
                (client_id, tutor_id)
            )
            return cursor.fetchone() is not None

def remove_duplicate_reviews():
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                WITH ranked_reviews AS (
                    SELECT
                        review_id,
                        client_id,
                        tutor_id,
                        ROW_NUMBER() OVER (PARTITION BY client_id, tutor_id ORDER BY review_date DESC) as rn
                    FROM Reviews
                )
                DELETE FROM Reviews
                WHERE review_id IN (
                    SELECT review_id FROM ranked_reviews WHERE rn > 1
                );
                """
            )
            conn.commit()

def response_exists(request_id, tutor_id):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT 1 FROM Responses WHERE request_id = %s AND tutor_id = %s",
                (request_id, tutor_id)
            )
            return cursor.fetchone() is not None

def get_tutor_profile(tutor_id):
    update_tutor_rating(tutor_id)
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT t.description, t.rating, t.hourly_rate, u.first_name, u.last_name
                FROM Tutors t
                JOIN Users u ON t.user_id = u.user_id
                WHERE t.tutor_id = %s
                """,
                [tutor_id]
            )
            profile = cursor.fetchone()
            return profile

def get_tutor_rating_and_reviews_count(tutor_id):
    update_tutor_rating(tutor_id)  
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT AVG(r.rating) as avg_rating, COUNT(r.review_id) as reviews_count
                FROM Reviews r
                WHERE r.tutor_id = %s
                """,
                [tutor_id]
            )
            result = cursor.fetchone()
            if result:
                return result[0], result[1]
    return 0, 0

def get_subject_name(subject_id):
    conn = get_connection()
    if conn is None:
        return None
    cursor = conn.cursor()
    cursor.execute("SELECT subject_name FROM Subject WHERE subject_id = %s", [subject_id])
    subject_name = cursor.fetchone()
    cursor.close()
    conn.close()
    return subject_name[0] if subject_name else None


def get_all_requests():
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT r.request_id, u.first_name, u.last_name, s.subject_name, r.description, r.budget, r.created_at FROM Requests r JOIN Users u ON r.client_id = u.user_id JOIN Subject s ON r.subject_id = s.subject_id")
            return cursor.fetchall()

def get_tutors_count():
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM Tutors")
            return cursor.fetchone()[0]

def get_clients_count():
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM Users WHERE role = 'client'")
            return cursor.fetchone()[0]

def get_responses_count():
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM Responses")
            return cursor.fetchone()[0]

def get_requests_count():
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM Requests")
            return cursor.fetchone()[0]

def get_clients():
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT user_id, first_name, last_name, email FROM Users WHERE role = 'client'")
            return cursor.fetchall()

def delete_user(user_id):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("UPDATE Reviews SET client_id = NULL WHERE client_id = %s", [user_id])

            cursor.execute("SELECT tutor_id FROM Reviews WHERE client_id = %s", [user_id])
            tutor_ids = cursor.fetchall()
            for tutor_id in tutor_ids:
                update_tutor_rating(tutor_id[0])

            cursor.execute("DELETE FROM Users WHERE user_id = %s", [user_id])

            cursor.execute("DELETE FROM Tutors WHERE user_id = %s", [user_id])

            cursor.execute("DELETE FROM Responses WHERE tutor_id = (SELECT tutor_id FROM Tutors WHERE user_id = %s)", [user_id])

            cursor.execute("DELETE FROM Requests WHERE client_id = %s", [user_id])

            cursor.execute("DELETE FROM Schedules WHERE tutor_id = (SELECT tutor_id FROM Tutors WHERE user_id = %s)", [user_id])

            conn.commit()

def main():
    st.set_page_config(page_title="Сервис поиска репетитора", page_icon="📚")

    initialize_database()
    # Проверка авторизации по токену Redis
    if st.session_state.get("auth_token"):
        user_id = redis_client.get(f"auth_token:{st.session_state['auth_token']}")
        if not user_id:
            st.warning("Сессия истекла, пожалуйста, войдите снова.")
            st.session_state['logged_in'] = False
            st.session_state['auth_token'] = None
            st.rerun()

    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False

    if not st.session_state['logged_in']:
        st.sidebar.title("Выберите действие")
        page = st.sidebar.selectbox("Выберите действие", ["Регистрация", "Вход"])

        if page == "Регистрация":
            st.header("Регистрация")
            first_name = st.text_input("Имя")
            last_name = st.text_input("Фамилия")
            email = st.text_input("Email")
            password = st.text_input("Пароль", type="password")
            confirm_password = st.text_input("Повторите пароль", type="password")
            role = st.selectbox("Кто вы?", ["Я ищу репетитора", "Я репетитор", "Я админ"])

            if st.button("Зарегистрироваться"):
                if email_exists(email):
                    st.error("Email уже зарегистрирован.")
                elif password != confirm_password:
                    st.error("Пароли не совпадают.")
                else:
                    role_mapping = {"Я ищу репетитора": "client", "Я репетитор": "tutor", "Я админ": "admin"}
                    register_user(first_name, last_name, email, password, role_mapping[role])
                    st.success("Регистрация успешна! Пожалуйста, войдите в свой аккаунт.")

        elif page == "Вход":
            st.header("Вход")
            login_email = st.text_input("Email")
            login_password = st.text_input("Пароль", type="password")
            if st.button("Войти"):
                user = authenticate_user(login_email, login_password)
                if user:
                    token = str(uuid.uuid4())
                    redis_client.setex(f"auth_token:{token}", 3600, user[0])  # TTL: 1 час
                    st.session_state['logged_in'] = True
                    st.session_state['user_id'] = user[0]
                    st.session_state['user_role'] = user[5]
                    st.session_state['auth_token'] = token
                    st.rerun()
                else:
                    st.error("Неверный email или пароль")
    else:
        user_info = get_user_info(st.session_state['user_id'])
        if st.session_state['user_role'] == 'client':
            st.title(f"Добро пожаловать, {user_info[0]} {user_info[1]}")

            st.sidebar.title("Меню")
            menu = st.sidebar.radio("Выберите действие", ["Мой аккаунт", "Выбрать репетитора", "Создать заявку", "Мои заявки"])

            if menu == "Мой аккаунт":
                st.markdown(
                    f"""
                    <div style="background-color: #f9f9f9; padding: 20px; border-radius: 10px; box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);">
                        <h2 style="color: #333;">Мой аккаунт</h2>
                        <p><strong>Имя:</strong> {user_info[0]}</p>
                        <p><strong>Фамилия:</strong> {user_info[1]}</p>
                        <p><strong>Email:</strong> {user_info[2]}</p>
                        <p><strong>Роль:</strong> {user_info[3]}</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                new_first_name = st.text_input("Новое имя", user_info[0])
                new_last_name = st.text_input("Новая фамилия", user_info[1])
                new_email = st.text_input("Новый email", user_info[2])
                if st.button("Сохранить изменения"):
                    edit_user_profile(st.session_state['user_id'], new_first_name, new_last_name, new_email)
                    st.success("Профиль успешно обновлен!")
                    st.rerun()
                if st.button("Выйти"):
                    token = st.session_state.get("auth_token")
                    if token:
                        redis_client.delete(f"auth_token:{token}")
                    st.session_state.clear()
                    st.rerun()

            elif menu == "Выбрать репетитора":
                tutors = get_tutors()
                for tutor in tutors:
                    st.write(f"Имя: {tutor[1]} {tutor[2]}")
                    st.write(f"Описание: {tutor[3]}")
                    st.write(f"Рейтинг: {tutor[4]:.2f}")
                    st.write(f"Стоимость за час: {tutor[5]}")
                    review_text = st.text_area(f"Отзыв для {tutor[1]} {tutor[2]}")
                    rating = st.number_input(f"Рейтинг для {tutor[1]} {tutor[2]}", min_value=1, max_value=5)
                    if st.button(f"Добавить отзыв для {tutor[1]} {tutor[2]}", key=f"add_review_{tutor[0]}"):
                        if add_review(st.session_state['user_id'], tutor[0], review_text, rating):
                            st.success("Отзыв добавлен успешно!")
                            update_tutor_rating(tutor[0])
                    st.write("---")

            elif menu == "Создать заявку":
                subjects = get_subjects()
                subject_options = {subject[1]: subject[0] for subject in subjects}
                subject_name = st.selectbox("Выберите предмет", list(subject_options.keys()))
                subject_id = subject_options[subject_name]
                description = st.text_area("Описание")
                budget = st.number_input("Бюджет", min_value=0, step=100)
                if st.button("Создать заявку"):
                    create_request(st.session_state['user_id'], subject_id, description, budget)
                    st.success("Заявка создана успешно!")

            elif menu == "Мои заявки":
                requests = get_user_requests(st.session_state['user_id'])
                if not requests:
                    st.write("Вы ещё не создавали ни одной заявки")
                else:
                    for request in requests:
                        subject_name = next(subject[1] for subject in get_subjects() if subject[0] == request[2])
                        created_at = request[5].strftime("%Y-%m-%d %H:%M")
                        st.write(f"ID заявки: {request[0]}")
                        st.write(f"Предмет: {subject_name}")
                        st.write(f"Описание: {request[3]}")
                        st.write(f"Бюджет: {request[4]}")
                        st.write(f"Дата создания: {created_at}")

                        responses = get_responses_for_request(request[0])
                        if responses:
                            if st.button(f"Посмотреть отклики для заявки {request[0]}", key=f"view_responses_{request[0]}"):
                                st.write("Отклики:")
                                for response in responses:
                                    with st.expander(f"Репетитор: {response[1]} {response[2]}"):
                                        st.write(f"ID отклика: {response[0]}")
                                        st.write(f"Сообщение: {response[3]}")
                                        st.write(f"Дата отклика: {response[4].strftime('%Y-%m-%d %H:%M')}")

                                        tutor_id = response[5]

                                        update_tutor_rating(tutor_id)

                                        tutor_profile = get_tutor_profile(tutor_id)
                                        if tutor_profile:
                                            st.write("Информация о репетиторе:")
                                            st.write(f"Описание: {tutor_profile[0]}")
                                            st.write(f"Стоимость за час: {tutor_profile[2]}")
                                            st.write(f"Имя: {tutor_profile[3]} {tutor_profile[4]}")

                                        rating, reviews_count = get_tutor_rating_and_reviews_count(tutor_id)
                                        st.write(f"Рейтинг: {rating:.2f}")  
                                        st.write(f"Количество отзывов: {reviews_count}")
                                        conn = get_connection()
                                        cursor = conn.cursor()
                                        cursor.execute(
                                            "SELECT email FROM Users WHERE user_id = (SELECT user_id FROM Tutors WHERE tutor_id = %s)",
                                            [tutor_id]
                                        )
                                        tutor_email = cursor.fetchone()
                                        cursor.close()
                                        conn.close()
                                        if tutor_email:
                                            st.write(f"Email репетитора: {tutor_email[0]}")
                                        else:
                                            st.write("Email репетитора не найден")
                                st.write("---")
                        if st.button(f"Удалить заявку {request[0]}", key=f"delete_request_{request[0]}"):
                            delete_request(request[0])
                            st.success("Заявка удалена успешно!")
                            st.rerun()
                        st.write("---")

        elif st.session_state['user_role'] == 'tutor':
            tutor_info = get_tutor_info(st.session_state['user_id'])
            if not tutor_info:
                st.title(f"Добро пожаловать, {user_info[0]} {user_info[1]}")
                st.write("Пожалуйста, добавьте информацию о себе:")
                subjects = get_subjects()
                subject_options = {subject[1]: subject[0] for subject in subjects}
                subject_name = st.selectbox("Выберите предмет", list(subject_options.keys()))
                subject_id = subject_options[subject_name]
                description = st.text_area("Описание")
                hourly_rate = st.number_input("Ставка за час", min_value=0, step=100)
                if st.button("Добавить информацию"):
                    add_tutor_info(st.session_state['user_id'], subject_id, description, hourly_rate)
                    st.success("Информация добавлена успешно!")
                    st.rerun()
            else:
                st.title(f"Добро пожаловать, {user_info[0]} {user_info[1]}")
                st.sidebar.title("Меню")
                menu = st.sidebar.radio("Выберите действие", ["Мой аккаунт", "Заявки", "Мои отзывы", "Моё расписание"])

                if menu == "Мой аккаунт":
                    subject_name = get_subject_name(tutor_info[3])
                    st.markdown(
                        f"""
                        <div style="background-color: #f9f9f9; padding: 20px; border-radius: 10px; box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);">
                            <h2 style="color: #333;">Мой аккаунт</h2>
                            <p><strong>Имя:</strong> {user_info[0]}</p>
                            <p><strong>Фамилия:</strong> {user_info[1]}</p>
                            <p><strong>Email:</strong> {user_info[2]}</p>
                            <p><strong>Роль:</strong> {user_info[3]}</p>
                            <p><strong>Предмет:</strong> {subject_name}</p>
                            <p><strong>Описание:</strong> {tutor_info[0]}</p>
                            <p><strong>Стоимость за час:</strong> {tutor_info[2]}</p>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                    if st.button("Выйти"):
                        token = st.session_state.get("auth_token")
                        if token:
                            redis_client.delete(f"auth_token:{token}")
                        st.session_state.clear()
                        st.rerun()


                elif menu == "Заявки":
                    tutor_subject_id = tutor_info[3]
                    requests = get_requests_by_subject(tutor_subject_id)
                    if not requests:
                        st.write("Нет доступных заявок по вашему предмету")
                    else:
                        for request in requests:
                            subject_name = next(subject[1] for subject in get_subjects() if subject[0] == request[2])
                            created_at = request[5].strftime("%Y-%m-%d %H:%M")
                            st.write(f"ID заявки: {request[0]}")
                            st.write(f"Предмет: {subject_name}")
                            st.write(f"Описание: {request[3]}")
                            st.write(f"Бюджет: {request[4]}")
                            st.write(f"Дата создания: {created_at}")
                            message = st.text_area(f"Сообщение для заявки {request[0]}")
                            if st.button(f"Откликнуться на заявку {request[0]}"):
                                create_response(request[0], st.session_state['user_id'], message)
                            st.write("---")

                elif menu == "Мои отзывы":
                    tutor_id = get_tutor_id_by_user_id(st.session_state['user_id'])
                    if tutor_id is None:
                        st.error("Информация о репетиторе не найдена.")
                    else:
                        reviews = get_tutor_reviews(tutor_id)
                        total_rating = sum(review[4] for review in reviews)
                        average_rating = total_rating / len(reviews) if reviews else 0
                        st.write(f"Средний рейтинг: {average_rating:.2f}")
                        st.write(f"Количество отзывов: {len(reviews)}")
                        st.write("---")
                        for review in reviews:
                            st.write(f"ID отзыва: {review[0]}")
                            st.write(f"Клиент: {review[1]} {review[2]}")
                            st.write(f"Отзыв: {review[3]}")
                            st.write(f"Рейтинг: {review[4]}")
                            st.write(f"Дата отзыва: {review[5].strftime('%Y-%m-%d %H:%M')}")
                            st.write("---")

                elif menu == "Моё расписание":
                    tutor_id = get_tutor_id_by_user_id(st.session_state['user_id'])
                    if tutor_id is None:
                        st.error("Информация о репетиторе не найдена.")
                    else:
                        schedule = get_tutor_schedule(tutor_id)
                        if not schedule:
                            st.write("У вас пока нет расписания.")
                        else:
                            st.write("Ваше текущее расписание:")
                            for entry in schedule:
                                day_mapping = {
                                    "Monday": "Понедельник",
                                    "Tuesday": "Вторник",
                                    "Wednesday": "Среда",
                                    "Thursday": "Четверг",
                                    "Friday": "Пятница",
                                    "Saturday": "Суббота",
                                    "Sunday": "Воскресенье"
                                }
                                st.write(f"День недели: {day_mapping[entry[1]]}")
                                st.write(f"Время начала: {entry[2].strftime('%H:%M')}")
                                st.write(f"Время окончания: {entry[3].strftime('%H:%M')}")
                                st.write("---")

                        st.write("Добавить новое время:")
                        day_of_week = st.selectbox("День недели", ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"])
                        start_time = st.time_input("Время начала")
                        end_time = st.time_input("Время окончания")
                        if st.button("Добавить расписание"):
                            day_mapping = {
                                "Понедельник": "Monday",
                                "Вторник": "Tuesday",
                                "Среда": "Wednesday",
                                "Четверг": "Thursday",
                                "Пятница": "Friday",
                                "Суббота": "Saturday",
                                "Воскресенье": "Sunday"
                            }
                            add_schedule(tutor_id, day_mapping[day_of_week], start_time, end_time)
                            st.success("Расписание добавлено успешно!")
                            st.rerun()
        elif st.session_state['user_role'] == 'admin':
            st.title(f"Добро пожаловать, {user_info[0]} {user_info[1]}")

            st.sidebar.title("Меню")
            menu = st.sidebar.radio("Выберите действие", ["Мой аккаунт", "Заявки", "Клиенты", "Статистика", "Создать архивную копию", "Восстановить из архивной копии"])
            if menu == "Мой аккаунт":
                st.markdown(
                    f"""
                    <div style="background-color: #f9f9f9; padding: 20px; border-radius: 10px; box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);">
                        <h2 style="color: #333;">Мой аккаунт</h2>
                        <p><strong>Имя:</strong> {user_info[0]}</p>
                        <p><strong>Фамилия:</strong> {user_info[1]}</p>
                        <p><strong>Email:</strong> {user_info[2]}</p>
                        <p><strong>Роль:</strong> {user_info[3]}</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                new_first_name = st.text_input("Новое имя", user_info[0])
                new_last_name = st.text_input("Новая фамилия", user_info[1])
                new_email = st.text_input("Новый email", user_info[2])
                if st.button("Сохранить изменения"):
                    edit_user_profile(st.session_state['user_id'], new_first_name, new_last_name, new_email)
                    st.success("Профиль успешно обновлен!")
                    st.rerun()
                if st.button("Выйти"):
                    token = st.session_state.get("auth_token")
                    if token:
                        redis_client.delete(f"auth_token:{token}")
                    st.session_state.clear()
                    st.rerun()
                    
            elif menu == "Заявки":
                requests = get_all_requests()
                for request in requests:
                    with st.expander(f"Заявка #{request[0]} от {request[1]} {request[2]}"):
                        st.write(f"Предмет: {request[3]}")
                        st.write(f"Описание: {request[4]}")
                        st.write(f"Бюджет: {request[5]}")
                        st.write(f"Дата создания: {request[6].strftime('%Y-%m-%d %H:%M')}")
                        if st.button(f"Удалить заявку {request[0]}", key=f"delete_request_{request[0]}"):
                            delete_request(request[0])
                            st.success("Заявка удалена успешно!")
                            st.rerun()

            elif menu == "Клиенты":
                clients = get_clients()
                for client in clients:
                    with st.expander(f"{client[1]} {client[2]}"):
                        st.write(f"Email: {client[3]}")
                        if st.button(f"Удалить клиента {client[1]} {client[2]}", key=f"delete_client_{client[0]}"):
                            delete_user(client[0])
                            st.success(f"Клиент {client[1]} {client[2]} удален.")
                            st.rerun()

            elif menu == "Статистика":
                st.write("Статистика:")
                st.write(f"Общее количество репетиторов: {get_tutors_count()}")
                st.write(f"Общее количество клиентов: {get_clients_count()}")
                st.write(f"Общее количество откликов: {get_responses_count()}")
                st.write(f"Общее количество заявок: {get_requests_count()}")

            elif menu == "Создать архивную копию":
                if st.button("Создать архивную копию"):
                    create_backup()

            elif menu == "Восстановить из архивной копии":
                if st.button("Восстановить из архивной копии"):
                    restore_backup()

if __name__ == "__main__":
    main()
