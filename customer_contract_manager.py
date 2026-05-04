import csv
import os
from datetime import datetime
from decimal import Decimal, InvalidOperation
from getpass import getpass

import mysql.connector
from mysql.connector import Error


# =========================================================
# DATABASE CONFIGURATION
# =========================================================

DB_BASE_CONFIG = {
    "host": "localhost",
    "database": "mydb",
}

USER_PROFILES = {
    "1": {
        "profile": "sales",
        "user": "sales_user",
        "description": "Sales user - manage customers, services, and contracts"
    },
    "2": {
        "profile": "finance",
        "user": "finance_user",
        "description": "Finance user - manage invoices, payments, and reports"
    },
    "3": {
        "profile": "admin",
        "user": "admin_user",
        "description": "Admin user - full database administration"
    }
}

CURRENT_SESSION = {
    "profile": None,
    "user": None,
    "password": None
}


# =========================================================
# CONNECTION AND BASIC UTILITIES
# =========================================================

def login():
    print("\nDatabase login profile")
    print("=" * 60)
    for key, value in USER_PROFILES.items():
        print(f"{key}. {value['description']}")
    print("=" * 60)

    choice = input("Choose login profile: ").strip()

    if choice not in USER_PROFILES:
        print("\nInvalid login profile.\n")
        return False

    selected = USER_PROFILES[choice]

    CURRENT_SESSION["profile"] = selected["profile"]
    CURRENT_SESSION["user"] = selected["user"]
    CURRENT_SESSION["password"] = getpass(f"Password for {selected['user']}: ")

    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT USER(), CURRENT_USER(), CURRENT_ROLE()")
        login_info = cur.fetchone()
        cur.close()
        conn.close()

        print("\nLogin successful.")
        print(f"Login user       : {login_info[0]}")
        print(f"Authenticated as : {login_info[1]}")
        print(f"Current role     : {login_info[2]}\n")
        return True

    except Error as e:
        print(f"\nLogin failed: {e}\n")
        CURRENT_SESSION["profile"] = None
        CURRENT_SESSION["user"] = None
        CURRENT_SESSION["password"] = None
        return False


def get_connection():
    if not CURRENT_SESSION["user"]:
        raise RuntimeError("No database user is logged in.")

    config = DB_BASE_CONFIG.copy()
    config["user"] = CURRENT_SESSION["user"]
    config["password"] = CURRENT_SESSION["password"]

    return mysql.connector.connect(**config)


def print_table(headers, rows):
    if not rows:
        print("\nNo data found.\n")
        return

    widths = [len(str(h)) for h in headers]

    for row in rows:
        for i, value in enumerate(row):
            value_text = "" if value is None else str(value)
            widths[i] = max(widths[i], len(value_text))

    line = "+-" + "-+-".join("-" * w for w in widths) + "-+"

    print(line)
    print("| " + " | ".join(str(h).ljust(widths[i]) for i, h in enumerate(headers)) + " |")
    print(line)

    for row in rows:
        print("| " + " | ".join(
            ("" if value is None else str(value)).ljust(widths[i])
            for i, value in enumerate(row)
        ) + " |")

    print(line)


def fetch_rows(query, params=None):
    conn = None
    cur = None

    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(query, params or ())
        rows = cur.fetchall()
        headers = [desc[0] for desc in cur.description]
        return headers, rows

    finally:
        if cur:
            cur.close()
        if conn and conn.is_connected():
            conn.close()


def run_select(query, params=None):
    headers, rows = fetch_rows(query, params)
    print()
    print_table(headers, rows)


def run_call(proc_name, args):
    conn = None
    cur = None

    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.callproc(proc_name, args)
        conn.commit()

    finally:
        if cur:
            cur.close()
        if conn and conn.is_connected():
            conn.close()


def ask_int(prompt, allow_blank=False):
    while True:
        value = input(prompt).strip()

        if allow_blank and value == "":
            return None

        try:
            return int(value)
        except ValueError:
            print("Invalid integer. Please try again.")


def ask_decimal(prompt, allow_blank=False):
    while True:
        value = input(prompt).strip()

        if allow_blank and value == "":
            return None

        try:
            return Decimal(value)
        except InvalidOperation:
            print("Invalid decimal number. Please try again.")


def ask_date(prompt, allow_blank=False):
    while True:
        value = input(prompt).strip()

        if allow_blank and value == "":
            return None

        try:
            datetime.strptime(value, "%Y-%m-%d")
            return value
        except ValueError:
            print("Invalid date format. Please use YYYY-MM-DD.")


def ask_status(prompt="Status (Active/Expired/Terminated): "):
    valid_statuses = {"Active", "Expired", "Terminated"}

    while True:
        value = input(prompt).strip()

        if value in valid_statuses:
            return value

        print("Invalid status. Please enter Active, Expired, or Terminated.")


# =========================================================
# CUSTOMER MANAGEMENT
# =========================================================

def add_customer():
    print("\nAdd customer")
    print("-" * 60)

    name = input("Customer name: ").strip()
    address = input("Address: ").strip()
    phone = input("Phone number: ").strip()
    email = input("Email: ").strip()

    if not name:
        print("\nCustomer name is required.\n")
        return

    query = """
        INSERT INTO Customers (CustomerName, Address, PhoneNumber, Email)
        VALUES (%s, %s, %s, %s)
    """

    conn = None
    cur = None

    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(query, (name, address, phone, email))
        conn.commit()

        print(f"\nCustomer added successfully.")
        print(f"New CustomerID = {cur.lastrowid}")
        print(f"Customer name  = {name}\n")

    finally:
        if cur:
            cur.close()
        if conn and conn.is_connected():
            conn.close()


def update_customer():
    print("\nUpdate customer")
    print("-" * 60)

    customer_id = ask_int("Customer ID: ")

    headers, rows = fetch_rows("""
        SELECT CustomerID, CustomerName, Address, PhoneNumber, Email
        FROM Customers
        WHERE CustomerID = %s
    """, (customer_id,))

    if not rows:
        print("\nCustomer not found.\n")
        return

    print("\nCurrent customer information:")
    print_table(headers, rows)

    current = rows[0]

    print("\nEnter new values. Leave blank to keep current value.")
    new_name = input(f"Customer name [{current[1]}]: ").strip() or current[1]
    new_address = input(f"Address [{current[2]}]: ").strip() or current[2]
    new_phone = input(f"Phone number [{current[3]}]: ").strip() or current[3]
    new_email = input(f"Email [{current[4]}]: ").strip() or current[4]

    conn = None
    cur = None

    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            UPDATE Customers
            SET CustomerName = %s,
                Address = %s,
                PhoneNumber = %s,
                Email = %s
            WHERE CustomerID = %s
        """, (new_name, new_address, new_phone, new_email, customer_id))
        conn.commit()

        print(f"\nCustomer updated successfully.")
        print(f"CustomerID    = {customer_id}")
        print(f"Customer name = {new_name}\n")

    finally:
        if cur:
            cur.close()
        if conn and conn.is_connected():
            conn.close()


def search_customer_by_name():
    print("\nSearch customer by name")
    print("-" * 60)

    keyword = input("Enter customer name keyword: ").strip()

    run_select("""
        SELECT CustomerID, CustomerName, Address, PhoneNumber, Email
        FROM Customers
        WHERE CustomerName LIKE %s
        ORDER BY CustomerID
        LIMIT 20
    """, (f"%{keyword}%",))


def view_customer_contract_history():
    print("\nCustomer contract history")
    print("-" * 60)

    customer_id = ask_int("Customer ID: ")

    if CURRENT_SESSION["profile"] == "sales":
        run_select("""
            SELECT
                cu.CustomerID,
                cu.CustomerName,
                c.ContractID,
                c.SignDate,
                c.Duration,
                'encrypted / restricted' AS TotalValueDisplay,
                c.Status
            FROM Customers cu
            JOIN Contracts c ON cu.CustomerID = c.CustomerID
            WHERE cu.CustomerID = %s
            ORDER BY c.ContractID
        """, (customer_id,))
        return

    run_select("""
        SELECT
            cu.CustomerID,
            cu.CustomerName,
            c.ContractID,
            c.SignDate,
            c.Duration,
            c.TotalValue,
            c.Status,
            COALESCE(SUM(i.TotalAmount), 0) AS TotalInvoiced,
            COALESCE(SUM(p.Amount), 0) AS TotalPaid
        FROM Customers cu
        JOIN Contracts c ON cu.CustomerID = c.CustomerID
        LEFT JOIN Invoices i ON c.ContractID = i.ContractID
        LEFT JOIN Payments p ON c.ContractID = p.ContractID
        WHERE cu.CustomerID = %s
        GROUP BY
            cu.CustomerID,
            cu.CustomerName,
            c.ContractID,
            c.SignDate,
            c.Duration,
            c.TotalValue,
            c.Status
        ORDER BY c.ContractID
    """, (customer_id,))


# =========================================================
# SERVICE MANAGEMENT
# =========================================================

def view_services():
    print("\nService catalog")
    print("-" * 60)

    run_select("""
        SELECT ServiceID, ServiceName, Description, UnitPrice
        FROM Services
        ORDER BY ServiceID
        LIMIT 50
    """)


def add_service():
    print("\nAdd service")
    print("-" * 60)

    service_name = input("Service name: ").strip()
    description = input("Description: ").strip()
    unit_price = ask_decimal("Unit price: ")

    if not service_name:
        print("\nService name is required.\n")
        return

    conn = None
    cur = None

    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO Services (ServiceName, Description, UnitPrice)
            VALUES (%s, %s, %s)
        """, (service_name, description, unit_price))
        conn.commit()

        print(f"\nService added successfully.")
        print(f"New ServiceID = {cur.lastrowid}")
        print(f"Service name  = {service_name}\n")

    finally:
        if cur:
            cur.close()
        if conn and conn.is_connected():
            conn.close()


def update_service():
    print("\nUpdate service")
    print("-" * 60)

    service_id = ask_int("Service ID: ")

    headers, rows = fetch_rows("""
        SELECT ServiceID, ServiceName, Description, UnitPrice
        FROM Services
        WHERE ServiceID = %s
    """, (service_id,))

    if not rows:
        print("\nService not found.\n")
        return

    print("\nCurrent service information:")
    print_table(headers, rows)

    current = rows[0]

    print("\nEnter new values. Leave blank to keep current value.")
    new_name = input(f"Service name [{current[1]}]: ").strip() or current[1]
    new_description = input(f"Description [{current[2]}]: ").strip() or current[2]
    new_unit_price = ask_decimal(f"Unit price [{current[3]}]: ", allow_blank=True)

    if new_unit_price is None:
        new_unit_price = current[3]

    conn = None
    cur = None

    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            UPDATE Services
            SET ServiceName = %s,
                Description = %s,
                UnitPrice = %s
            WHERE ServiceID = %s
        """, (new_name, new_description, new_unit_price, service_id))
        conn.commit()

        print(f"\nService updated successfully.")
        print(f"ServiceID    = {service_id}")
        print(f"Service name = {new_name}\n")

    finally:
        if cur:
            cur.close()
        if conn and conn.is_connected():
            conn.close()


# =========================================================
# CONTRACT MANAGEMENT
# =========================================================

def view_active_contracts():
    print("\nActive contracts")
    print("-" * 60)

    if CURRENT_SESSION["profile"] == "sales":
        try:
            run_select("""
                SELECT *
                FROM vw_active_contracts_masked
                LIMIT 20
            """)
            return
        except Error as e:
            print("\nMasked view is not available or permission was not granted.")
            print(f"Falling back to restricted base-table query. Message: {e}\n")

        run_select("""
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
            WHERE c.Status = 'Active'
            ORDER BY c.ContractID
            LIMIT 20
        """)
        return

    try:
        run_select("""
            SELECT *
            FROM vw_active_contracts
            LIMIT 20
        """)
        return
    except Error:
        pass

    run_select("""
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
        WHERE c.Status = 'Active'
        ORDER BY c.ContractID
        LIMIT 20
    """)


def create_contract():
    print("\nCreate contract")
    print("-" * 60)

    customer_id = ask_int("Customer ID: ")

    headers, rows = fetch_rows("""
        SELECT CustomerID, CustomerName, PhoneNumber, Email
        FROM Customers
        WHERE CustomerID = %s
    """, (customer_id,))

    if not rows:
        print("\nCustomer not found. Please add the customer first.\n")
        return

    print("\nCustomer information:")
    print_table(headers, rows)

    sign_date = ask_date("Sign date (YYYY-MM-DD): ")
    duration = ask_int("Duration in months: ")
    status = ask_status()

    print("\nAdd services to this contract.")
    print("Enter service items one by one. Type 0 when finished.\n")

    contract_items = []
    total_value = Decimal("0.00")

    while True:
        service_id = ask_int("Service ID (0 to finish): ")

        if service_id == 0:
            break

        service_headers, service_rows = fetch_rows("""
            SELECT ServiceID, ServiceName, UnitPrice
            FROM Services
            WHERE ServiceID = %s
        """, (service_id,))

        if not service_rows:
            print("Service not found. Please try again.")
            continue

        service = service_rows[0]
        print_table(service_headers, service_rows)

        quantity = ask_int("Quantity: ")

        if quantity <= 0:
            print("Quantity must be greater than 0.")
            continue

        unit_price = Decimal(str(service[2]))
        line_total = unit_price * quantity

        contract_items.append({
            "service_id": service_id,
            "quantity": quantity,
            "unit_price": unit_price,
            "line_total": line_total
        })

        total_value += line_total

        print(f"Added service item. Line total = {line_total}\n")

    if not contract_items:
        print("\nNo service items added. Contract creation cancelled.\n")
        return

    conn = None
    cur = None

    try:
        conn = get_connection()
        cur = conn.cursor()
        conn.start_transaction()

        cur.execute("""
            INSERT INTO Contracts (CustomerID, SignDate, Duration, TotalValue, Status)
            VALUES (%s, %s, %s, %s, %s)
        """, (customer_id, sign_date, duration, total_value, status))

        contract_id = cur.lastrowid

        for item in contract_items:
            cur.execute("""
                INSERT INTO ContractServices (ContractID, ServiceID, Quantity, UnitPrice)
                VALUES (%s, %s, %s, %s)
            """, (
                contract_id,
                item["service_id"],
                item["quantity"],
                item["unit_price"]
            ))

        conn.commit()

        print("\nContract created successfully.")
        print(f"New ContractID = {contract_id}")
        print(f"CustomerID     = {customer_id}")
        print(f"Total value    = {total_value}")
        print(f"Status         = {status}\n")

    except Exception:
        if conn:
            conn.rollback()
        raise

    finally:
        if cur:
            cur.close()
        if conn and conn.is_connected():
            conn.close()


def update_contract_status():
    print("\nUpdate contract status")
    print("-" * 60)

    contract_id = ask_int("Contract ID: ")

    headers, rows = fetch_rows("""
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
        WHERE c.ContractID = %s
    """, (contract_id,))

    if not rows:
        print("\nContract not found.\n")
        return

    print("\nCurrent contract information:")
    print_table(headers, rows)

    new_status = ask_status("New status (Active/Expired/Terminated): ")

    conn = None
    cur = None

    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            UPDATE Contracts
            SET Status = %s
            WHERE ContractID = %s
        """, (new_status, contract_id))
        conn.commit()

        print("\nContract status updated successfully.")
        print(f"ContractID = {contract_id}")
        print(f"New status = {new_status}\n")

    finally:
        if cur:
            cur.close()
        if conn and conn.is_connected():
            conn.close()


def view_contract_services():
    print("\nView contract services")
    print("-" * 60)

    contract_id = ask_int("Contract ID: ")

    run_select("""
        SELECT
            cs.ContractServiceID,
            cs.ContractID,
            s.ServiceID,
            s.ServiceName,
            cs.Quantity,
            cs.UnitPrice,
            cs.Quantity * cs.UnitPrice AS LineTotal
        FROM ContractServices cs
        JOIN Services s ON cs.ServiceID = s.ServiceID
        WHERE cs.ContractID = %s
        ORDER BY cs.ContractServiceID
    """, (contract_id,))


# =========================================================
# INVOICE AND PAYMENT MANAGEMENT
# =========================================================

def view_unpaid_invoices():
    print("\nUnpaid / overdue invoices")
    print("-" * 60)

    run_select("""
        SELECT *
        FROM vw_unpaid_invoices
        ORDER BY DueDate, InvoiceID
        LIMIT 20
    """)


def generate_invoice():
    print("\nGenerate invoice")
    print("-" * 60)

    contract_id = ask_int("Contract ID: ")
    issue_date = ask_date("Issue date (YYYY-MM-DD): ")
    due_date = ask_date("Due date (YYYY-MM-DD): ")

    run_call("sp_generate_invoice", [contract_id, issue_date, due_date])

    print("\nInvoice generated successfully.\n")

    run_select("""
        SELECT
            InvoiceID,
            ContractID,
            IssueDate,
            DueDate,
            TotalAmount,
            InvoiceStatus
        FROM Invoices
        WHERE ContractID = %s
        ORDER BY InvoiceID DESC
        LIMIT 5
    """, (contract_id,))


def record_payment():
    print("\nRecord payment")
    print("-" * 60)

    contract_id = ask_int("Contract ID: ")
    payment_date = ask_date("Payment date (YYYY-MM-DD): ")
    amount = ask_decimal("Amount: ")
    payment_method = input("Payment method: ").strip()

    if not payment_method:
        print("\nPayment method is required.\n")
        return

    run_call("sp_record_payment", [contract_id, payment_date, amount, payment_method])

    print("\nPayment recorded successfully.")
    print("The payment trigger will also update related invoice and contract status if applicable.\n")

    print("Recent payments:")
    run_select("""
        SELECT
            PaymentID,
            ContractID,
            PaymentDate,
            Amount,
            PaymentMethod
        FROM Payments
        WHERE ContractID = %s
        ORDER BY PaymentID DESC
        LIMIT 5
    """, (contract_id,))

    print("\nRelated invoices:")
    run_select("""
        SELECT
            InvoiceID,
            ContractID,
            IssueDate,
            DueDate,
            TotalAmount,
            InvoiceStatus
        FROM Invoices
        WHERE ContractID = %s
        ORDER BY InvoiceID DESC
        LIMIT 5
    """, (contract_id,))

    print("\nContract status:")
    run_select("""
        SELECT ContractID, CustomerID, TotalValue, Status
        FROM Contracts
        WHERE ContractID = %s
    """, (contract_id,))


# =========================================================
# REPORTING
# =========================================================

def view_customer_billing_summary():
    print("\nCustomer billing summary")
    print("-" * 60)

    run_select("""
        SELECT *
        FROM vw_customer_billing_summary
        ORDER BY CustomerID
        LIMIT 20
    """)


def view_monthly_revenue():
    print("\nMonthly revenue")
    print("-" * 60)

    year = ask_int("Year: ")
    month = ask_int("Month (1-12): ")

    if month < 1 or month > 12:
        print("\nInvalid month.\n")
        return

    headers, rows = fetch_rows("""
        SELECT fn_monthly_revenue(%s, %s) AS MonthlyRevenue
    """, (year, month))

    print()
    print_table(headers, rows)


def view_remaining_contract_value():
    print("\nRemaining contract value")
    print("-" * 60)

    contract_id = ask_int("Contract ID: ")

    headers, rows = fetch_rows("""
        SELECT fn_remaining_contract_value(%s) AS RemainingValue
    """, (contract_id,))

    print()
    print_table(headers, rows)


def export_csv(filename, headers, rows):
    report_dir = "reports"
    os.makedirs(report_dir, exist_ok=True)

    filepath = os.path.join(report_dir, filename)

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)

    return filepath


def generate_reports():
    print("\nGenerate reports")
    print("-" * 60)
    print("1. Customer billing summary report")
    print("2. Monthly revenue report")
    print("3. Unpaid / overdue invoices report")
    print("4. Generate all reports")

    choice = input("Choose report option: ").strip()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    generated_files = []

    if choice == "1":
        headers, rows = fetch_rows("""
            SELECT *
            FROM vw_customer_billing_summary
            ORDER BY CustomerID
        """)

        generated_files.append(
            export_csv(f"customer_billing_summary_{timestamp}.csv", headers, rows)
        )

    elif choice == "2":
        year = ask_int("Year: ")
        month = ask_int("Month (1-12): ")

        if month < 1 or month > 12:
            print("\nInvalid month.\n")
            return

        headers, rows = fetch_rows("""
            SELECT
                %s AS ReportYear,
                %s AS ReportMonth,
                fn_monthly_revenue(%s, %s) AS MonthlyRevenue
        """, (year, month, year, month))

        generated_files.append(
            export_csv(f"monthly_revenue_{year}_{month}_{timestamp}.csv", headers, rows)
        )

    elif choice == "3":
        headers, rows = fetch_rows("""
            SELECT *
            FROM vw_unpaid_invoices
            ORDER BY DueDate, InvoiceID
        """)

        generated_files.append(
            export_csv(f"unpaid_invoices_{timestamp}.csv", headers, rows)
        )

    elif choice == "4":
        headers, rows = fetch_rows("""
            SELECT *
            FROM vw_customer_billing_summary
            ORDER BY CustomerID
        """)

        generated_files.append(
            export_csv(f"customer_billing_summary_{timestamp}.csv", headers, rows)
        )

        year = ask_int("Year for monthly revenue report: ")
        month = ask_int("Month for monthly revenue report (1-12): ")

        if month < 1 or month > 12:
            print("\nInvalid month.\n")
            return

        headers, rows = fetch_rows("""
            SELECT
                %s AS ReportYear,
                %s AS ReportMonth,
                fn_monthly_revenue(%s, %s) AS MonthlyRevenue
        """, (year, month, year, month))

        generated_files.append(
            export_csv(f"monthly_revenue_{year}_{month}_{timestamp}.csv", headers, rows)
        )

        headers, rows = fetch_rows("""
            SELECT *
            FROM vw_unpaid_invoices
            ORDER BY DueDate, InvoiceID
        """)

        generated_files.append(
            export_csv(f"unpaid_invoices_{timestamp}.csv", headers, rows)
        )

    else:
        print("\nInvalid report option.\n")
        return

    print("\nReport file(s) generated successfully:")
    for path in generated_files:
        print(f"- {path}")
    print()


# =========================================================
# SECURITY AND ADMINISTRATION DEMO
# =========================================================

def view_current_db_user():
    print("\nCurrent database user and role")
    print("-" * 60)

    run_select("""
        SELECT
            USER() AS LoginUser,
            CURRENT_USER() AS AuthenticatedUser,
            CURRENT_ROLE() AS CurrentRole
    """)


def view_my_grants():
    print("\nCurrent user grants")
    print("-" * 60)

    conn = None
    cur = None

    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SHOW GRANTS")
        rows = cur.fetchall()
        headers = [desc[0] for desc in cur.description]

        print()
        print_table(headers, rows)

    finally:
        if cur:
            cur.close()
        if conn and conn.is_connected():
            conn.close()


def test_restricted_access():
    print("\nSecurity permission test")
    print("-" * 60)
    print("This test tries to read the Payments table directly.")
    print("Expected result:")
    print("- sales_user   : access denied")
    print("- finance_user : access granted")
    print("- admin_user   : access granted")

    try:
        run_select("""
            SELECT
                PaymentID,
                ContractID,
                PaymentDate,
                Amount,
                PaymentMethod
            FROM Payments
            LIMIT 5
        """)
        print("\nAccess granted by the current database role.\n")

    except Error as e:
        print("\nAccess denied or restricted by the current database role.")
        print(f"Database message: {e}\n")


def view_contract_encryption_check():
    print("\nContract encryption check")
    print("-" * 60)

    run_select("""
        SELECT
            ContractID,
            TotalValue,
            TotalValueCipherText,
            DecryptedTotalValue
        FROM vw_contract_encryption_check
        LIMIT 10
    """)


def view_payment_encryption_check():
    print("\nPayment encryption check")
    print("-" * 60)

    run_select("""
        SELECT
            PaymentID,
            ContractID,
            Amount,
            AmountCipherText,
            DecryptedAmount
        FROM vw_payment_encryption_check
        LIMIT 10
    """)


def verify_sample_data_counts():
    print("\nSample data count verification")
    print("-" * 60)

    run_select("""
        SELECT 'Customers' AS TableName, COUNT(*) AS TotalRows FROM Customers
        UNION ALL
        SELECT 'Services' AS TableName, COUNT(*) AS TotalRows FROM Services
        UNION ALL
        SELECT 'Contracts' AS TableName, COUNT(*) AS TotalRows FROM Contracts
        UNION ALL
        SELECT 'ContractServices' AS TableName, COUNT(*) AS TotalRows FROM ContractServices
        UNION ALL
        SELECT 'Invoices' AS TableName, COUNT(*) AS TotalRows FROM Invoices
        UNION ALL
        SELECT 'Payments' AS TableName, COUNT(*) AS TotalRows FROM Payments
    """)


def view_index_and_optimization_checks():
    print("\nQuery optimization checks")
    print("-" * 60)

    print("\nEXPLAIN: Contracts lookup by CustomerID and Status")
    run_select("""
        EXPLAIN
        SELECT *
        FROM Contracts
        WHERE CustomerID = 10
          AND Status = 'Active'
    """)

    print("\nEXPLAIN: Payments lookup by ContractID and PaymentDate")
    run_select("""
        EXPLAIN
        SELECT *
        FROM Payments
        WHERE ContractID = 10
        ORDER BY PaymentDate DESC
    """)

    print("\nEXPLAIN: Invoices lookup by ContractID and InvoiceStatus")
    run_select("""
        EXPLAIN
        SELECT *
        FROM Invoices
        WHERE ContractID = 10
          AND InvoiceStatus = 'Unpaid'
    """)


def show_backup_recovery_commands():
    print("\nBackup and recovery commands")
    print("-" * 60)

    print("\n1. Create a backup folder if it does not exist:")
    print("mkdir backups")

    print("\n2. Logical backup command:")
    print("mysqldump -u admin_user -p --single-transaction --routines --triggers --events mydb > backups\\mydb_project15_backup.sql")

    print("\n3. Recovery command into the existing mydb database:")
    print("mysql -u admin_user -p mydb < backups\\mydb_project15_backup.sql")

    print("\n4. Optional restore-test workflow using root:")
    print('mysql -u root -p -e "DROP DATABASE IF EXISTS mydb_restore_test; CREATE DATABASE mydb_restore_test;"')
    print("mysql -u root -p mydb_restore_test < backups\\mydb_project15_backup.sql")

    print("\n5. Verification query after restore:")
    print("SELECT 'Customers' AS TableName, COUNT(*) AS TotalRows FROM Customers")
    print("UNION ALL SELECT 'Services', COUNT(*) FROM Services")
    print("UNION ALL SELECT 'Contracts', COUNT(*) FROM Contracts")
    print("UNION ALL SELECT 'ContractServices', COUNT(*) FROM ContractServices")
    print("UNION ALL SELECT 'Invoices', COUNT(*) FROM Invoices")
    print("UNION ALL SELECT 'Payments', COUNT(*) FROM Payments;")

    print("\nNote:")
    print("Backup and recovery are administrative operations.")
    print("They are normally executed outside the CLI using standard MySQL tools.\n")


# =========================================================
# MENU CONFIGURATION
# =========================================================

def get_menu_items():
    profile = CURRENT_SESSION["profile"]

    security_common = [
        ("90", "View current database user and role", view_current_db_user),
        ("91", "View my grants", view_my_grants),
        ("92", "Test restricted access to Payments table", test_restricted_access),
    ]

    if profile == "sales":
        return [
            ("1", "Add customer", add_customer),
            ("2", "Update customer", update_customer),
            ("3", "Search customer by name", search_customer_by_name),
            ("4", "View service catalog", view_services),
            ("5", "Create contract", create_contract),
            ("6", "Update contract status", update_contract_status),
            ("7", "View active contracts", view_active_contracts),
            ("8", "View contract services", view_contract_services),
            ("9", "View customer contract history", view_customer_contract_history),
            *security_common,
            ("0", "Exit", None),
        ]

    if profile == "finance":
        return [
            ("1", "View active contracts", view_active_contracts),
            ("2", "View contract services", view_contract_services),
            ("3", "View unpaid / overdue invoices", view_unpaid_invoices),
            ("4", "Generate invoice", generate_invoice),
            ("5", "Record payment", record_payment),
            ("6", "View customer billing summary", view_customer_billing_summary),
            ("7", "View monthly revenue", view_monthly_revenue),
            ("8", "View remaining contract value", view_remaining_contract_value),
            ("9", "Generate CSV reports", generate_reports),
            ("10", "View contract encryption check", view_contract_encryption_check),
            ("11", "View payment encryption check", view_payment_encryption_check),
            *security_common,
            ("0", "Exit", None),
        ]

    if profile == "admin":
        return [
            ("1", "Add customer", add_customer),
            ("2", "Update customer", update_customer),
            ("3", "Search customer by name", search_customer_by_name),
            ("4", "View service catalog", view_services),
            ("5", "Add service", add_service),
            ("6", "Update service", update_service),
            ("7", "Create contract", create_contract),
            ("8", "Update contract status", update_contract_status),
            ("9", "View active contracts", view_active_contracts),
            ("10", "View contract services", view_contract_services),
            ("11", "View customer contract history", view_customer_contract_history),
            ("12", "View unpaid / overdue invoices", view_unpaid_invoices),
            ("13", "Generate invoice", generate_invoice),
            ("14", "Record payment", record_payment),
            ("15", "View customer billing summary", view_customer_billing_summary),
            ("16", "View monthly revenue", view_monthly_revenue),
            ("17", "View remaining contract value", view_remaining_contract_value),
            ("18", "Generate CSV reports", generate_reports),
            ("19", "Verify sample data counts", verify_sample_data_counts),
            ("20", "View contract encryption check", view_contract_encryption_check),
            ("21", "View payment encryption check", view_payment_encryption_check),
            ("22", "View query optimization checks", view_index_and_optimization_checks),
            ("23", "Show backup and recovery commands", show_backup_recovery_commands),
            *security_common,
            ("0", "Exit", None),
        ]

    return [
        ("0", "Exit", None),
    ]


def show_menu():
    print("\n" + "=" * 78)
    print(" CUSTOMER AND CONTRACT MANAGEMENT SYSTEM - PYTHON CLI ")
    print("=" * 78)
    print(f" Logged in as : {CURRENT_SESSION['user']}")
    print(f" Role profile : {CURRENT_SESSION['profile']}")
    print("=" * 78)

    for key, label, _ in get_menu_items():
        print(f"{key}. {label}")

    print("=" * 78)


# =========================================================
# MAIN PROGRAM
# =========================================================

def main():
    if not login():
        return

    while True:
        show_menu()
        choice = input("Choose an option: ").strip()

        menu_items = get_menu_items()
        menu_dict = {key: action for key, _, action in menu_items}

        if choice == "0":
            print("\nExit program.")
            break

        if choice not in menu_dict:
            print("\nInvalid choice or permission not available for this role.\n")
            continue

        try:
            action = menu_dict[choice]
            action()

        except Error as e:
            print("\nDatabase error.")
            print(f"Message: {e}\n")

        except RuntimeError as e:
            print("\nRuntime error.")
            print(f"Message: {e}\n")

        except ValueError:
            print("\nInvalid input type.\n")

        except KeyboardInterrupt:
            print("\n\nProgram interrupted by user.")
            break

        except Exception as e:
            print("\nUnexpected error.")
            print(f"Message: {e}\n")


if __name__ == "__main__":
    main()
