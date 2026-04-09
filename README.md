# Customer and Contract Management System

This is my work on the Final Project for the Introduction to Databases Course. This project is built with MySQL and Python to manage customers, contracts, services, invoices, payments, and reporting.

## Overview
This system was designed to support the full workflow of customer and contract management:
- Store customer and contract information
- Manage service mappings for each contract
- Generate invoices and record payments
- Track active contracts and overdue invoices
- Produce billing and revenue reports

The project combines **database design**, **advanced SQL objects**, and a **Python CLI application**.

## Main Tables
- **Customers**: customer information
- **Contracts**: contract records linked to customers
- **Services**: service catalog
- **ContractServices**: mapping between contracts and services
- **Invoices**: invoice records for contracts
- **Payments**: payment records for contracts

## Advanced Database Objects
The project includes:
- **Indexes** for query optimization
- **Views** for active contracts, unpaid invoices, and billing summary
- **Stored Procedures** for invoice generation and payment recording
- **Functions** for remaining contract value and monthly revenue
- **Triggers** for automatic invoice/contract status updates
- **Security/Admin scripts** for roles, permissions, encryption, backup, and query analysis

## Python Application 
The Python CLI connects to MySQL and provides these features:
- Add customer
- Search customer by name
- View active contracts
- View unpaid / overdue invoices
- Generate invoice
- Record payment
- View customer billing summary
- View monthly revenue
- View remaining contract value
- Generate CSV reports

## Workflow
Typical workflow:
1. View active contracts
2. Check unpaid or overdue invoices
3. Generate an invoice for a contract
4. Record payment
5. Review billing summary
6. Check monthly revenue
7. Export reports to CSV

## Technologies Used
- MySQL
- MySQL Workbench
- Python
- mysql-connector-python

## Project Files
- `01. Create Table.sql`
- `02. Sample Data.sql`
- `03. Indexes.sql`
- `04. Views.sql`
- `05. Procedures.sql`
- `06. Functions.sql`
- `07. Triggers.sql`
- `08. Security and Admin.sql`
- `customer_contract_manager.py`

## How to Run

### 1. Execute the SQL scripts in the following order
- `01. Create Table.sql`
- `02. Sample Data.sql`
- `03. Indexes.sql`
- `04. Views.sql`
- `05. Procedures.sql`
- `06. Functions.sql`
- `07. Triggers.sql`
- `08. Security and Admin.sql`
  
### 2. Run the Python app 
Install dependency:
```bash
pip install mysql-connector-python
```
Run:
```bash
python customer_contract_manager.py
```
## Outputs and Features
The system supports:
- Customer and contract management
- Invoice generation and payment recording
- Active contract and overdue invoice tracking
- Billing summary and monthly revenue analysis
- CSV report generation, including:
  - customer billing summary
  - monthly revenue report
  - unpaid / overdue invoices report
    
## Conclusion
This project demonstrates a complete MySQL-based management system integrated with Python for real business operations, reporting, and database administration.
