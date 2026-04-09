USE mydb;

CREATE INDEX idx_customers_name
ON Customers (CustomerName);

CREATE INDEX idx_contracts_customer_status
ON Contracts (CustomerID, Status);

CREATE INDEX idx_invoices_contract_status
ON Invoices (ContractID, InvoiceStatus);

CREATE INDEX idx_payments_contract_date
ON Payments (ContractID, PaymentDate);