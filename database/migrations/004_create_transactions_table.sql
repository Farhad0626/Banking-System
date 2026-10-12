CREATE TABLE IF NOT EXISTS transactions (
    id                      BIGSERIAL      PRIMARY KEY,
    transaction_type        VARCHAR(10)    NOT NULL CHECK (transaction_type IN ('DEPOSIT', 'WITHDRAW', 'TRANSFER')),
    amount                  NUMERIC(15,2)  NOT NULL CHECK (amount > 0),
    source_account_id       BIGINT         NULL REFERENCES accounts(id),
    destination_account_id  BIGINT         NULL REFERENCES accounts(id),
    status                  VARCHAR(10)    NOT NULL DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'COMPLETED', 'FAILED')),
    created_at              TIMESTAMPTZ    NOT NULL DEFAULT now(),

    CONSTRAINT chk_transfer_accounts_differ
        CHECK (
            transaction_type <> 'TRANSFER'
            OR source_account_id IS DISTINCT FROM destination_account_id
        ),
    CONSTRAINT chk_deposit_has_destination
        CHECK (transaction_type <> 'DEPOSIT' OR destination_account_id IS NOT NULL),
    CONSTRAINT chk_withdraw_has_source
        CHECK (transaction_type <> 'WITHDRAW' OR source_account_id IS NOT NULL)
);

CREATE INDEX IF NOT EXISTS idx_transactions_source_created
    ON transactions(source_account_id, created_at);

CREATE INDEX IF NOT EXISTS idx_transactions_destination_created
    ON transactions(destination_account_id, created_at);

CREATE INDEX IF NOT EXISTS idx_transactions_created_at
    ON transactions(created_at);