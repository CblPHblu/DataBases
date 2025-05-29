import csv
import random
from faker import Faker
from datetime import datetime, timedelta
from pathlib import Path

fake = Faker()
OUTPUT_DIR = Path("data")
OUTPUT_DIR.mkdir(exist_ok=True)

NUM_CLIENTS = 2_000_000
NUM_TUTORS = 1_000_000
NUM_REVIEWS = 1_000_000
NUM_LESSONS = 1_000_000

SUBJECTS = [
    "Mathematics", "Physics", "Chemistry", "Biology",
    "English", "History", "Geography", "Computer Science",
    "French", "German"
]


def save_csv(filename, header, rows):
    with open(OUTPUT_DIR / filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)


def generate_subjects():
    rows = [[i + 1, name] for i, name in enumerate(SUBJECTS)]
    save_csv("subjects.csv", ["id", "name"], rows)
    return rows


def generate_clients(n):
    emails = set()
    rows = []
    for i in range(1, n + 1):
        email = fake.unique.email()
        phone = fake.phone_number()
        name = fake.name()
        rows.append([i, name, email, phone])
    save_csv("clients.csv", ["id", "name", "email", "phone_number"], rows)
    return rows


def generate_tutors(n, subjects):
    rows = []
    for i in range(1, n + 1):
        name = fake.name()
        email = fake.unique.email()
        phone = fake.phone_number()
        rating = round(random.uniform(1.0, 5.0), 2)
        subject_id = random.choice(subjects)[0]
        rows.append([i, name, email, phone, rating, subject_id])
    save_csv("tutors.csv", ["id", "name", "email", "phone_number", "rating", "subject_id"], rows)
    return rows


def generate_reviews(n, clients, tutors):
    rows = []
    for i in range(1, n + 1):
        tutor_id = random.choice(tutors)[0]
        client_id = random.choice(clients)[0]
        rating = random.randint(1, 5)
        text = fake.sentence(nb_words=10)
        rows.append([i, tutor_id, client_id, text, rating])
    save_csv("reviews.csv", ["id", "tutor_id", "client_id", "text", "rating"], rows)
    return rows


def generate_lessons(n, clients, tutors):
    rows = []
    for i in range(1, n + 1):
        tutor_id = random.choice(tutors)[0]
        client_id = random.choice(clients)[0]
        date = fake.date_time_between(start_date="-2y", end_date="now").strftime('%Y-%m-%d %H:%M:%S')
        duration = random.choice([30, 45, 60, 90])
        rows.append([i, tutor_id, client_id, date, duration])
    save_csv("lessons.csv", ["id", "tutor_id", "client_id", "date", "duration_minutes"], rows)
    return rows


if __name__ == "__main__":
    print("\n--- Генерация данных для сервиса репетиторов ---\n")

    print("1. Генерация предметов...")
    subjects = generate_subjects()

    print("2. Генерация клиентов...")
    clients = generate_clients(NUM_CLIENTS)

    print("3. Генерация репетиторов...")
    tutors = generate_tutors(NUM_TUTORS, subjects)

    print("4. Генерация отзывов...")
    generate_reviews(NUM_REVIEWS, clients, tutors)

    print("5. Генерация уроков...")
    generate_lessons(NUM_LESSONS, clients, tutors)

    print("\n✅ Все файлы успешно сгенерированы в папке 'data'.")
