ALTER TABLE transactions
    DROP CONSTRAINT IF EXISTS transactions_transaction_type_check;

ALTER TABLE transactions
    ADD CONSTRAINT transactions_transaction_type_check
    CHECK (transaction_type IN ('DEPOSIT', 'WITHDRAWAL', 'TRANSFER'));
