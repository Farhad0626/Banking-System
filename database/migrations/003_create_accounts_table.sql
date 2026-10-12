CREATE TABLE IF NOT EXISTS accounts (
    id                  BIGSERIAL       PRIMARY KEY,
    account_number      VARCHAR(16)     NOT NULL UNIQUE,
    customer_id         BIGINT          NOT NULL REFERENCES customers(id),
    account_type        VARCHAR(20)     NOT NULL CHECK (account_type IN ('SAVINGS', 'CHECKING', 'TERM_DEPOSIT')),
    balance             NUMERIC(15,2)   NOT NULL DEFAULT 0,
    status              VARCHAR(10)     NOT NULL DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'INACTIVE')),
    interest_rate       NUMERIC(5,4)    NULL,
    overdraft_limit     NUMERIC(15,2)   NULL,
    term_start_date     DATE            NULL,
    term_end_date       DATE            NULL,
    created_at          TIMESTAMPTZ     NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ     NOT NULL DEFAULT now(),
    deleted_at          TIMESTAMPTZ     NULL
);

CREATE INDEX IF NOT EXISTS idx_accounts_customer_id ON accounts(customer_id);

DROP TRIGGER IF EXISTS trg_accounts_updated_at ON accounts;

CREATE TRIGGER trg_accounts_updated_at
    BEFORE UPDATE ON accounts
    FOR EACH ROW
    EXECUTE FUNCTION set_updated_at();