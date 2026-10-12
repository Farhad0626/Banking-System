CREATE TABLE IF NOT EXISTS customers (
    id              BIGSERIAL       PRIMARY KEY,
    first_name      VARCHAR(100)    NOT NULL,
    last_name       VARCHAR(100)    NOT NULL,
    national_id     VARCHAR(10)     NOT NULL UNIQUE,
    mobile          VARCHAR(11)     NOT NULL UNIQUE,
    email           VARCHAR(255)    NOT NULL,
    username        VARCHAR(50)     NOT NULL UNIQUE,
    password_hash   VARCHAR(255)    NOT NULL,
    is_active       BOOLEAN         NOT NULL DEFAULT TRUE,
    is_restricted   BOOLEAN         NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ     NOT NULL DEFAULT now(),
    deleted_at      TIMESTAMPTZ     NULL
);