import csv
import os
from datetime import datetime
from getpass import getpass

import mysql.connector
from mysql.connector import Error

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "mydb",
}

_CACHED_PASSWORD = None


def get_connection():
    global _CACHED_PASSWORD
    config = DB_CONFIG.copy()

    if not config["password"]:
        if _CACHED_PASSWORD is None:
            _CACHED_PASSWORD = getpass("MySQL password: ")
        config["password"] = _CACHED_PASSWORD

    return mysql.connector.connect(**config)


def print_table(headers, rows):
    if not rows:
        print("\nNo data found.\n")
        return

    widths = [len(str(h)) for h in headers]
    for row in rows:
        for i, value in enumerate(row):
            widths[i] = max(widths[i], len("" if value is None else str(value)))

    line = "+-" + "-+-".join("-" * w for w in widths) + "-+"
    print(line)
    print("| " + " | ".join(str(h).ljust(widths[i]) for i, h in enumerate(headers)) + " |")
    print(line)
    for row in rows:
        print("| " + " | ".join(("" if v is None else str(v)).ljust(widths[i]) for i, v in enumerate(row)) + " |")
    print(line)


def fetch_rows(query, params=None):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(query, params or ())
        rows = cur.fetchall()
        headers = [desc[0] for desc in cur.description]
        return headers, rows
    finally:
        cur.close()
        conn.close()


def run_select(query, params=None):
    headers, rows = fetch_rows(query, params)
    print()
    print_table(headers, rows)


def run_call(proc_name, args):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.callproc(proc_name, args)
        conn.commit()
    finally:
        cur.close()
        conn.close()


def add_customer():
    print("\nAdd customer")
    name = input("Customer name: ").strip()
    address = input("Address: ").strip()
    phone = input("Phone number: ").strip()
    email = input("Email: ").strip()

    query = """
        INSERT INTO Customers (CustomerName, Address, PhoneNumber, Email)
        VALUES (%s, %s, %s, %s)
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(query, (name, address, phone, email))
        conn.commit()
        print(f"\nCustomer added successfully. New CustomerID = {cur.lastrowid}\n")
    finally:
        cur.close()
        conn.close()


def search_customer_by_name():
    print("\nSearch customer by name")
    keyword = input("Enter customer name keyword: ").strip()

    run_select("""
        SELECT CustomerID, CustomerName, Address, PhoneNumber, Email
        FROM Customers
        WHERE CustomerName LIKE %s
        ORDER BY CustomerID
        LIMIT 20
    """, (f"%{keyword}%",))


def view_active_contracts():
    print("\nActive contracts")
    run_select("SELECT * FROM vw_active_contracts LIMIT 20")


def view_unpaid_invoices():
    print("\nUnpaid / overdue invoices")
    run_select("SELECT * FROM vw_unpaid_invoices LIMIT 20")


def generate_invoice():
    print("\nGenerate invoice")
    contract_id = int(input("Contract ID: ").strip())
    issue_date = input("Issue date (YYYY-MM-DD): ").strip()
    due_date = input("Due date (YYYY-MM-DD): ").strip()

    run_call("sp_generate_invoice", [contract_id, issue_date, due_date])
    print("\nInvoice generated successfully.\n")

    run_select("""
        SELECT InvoiceID, ContractID, IssueDate, DueDate, TotalAmount, InvoiceStatus
        FROM Invoices
        WHERE ContractID = %s
        ORDER BY InvoiceID DESC
        LIMIT 5
    """, (contract_id,))


def record_payment():
    print("\nRecord payment")
    contract_id = int(input("Contract ID: ").strip())
    payment_date = input("Payment date (YYYY-MM-DD): ").strip()
    amount = float(input("Amount: ").strip())
    payment_method = input("Payment method: ").strip()

    run_call("sp_record_payment", [contract_id, payment_date, amount, payment_method])
    print("\nPayment recorded successfully.\n")

    run_select("""
        SELECT PaymentID, ContractID, PaymentDate, Amount, PaymentMethod
        FROM Payments
        WHERE ContractID = %s
        ORDER BY PaymentID DESC
        LIMIT 5
    """, (contract_id,))


def view_customer_billing_summary():
    print("\nCustomer billing summary")
    run_select("SELECT * FROM vw_customer_billing_summary LIMIT 20")


def view_monthly_revenue():
    print("\nMonthly revenue")
    year = int(input("Year: ").strip())
    month = int(input("Month (1-12): ").strip())

    headers, rows = fetch_rows(
        "SELECT fn_monthly_revenue(%s, %s) AS MonthlyRevenue",
        (year, month)
    )
    print()
    print_table(headers, rows)


def view_remaining_contract_value():
    print("\nRemaining contract value")
    contract_id = int(input("Contract ID: ").strip())

    headers, rows = fetch_rows(
        "SELECT fn_remaining_contract_value(%s) AS RemainingValue",
        (contract_id,)
    )
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
        year = int(input("Year: ").strip())
        month = int(input("Month (1-12): ").strip())
        headers, rows = fetch_rows(
            "SELECT %s AS ReportYear, %s AS ReportMonth, fn_monthly_revenue(%s, %s) AS MonthlyRevenue",
            (year, month, year, month)
        )
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

        year = int(input("Year for monthly revenue report: ").strip())
        month = int(input("Month for monthly revenue report (1-12): ").strip())
        headers, rows = fetch_rows(
            "SELECT %s AS ReportYear, %s AS ReportMonth, fn_monthly_revenue(%s, %s) AS MonthlyRevenue",
            (year, month, year, month)
        )
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


def show_menu():
    print("\n" + "=" * 58)
    print(" CUSTOMER AND CONTRACT MANAGEMENT SYSTEM - PYTHON CLI ")
    print("=" * 58)
    print("1. Add customer")
    print("2. Search customer by name")
    print("3. View active contracts")
    print("4. View unpaid / overdue invoices")
    print("5. Generate invoice")
    print("6. Record payment")
    print("7. View customer billing summary")
    print("8. View monthly revenue")
    print("9. View remaining contract value")
    print("10. Generate reports")
    print("0. Exit")
    print("=" * 58)


def main():
    while True:
        show_menu()
        choice = input("Choose an option: ").strip()

        try:
            if choice == "1":
                add_customer()
            elif choice == "2":
                search_customer_by_name()
            elif choice == "3":
                view_active_contracts()
            elif choice == "4":
                view_unpaid_invoices()
            elif choice == "5":
                generate_invoice()
            elif choice == "6":
                record_payment()
            elif choice == "7":
                view_customer_billing_summary()
            elif choice == "8":
                view_monthly_revenue()
            elif choice == "9":
                view_remaining_contract_value()
            elif choice == "10":
                generate_reports()
            elif choice == "0":
                print("\nExit program.")
                break
            else:
                print("\nInvalid choice.\n")
        except Error as e:
            print(f"\nDatabase error: {e}\n")
        except ValueError:
            print("\nInvalid input type.\n")
        except Exception as e:
            print(f"\nUnexpected error: {e}\n")


if __name__ == "__main__":
    main()
