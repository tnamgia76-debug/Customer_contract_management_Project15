USE mydb;

DROP FUNCTION IF EXISTS fn_remaining_contract_value;
DROP FUNCTION IF EXISTS fn_monthly_revenue;

DELIMITER $$

CREATE FUNCTION fn_remaining_contract_value(p_contract_id INT)
RETURNS DECIMAL(12,2)
DETERMINISTIC
READS SQL DATA
BEGIN
    DECLARE v_total_value DECIMAL(12,2);
    DECLARE v_total_paid DECIMAL(12,2);

    SELECT TotalValue
    INTO v_total_value
    FROM Contracts
    WHERE ContractID = p_contract_id;

    SELECT COALESCE(SUM(Amount), 0)
    INTO v_total_paid
    FROM Payments
    WHERE ContractID = p_contract_id;

    RETURN COALESCE(v_total_value, 0) - COALESCE(v_total_paid, 0);
END $$


CREATE FUNCTION fn_monthly_revenue(p_year INT, p_month INT)
RETURNS DECIMAL(12,2)
DETERMINISTIC
READS SQL DATA
BEGIN
    DECLARE v_revenue DECIMAL(12,2);

    SELECT COALESCE(SUM(Amount), 0)
    INTO v_revenue
    FROM Payments
    WHERE YEAR(PaymentDate) = p_year
      AND MONTH(PaymentDate) = p_month;

    RETURN v_revenue;
END $$

DELIMITER ;