FROM postgres:17-bookworm

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl libc-bin dnsutils iproute2 \
    && rm -rf /var/lib/apt/lists/*

COPY init.sql /docker-entrypoint-initdb.d/01-inventory.sql
