USE mydb;
DROP INDEX idx_customers_name ON Customers;
DROP INDEX idx_contracts_customer_status ON Contracts;
DROP INDEX idx_invoices_contract_status ON Invoices;
DROP INDEX idx_payments_contract_date ON Payments;

CREATE INDEX idx_customers_name ON Customers (CustomerName);
CREATE INDEX idx_contracts_customer_status ON Contracts (CustomerID, Status);
CREATE INDEX idx_invoices_contract_status ON Invoices (ContractID, InvoiceStatus);
CREATE INDEX idx_payments_contract_date ON Payments (ContractID, PaymentDate);
