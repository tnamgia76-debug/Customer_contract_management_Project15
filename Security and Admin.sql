USE mydb;

-- 1. Roles
CREATE ROLE IF NOT EXISTS sales_role;
CREATE ROLE IF NOT EXISTS finance_role;
CREATE ROLE IF NOT EXISTS admin_role;

-- 2. Grants
GRANT SELECT, INSERT, UPDATE ON mydb.Customers TO sales_role;
GRANT SELECT, INSERT, UPDATE ON mydb.Contracts TO sales_role;
GRANT SELECT ON mydb.Services TO sales_role;

GRANT SELECT ON mydb.Customers TO finance_role;
GRANT SELECT ON mydb.Contracts TO finance_role;
GRANT SELECT ON mydb.ContractServices TO finance_role;
GRANT SELECT, INSERT, UPDATE ON mydb.Invoices TO finance_role;
GRANT SELECT, INSERT, UPDATE ON mydb.Payments TO finance_role;

GRANT ALL PRIVILEGES ON mydb.* TO admin_role;

-- 3. Demo users
CREATE USER IF NOT EXISTS 'sales_user'@'localhost' IDENTIFIED BY 'Sales@123';
CREATE USER IF NOT EXISTS 'finance_user'@'localhost' IDENTIFIED BY 'Finance@123';
CREATE USER IF NOT EXISTS 'admin_user'@'localhost' IDENTIFIED BY 'Admin@123';

GRANT sales_role TO 'sales_user'@'localhost';
GRANT finance_role TO 'finance_user'@'localhost';
GRANT admin_role TO 'admin_user'@'localhost';

SET DEFAULT ROLE sales_role TO 'sales_user'@'localhost';
SET DEFAULT ROLE finance_role TO 'finance_user'@'localhost';
SET DEFAULT ROLE admin_role TO 'admin_user'@'localhost';

-- 4. Optional encryption demo
ALTER TABLE Contracts
ADD COLUMN TotalValueEncrypted VARBINARY(255) NULL;

ALTER TABLE Payments
ADD COLUMN AmountEncrypted VARBINARY(255) NULL;

UPDATE Contracts
SET TotalValueEncrypted = AES_ENCRYPT(CAST(TotalValue AS CHAR), 'project15_key');

UPDATE Payments
SET AmountEncrypted = AES_ENCRYPT(CAST(Amount AS CHAR), 'project15_key');

-- 5. Verify encryption
SELECT
    ContractID,
    CAST(AES_DECRYPT(TotalValueEncrypted, 'project15_key') AS CHAR(50)) AS DecryptedTotalValue
FROM Contracts
LIMIT 5;

SELECT
    PaymentID,
    CAST(AES_DECRYPT(AmountEncrypted, 'project15_key') AS CHAR(50)) AS DecryptedAmount
FROM Payments
LIMIT 5;

-- 6. Query optimization checks
EXPLAIN SELECT * FROM Contracts WHERE CustomerID = 10 AND Status = 'Active';
EXPLAIN SELECT * FROM Payments WHERE ContractID = 10 ORDER BY PaymentDate DESC;