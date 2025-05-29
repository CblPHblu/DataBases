FROM postgres:15

# Установка зависимостей, сборка и установка pg_bigm
RUN apt-get update && \
    apt-get install -y wget zip make gcc postgresql-server-dev-15 && \
    wget https://github.com/pgbigm/pg_bigm/archive/refs/heads/master.zip -O pg_bigm.zip && \
    unzip pg_bigm.zip && \
    cd pg_bigm-master && \
    make USE_PGXS=1 && \
    make USE_PGXS=1 install && \
    cd .. && \
    rm -rf pg_bigm-master pg_bigm.zip && \
    apt-get purge -y wget zip make gcc postgresql-server-dev-15 && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/*

# Установка стандартных расширений PostgreSQL
RUN apt-get update && \
    apt-get install -y postgresql-contrib && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Копируем скрипты инициализации
COPY ./initDatabase/ /docker-entrypoint-initdb.d/
