USE mydb;

DROP TRIGGER IF EXISTS trg_invoices_before_insert;
DROP TRIGGER IF EXISTS trg_invoices_before_update;
DROP TRIGGER IF EXISTS trg_payments_after_insert;

DELIMITER $$

CREATE TRIGGER trg_invoices_before_insert
BEFORE INSERT ON Invoices
FOR EACH ROW
BEGIN
    IF NEW.InvoiceStatus IS NULL OR NEW.InvoiceStatus = '' THEN
        IF NEW.DueDate < CURDATE() THEN
            SET NEW.InvoiceStatus = 'Overdue';
        ELSE
            SET NEW.InvoiceStatus = 'Unpaid';
        END IF;
    END IF;
END $$


CREATE TRIGGER trg_invoices_before_update
BEFORE UPDATE ON Invoices
FOR EACH ROW
BEGIN
    IF NEW.InvoiceStatus <> 'Paid' AND NEW.DueDate < CURDATE() THEN
        SET NEW.InvoiceStatus = 'Overdue';
    END IF;
END $$


CREATE TRIGGER trg_payments_after_insert
AFTER INSERT ON Payments
FOR EACH ROW
BEGIN
    DECLARE v_total_paid DECIMAL(12,2);
    DECLARE v_total_invoice DECIMAL(12,2);
    DECLARE v_overdue_count INT;

    SELECT COALESCE(SUM(Amount), 0)
    INTO v_total_paid
    FROM Payments
    WHERE ContractID = NEW.ContractID;

    SELECT COALESCE(SUM(TotalAmount), 0)
    INTO v_total_invoice
    FROM Invoices
    WHERE ContractID = NEW.ContractID;

    IF v_total_paid >= v_total_invoice AND v_total_invoice > 0 THEN
        UPDATE Invoices
        SET InvoiceStatus = 'Paid'
        WHERE ContractID = NEW.ContractID
          AND InvoiceStatus IN ('Unpaid', 'Overdue');
    END IF;

    SELECT COUNT(*)
    INTO v_overdue_count
    FROM Invoices
    WHERE ContractID = NEW.ContractID
      AND DueDate < CURDATE()
      AND InvoiceStatus <> 'Paid';

    IF v_overdue_count > 0 THEN
        UPDATE Contracts
        SET Status = 'Terminated'
        WHERE ContractID = NEW.ContractID;
    ELSE
        UPDATE Contracts
        SET Status = 'Active'
        WHERE ContractID = NEW.ContractID;
    END IF;
END $$

DELIMITER ;
