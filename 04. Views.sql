USE mydb;

CREATE OR REPLACE VIEW vw_active_contracts AS
SELECT 
    c.ContractID,
    c.CustomerID,
    cu.CustomerName,
    c.SignDate,
    c.Duration,
    c.TotalValue,
    c.Status
FROM Contracts c
JOIN Customers cu ON c.CustomerID = cu.CustomerID
WHERE c.Status = 'Active';

CREATE OR REPLACE VIEW vw_unpaid_invoices AS
SELECT
    i.InvoiceID,
    i.ContractID,
    cu.CustomerID,
    cu.CustomerName,
    i.IssueDate,
    i.DueDate,
    i.TotalAmount,
    i.InvoiceStatus
FROM Invoices i
JOIN Contracts c ON i.ContractID = c.ContractID
JOIN Customers cu ON c.CustomerID = cu.CustomerID
WHERE i.InvoiceStatus IN ('Unpaid', 'Overdue');

CREATE OR REPLACE VIEW vw_customer_billing_summary AS
SELECT
    cu.CustomerID,
    cu.CustomerName,
    COALESCE(ct.TotalContracts, 0) AS TotalContracts,
    COALESCE(iv.TotalInvoiced, 0) AS TotalInvoiced,
    COALESCE(py.TotalPaid, 0) AS TotalPaid,
    COALESCE(iv.TotalInvoiced, 0) - COALESCE(py.TotalPaid, 0) AS OutstandingBalance
FROM Customers cu
LEFT JOIN (
    SELECT 
        CustomerID,
        COUNT(*) AS TotalContracts
    FROM Contracts
    GROUP BY CustomerID
) ct ON cu.CustomerID = ct.CustomerID
LEFT JOIN (
    SELECT 
        c.CustomerID,
        SUM(i.TotalAmount) AS TotalInvoiced
    FROM Contracts c
    LEFT JOIN Invoices i ON c.ContractID = i.ContractID
    GROUP BY c.CustomerID
) iv ON cu.CustomerID = iv.CustomerID
LEFT JOIN (
    SELECT 
        c.CustomerID,
        SUM(p.Amount) AS TotalPaid
    FROM Contracts c
    LEFT JOIN Payments p ON c.ContractID = p.ContractID
    GROUP BY c.CustomerID
) py ON cu.CustomerID = py.CustomerID;

USE mydb;

SELECT * FROM vw_active_contracts LIMIT 20;
SELECT * FROM vw_unpaid_invoices LIMIT 20;
SELECT * FROM vw_customer_billing_summary LIMIT 20;
