# Customer and Contract Management System

This is my work on the Final Project for the Introduction to Databases Course. This project is built with MySQL and Python to manage customers, contracts, services, invoices, payments, and reporting.

## Overview
This system was designed to support the full workflow of customer and contract management:
- Store and manage customer information
- Create and track service contracts
- Manage service mappings for each contract
- Generate invoices and record payments
- Track active contracts and unpaid/overdue invoices
- Produce billing, revenue, and customer history reports
- Demonstrate database security, encryption, backup/recovery, and query optimization

The project combines **database design**, **advanced SQL objects**, and a **Python CLI application**.

## Main Tables
- **Customers**: customer information
- **Contracts**: contract records linked to customers
- **Services**: service catalog
- **ContractServices**: mapping between contracts and services
- **Invoices**: invoice records for contracts
- **Payments**: payment records for contracts

## Advanced Database Objects
- Indexes for improving lookup and reporting performance
- Views for active contracts, unpaid invoices, billing summaries, and security verification
- Stored Procedures for invoice generation and payment recording
- User-Defined Functions for remaining contract value and monthly revenue calculations
- Triggers for automatic invoice/contract status updates and encrypted financial copies
- Security and Administration scripts for roles, permissions, encryption, backup/recovery notes, and query analysis

## Security and Administration
- Role-based access control
- Demo users: sales_user, finance_user, and admin_user
- Permissions for sales, finance, and admin responsibilities
- Encrypted copies of sensitive financial fields: Contracts.TotalValueEncrypted and Payments.AmountEncrypted
- Encryption verification views
- Backup and recovery commands
- EXPLAIN queries for optimization evidence
  
The Python CLI connects using these demonstration users instead of using the MySQL root account.

## Python Application 
The Python CLI application is implemented in:
customer_contract_manager.py
At startup, the user chooses a login profile:
1. Sales user
2. Finance user
3. Admin user

### Sales User Features
-	Add customer
-	Update customer
-	Search customer by name
-	View service catalog
-	Create contract
-	Update contract status
-	View active contracts
-	View contract services
-	View customer contract history
-	Test restricted access to payment data

### Finance User Features
- View active contracts
- View contract services
- View unpaid/overdue invoices
- Generate invoices
- Record payments
- View customer billing summary
- View monthly revenue
- View remaining contract value
- Generate CSV reports
- View contract/payment encryption checks

### Admin User Features
- Customer, service, and contract management
- Invoice and payment management
- Reporting and CSV export
- Sample data count verification
- Encryption verification
- Query optimization checks
- Backup and recovery command display
- User/role/grant inspection

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
Login Profiles:
Use the following demo accounts created by 08. Security and Admin.sql:
1. sales_user   -> Sales@123
2. finance_user -> Finance@123
3. admin_user   -> Admin@123
   
These accounts are for local demonstration only.

## Backup and Recovery
The project demonstrates backup and recovery using standard MySQL tools.
Create a backup folder:
```bash
mkdir backups
```
Backup command:
```bash
mysqldump -u admin_user -p --single-transaction --routines --triggers --events mydb > backups\mydb_project15_backup.sql
```
Recovery command:
```bash
mysql -u admin_user -p mydb < backups\mydb_project15_backup.sql
```
An optional restore test can be performed by restoring the backup file into a separate database such as mydb_restore_test.

## Outputs
The Python application can generate CSV reports in the reports folder, including:
-	Customer billing summary report
-	Monthly revenue report
-	Unpaid/overdue invoices report
The CLI also displays operational results directly in the terminal, such as active contracts, unpaid invoices, generated invoices, recorded payments, and encryption checks.

    
## Conclusion
This project demonstrates a complete database-driven Customer and Contract Management System. It integrates relational database design, advanced SQL programming, role-based security, financial data encryption, backup/recovery planning, query optimization, and a Python CLI application for operational use and reporting.
