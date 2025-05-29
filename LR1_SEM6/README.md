# 📦 Базы данных — Лабораторная работа №1 (6 семестр)

## 🚀 Как запустить


### ✅ Запуск локально 

1. Убедись, что PostgreSQL запущен и настроен:
   - Пользователь: `postgres`
   - База данных: `labdb`
   - Порт: `5433` (если нестандартный)

2. Загрузить структуру и данные:

```bash
psql -h localhost -U postgres -d labdb -p 5433 -f InitDatabse/ddl.sql
psql -h localhost -U postgres -d labdb -p 5433 -f InitDatabse/dml.sql
```

3. Запустить задания:

```bash
psql -h localhost -U postgres -d labdb -p 5433 -f tasks/1_1.sql
psql -h localhost -U postgres -d labdb -p 5433 -f tasks/1_2.sql
psql -h localhost -U postgres -d labdb -p 5433 -f tasks/1_3.sql
```


### Филатов А.К. М8О-306Б-22