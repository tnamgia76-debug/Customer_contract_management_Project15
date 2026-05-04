USE mydb;

-- 1. CREATE ROLES

CREATE ROLE IF NOT EXISTS sales_role;
CREATE ROLE IF NOT EXISTS finance_role;
CREATE ROLE IF NOT EXISTS admin_role;

-- RESET OLD GRANTS ON ROLES TO AVOID PERMISSION CONFLICT WHEN RERUNNING SCRIPT
REVOKE ALL PRIVILEGES, GRANT OPTION FROM sales_role;
REVOKE ALL PRIVILEGES, GRANT OPTION FROM finance_role;
REVOKE ALL PRIVILEGES, GRANT OPTION FROM admin_role;

-- 2. CREATE DEMO USERS

CREATE USER IF NOT EXISTS 'sales_user'@'localhost' IDENTIFIED BY 'Sales@123';
CREATE USER IF NOT EXISTS 'finance_user'@'localhost' IDENTIFIED BY 'Finance@123';
CREATE USER IF NOT EXISTS 'admin_user'@'localhost' IDENTIFIED BY 'Admin@123';

-- FORCE DEMO PASSWORDS TO BE CONSISTENT WHEN THE SCRIPT IS RERUN
ALTER USER 'sales_user'@'localhost' IDENTIFIED BY 'Sales@123';
ALTER USER 'finance_user'@'localhost' IDENTIFIED BY 'Finance@123';
ALTER USER 'admin_user'@'localhost' IDENTIFIED BY 'Admin@123';

-- REMOVE ANY OLD DIRECT PRIVILEGES FROM DEMO USERS.
-- THIS MAKES THE DEMO DEPEND ON ROLES INSTEAD OF HIDDEN DIRECT GRANTS.
REVOKE ALL PRIVILEGES, GRANT OPTION FROM 'sales_user'@'localhost';
REVOKE ALL PRIVILEGES, GRANT OPTION FROM 'finance_user'@'localhost';
REVOKE ALL PRIVILEGES, GRANT OPTION FROM 'admin_user'@'localhost';

GRANT sales_role TO 'sales_user'@'localhost';
GRANT finance_role TO 'finance_user'@'localhost';
GRANT admin_role TO 'admin_user'@'localhost';

SET DEFAULT ROLE sales_role TO 'sales_user'@'localhost';
SET DEFAULT ROLE finance_role TO 'finance_user'@'localhost';
SET DEFAULT ROLE admin_role TO 'admin_user'@'localhost';

-- 3. ADD ENCRYPTED COLUMNS SAFELY

DROP PROCEDURE IF EXISTS sp_add_column_if_not_exists;

DELIMITER $$

CREATE PROCEDURE sp_add_column_if_not_exists(
    IN p_table_name VARCHAR(64),
    IN p_column_name VARCHAR(64),
    IN p_column_definition TEXT
)
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = p_table_name
          AND COLUMN_NAME = p_column_name
    ) THEN
        SET @sql_text = CONCAT(
            'ALTER TABLE ',
            p_table_name,
            ' ADD COLUMN ',
            p_column_name,
            ' ',
            p_column_definition
        );

        PREPARE stmt FROM @sql_text;
        EXECUTE stmt;
        DEALLOCATE PREPARE stmt;
    END IF;
END $$

DELIMITER ;

CALL sp_add_column_if_not_exists(
    'Contracts',
    'TotalValueEncrypted',
    'VARBINARY(255) NULL'
);

CALL sp_add_column_if_not_exists(
    'Payments',
    'AmountEncrypted',
    'VARBINARY(255) NULL'
);

DROP PROCEDURE IF EXISTS sp_add_column_if_not_exists;

-- 4. ENCRYPT EXISTING FINANCIAL DATA

SET @project15_encryption_key = 'project15_key';

UPDATE Contracts
SET TotalValueEncrypted = AES_ENCRYPT(CAST(TotalValue AS CHAR), @project15_encryption_key);

UPDATE Payments
SET AmountEncrypted = AES_ENCRYPT(CAST(Amount AS CHAR), @project15_encryption_key);

-- 5. CREATE AUTOMATIC ENCRYPTION TRIGGERS

DROP TRIGGER IF EXISTS trg_contracts_encrypt_before_insert;
DROP TRIGGER IF EXISTS trg_contracts_encrypt_before_update;
DROP TRIGGER IF EXISTS trg_payments_encrypt_before_insert;
DROP TRIGGER IF EXISTS trg_payments_encrypt_before_update;

DELIMITER $$

CREATE TRIGGER trg_contracts_encrypt_before_insert
BEFORE INSERT ON Contracts
FOR EACH ROW
BEGIN
    IF NEW.TotalValue IS NULL THEN
        SET NEW.TotalValueEncrypted = NULL;
    ELSE
        SET NEW.TotalValueEncrypted = AES_ENCRYPT(CAST(NEW.TotalValue AS CHAR), 'project15_key');
    END IF;
END $$

CREATE TRIGGER trg_contracts_encrypt_before_update
BEFORE UPDATE ON Contracts
FOR EACH ROW
BEGIN
    IF NOT (NEW.TotalValue <=> OLD.TotalValue) THEN
        IF NEW.TotalValue IS NULL THEN
            SET NEW.TotalValueEncrypted = NULL;
        ELSE
            SET NEW.TotalValueEncrypted = AES_ENCRYPT(CAST(NEW.TotalValue AS CHAR), 'project15_key');
        END IF;
    END IF;
END $$

CREATE TRIGGER trg_payments_encrypt_before_insert
BEFORE INSERT ON Payments
FOR EACH ROW
BEGIN
    IF NEW.Amount IS NULL THEN
        SET NEW.AmountEncrypted = NULL;
    ELSE
        SET NEW.AmountEncrypted = AES_ENCRYPT(CAST(NEW.Amount AS CHAR), 'project15_key');
    END IF;
END $$

CREATE TRIGGER trg_payments_encrypt_before_update
BEFORE UPDATE ON Payments
FOR EACH ROW
BEGIN
    IF NOT (NEW.Amount <=> OLD.Amount) THEN
        IF NEW.Amount IS NULL THEN
            SET NEW.AmountEncrypted = NULL;
        ELSE
            SET NEW.AmountEncrypted = AES_ENCRYPT(CAST(NEW.Amount AS CHAR), 'project15_key');
        END IF;
    END IF;
END $$

DELIMITER ;

-- 6. SECURITY VIEWS FOR DEMO

CREATE OR REPLACE SQL SECURITY DEFINER VIEW vw_active_contracts_masked AS
SELECT
    c.ContractID,
    c.CustomerID,
    cu.CustomerName,
    c.SignDate,
    c.Duration,
    'encrypted / restricted' AS TotalValueDisplay,
    c.Status
FROM Contracts c
JOIN Customers cu ON c.CustomerID = cu.CustomerID
WHERE c.Status = 'Active';

CREATE OR REPLACE SQL SECURITY DEFINER VIEW vw_contract_encryption_check AS
SELECT
    ContractID,
    TotalValue,
    HEX(TotalValueEncrypted) AS TotalValueCipherText,
    CAST(AES_DECRYPT(TotalValueEncrypted, 'project15_key') AS CHAR(50)) AS DecryptedTotalValue
FROM Contracts;

CREATE OR REPLACE SQL SECURITY DEFINER VIEW vw_payment_encryption_check AS
SELECT
    PaymentID,
    ContractID,
    Amount,
    HEX(AmountEncrypted) AS AmountCipherText,
    CAST(AES_DECRYPT(AmountEncrypted, 'project15_key') AS CHAR(50)) AS DecryptedAmount
FROM Payments;

-- 7. ROLE PERMISSIONS

-- SALES ROLE:
-- SALES STAFF CAN MANAGE CUSTOMER/CONTACT DATA, VIEW SERVICES, CREATE CONTRACTS,
-- AND UPDATE CONTRACT STATUS. SALES STAFF SHOULD NOT DIRECTLY ACCESS PAYMENT DATA.

GRANT SELECT, INSERT, UPDATE ON mydb.Customers TO sales_role;
GRANT SELECT ON mydb.Services TO sales_role;
GRANT SELECT, INSERT, UPDATE ON mydb.Contracts TO sales_role;
GRANT SELECT, INSERT, UPDATE ON mydb.ContractServices TO sales_role;
GRANT SELECT ON mydb.vw_active_contracts_masked TO sales_role;
GRANT SELECT ON mydb.vw_active_contracts TO sales_role;
GRANT SELECT ON mydb.vw_customer_billing_summary TO sales_role;

-- FINANCE ROLE:
-- FINANCE STAFF CAN WORK WITH INVOICES, PAYMENTS, BILLING REPORTS, AND FINANCIAL FUNCTIONS.

GRANT SELECT ON mydb.Customers TO finance_role;
GRANT SELECT ON mydb.Contracts TO finance_role;
GRANT SELECT ON mydb.Services TO finance_role;
GRANT SELECT ON mydb.ContractServices TO finance_role;
GRANT SELECT, INSERT, UPDATE ON mydb.Invoices TO finance_role;
GRANT SELECT, INSERT, UPDATE ON mydb.Payments TO finance_role;

GRANT SELECT ON mydb.vw_active_contracts TO finance_role;
GRANT SELECT ON mydb.vw_unpaid_invoices TO finance_role;
GRANT SELECT ON mydb.vw_customer_billing_summary TO finance_role;
GRANT SELECT ON mydb.vw_contract_encryption_check TO finance_role;
GRANT SELECT ON mydb.vw_payment_encryption_check TO finance_role;

GRANT EXECUTE ON PROCEDURE mydb.sp_generate_invoice TO finance_role;
GRANT EXECUTE ON PROCEDURE mydb.sp_record_payment TO finance_role;
GRANT EXECUTE ON FUNCTION mydb.fn_remaining_contract_value TO finance_role;
GRANT EXECUTE ON FUNCTION mydb.fn_monthly_revenue TO finance_role;

-- ADMIN ROLE:
-- ADMIN HAS FULL CONTROL FOR MAINTENANCE, BACKUP/RECOVERY, AND FULL INSPECTION.

GRANT ALL PRIVILEGES ON mydb.* TO admin_role;

FLUSH PRIVILEGES;

-- 8. VERIFICATION QUERIES FOR SCREENSHOTS

SHOW GRANTS FOR 'sales_user'@'localhost';
SHOW GRANTS FOR 'finance_user'@'localhost';
SHOW GRANTS FOR 'admin_user'@'localhost';

SELECT
    ContractID,
    TotalValue,
    TotalValueCipherText,
    DecryptedTotalValue
FROM vw_contract_encryption_check
LIMIT 5;

SELECT
    PaymentID,
    Amount,
    AmountCipherText,
    DecryptedAmount
FROM vw_payment_encryption_check
LIMIT 5;

SHOW INDEXES FROM Customers;
SHOW INDEXES FROM Contracts;
SHOW INDEXES FROM Invoices;
SHOW INDEXES FROM Payments;

EXPLAIN SELECT *
FROM Contracts
WHERE CustomerID = 10
  AND Status = 'Active';

EXPLAIN SELECT *
FROM Payments
WHERE ContractID = 10
ORDER BY PaymentDate DESC;

EXPLAIN SELECT *
FROM Invoices
WHERE ContractID = 10
  AND InvoiceStatus = 'Unpaid';

-- 9. BACKUP AND RECOVERY PLAN
-- BACKUP COMMAND, RUN IN WINDOWS TERMINAL / CMD / POWERSHELL:
-- mysqldump -u admin_user -p --single-transaction --routines --triggers --events mydb > backups\mydb_project15_backup.sql

-- RECOVERY COMMAND, RUN IN WINDOWS TERMINAL / CMD / POWERSHELL:
-- mysql -u admin_user -p mydb < backups\mydb_project15_backup.sql

-- RESTORE TEST PLAN:
-- 1. CREATE A SEPARATE DATABASE NAMED mydb_restore_test.
-- 2. IMPORT THE BACKUP FILE INTO mydb_restore_test.
-- 3. RUN ROW-COUNT VERIFICATION QUERIES TO CONFIRM THAT TABLES AND DATA WERE RESTORED.
-- 4. CHECK THAT VIEWS, PROCEDURES, FUNCTIONS, AND TRIGGERS ARE STILL AVAILABLE AFTER RESTORE.

