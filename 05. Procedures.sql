USE mydb;

DROP PROCEDURE IF EXISTS sp_generate_invoice;
DROP PROCEDURE IF EXISTS sp_record_payment;

DELIMITER $$

CREATE PROCEDURE sp_generate_invoice(
    IN p_contract_id INT,
    IN p_issue_date DATE,
    IN p_due_date DATE
)
BEGIN
    DECLARE v_total_amount DECIMAL(12,2);

    SELECT COALESCE(SUM(Quantity * UnitPrice), 0)
    INTO v_total_amount
    FROM ContractServices
    WHERE ContractID = p_contract_id;

    INSERT INTO Invoices (
        ContractID,
        IssueDate,
        DueDate,
        TotalAmount,
        InvoiceStatus
    )
    VALUES (
        p_contract_id,
        p_issue_date,
        p_due_date,
        v_total_amount,
        'Unpaid'
    );
END $$


CREATE PROCEDURE sp_record_payment(
    IN p_contract_id INT,
    IN p_payment_date DATE,
    IN p_amount DECIMAL(12,2),
    IN p_payment_method VARCHAR(50)
)
BEGIN
    INSERT INTO Payments (
        ContractID,
        PaymentDate,
        Amount,
        PaymentMethod
    )
    VALUES (
        p_contract_id,
        p_payment_date,
        p_amount,
        p_payment_method
    );
END $$

DELIMITER ;
