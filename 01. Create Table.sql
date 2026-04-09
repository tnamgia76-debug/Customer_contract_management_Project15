CREATE DATABASE IF NOT EXISTS mydb;
USE mydb;

DROP TABLE IF EXISTS Payments;
DROP TABLE IF EXISTS Invoices;
DROP TABLE IF EXISTS ContractServices;
DROP TABLE IF EXISTS Contracts;
DROP TABLE IF EXISTS Services;
DROP TABLE IF EXISTS Customers;

CREATE TABLE Customers (
    CustomerID INT NOT NULL AUTO_INCREMENT,
    CustomerName VARCHAR(100) NOT NULL,
    Address VARCHAR(255),
    PhoneNumber VARCHAR(20),
    Email VARCHAR(100),
    PRIMARY KEY (CustomerID)
) ENGINE=InnoDB;

CREATE TABLE Services (
    ServiceID INT NOT NULL AUTO_INCREMENT,
    ServiceName VARCHAR(100) NOT NULL,
    Description TEXT,
    UnitPrice DECIMAL(12,2) NOT NULL,
    PRIMARY KEY (ServiceID)
) ENGINE=InnoDB;

CREATE TABLE Contracts (
    ContractID INT NOT NULL AUTO_INCREMENT,
    CustomerID INT NOT NULL,
    SignDate DATE NOT NULL,
    Duration INT NOT NULL,
    TotalValue DECIMAL(12,2) NOT NULL,
    Status VARCHAR(20) NOT NULL,
    PRIMARY KEY (ContractID),
    CONSTRAINT fk_contracts_customers
        FOREIGN KEY (CustomerID)
        REFERENCES Customers(CustomerID)
        ON DELETE NO ACTION
        ON UPDATE NO ACTION
) ENGINE=InnoDB;

CREATE TABLE ContractServices (
    ContractServiceID INT NOT NULL AUTO_INCREMENT,
    ContractID INT NOT NULL,
    ServiceID INT NOT NULL,
    Quantity INT NOT NULL,
    UnitPrice DECIMAL(12,2) NOT NULL,
    PRIMARY KEY (ContractServiceID),
    CONSTRAINT fk_contractservices_contracts
        FOREIGN KEY (ContractID)
        REFERENCES Contracts(ContractID)
        ON DELETE NO ACTION
        ON UPDATE NO ACTION,
    CONSTRAINT fk_contractservices_services
        FOREIGN KEY (ServiceID)
        REFERENCES Services(ServiceID)
        ON DELETE NO ACTION
        ON UPDATE NO ACTION
) ENGINE=InnoDB;

CREATE TABLE Invoices (
    InvoiceID INT NOT NULL AUTO_INCREMENT,
    ContractID INT NOT NULL,
    IssueDate DATE NOT NULL,
    DueDate DATE,
    TotalAmount DECIMAL(12,2) NOT NULL,
    InvoiceStatus VARCHAR(20) NOT NULL,
    PRIMARY KEY (InvoiceID),
    CONSTRAINT fk_invoices_contracts
        FOREIGN KEY (ContractID)
        REFERENCES Contracts(ContractID)
        ON DELETE NO ACTION
        ON UPDATE NO ACTION
) ENGINE=InnoDB;

CREATE TABLE Payments (
    PaymentID INT NOT NULL AUTO_INCREMENT,
    ContractID INT NOT NULL,
    PaymentDate DATE NOT NULL,
    Amount DECIMAL(12,2) NOT NULL,
    PaymentMethod VARCHAR(50) NOT NULL,
    PRIMARY KEY (PaymentID),
    CONSTRAINT fk_payments_contracts
        FOREIGN KEY (ContractID)
        REFERENCES Contracts(ContractID)
        ON DELETE NO ACTION
        ON UPDATE NO ACTION
) ENGINE=InnoDB;

SHOW TABLES;
