-- 1. Total patients, devices, transmissions, and alerts

SELECT 
    (SELECT COUNT(*) FROM patients) AS total_patients,
    (SELECT COUNT(*) FROM devices) AS total_devices,
    (SELECT COUNT(*) FROM transmissions) AS total_transmissions,
    (SELECT COUNT(*) FROM alerts) AS total_alerts;

-- 2. Alert count by severity

SELECT 
    severity,
    COUNT(*) AS total_alerts
FROM alerts
GROUP BY severity
ORDER BY total_alerts DESC;

-- 3. Open alerts by clinic

SELECT
    c.clinic_id,
    c.clinic_name,
    COUNT(a.alert_id) AS open_alerts
FROM alerts a
JOIN patients p 
    ON a.patient_id = p.patient_id
JOIN clinics c 
    ON p.clinic_id = c.clinic_id
WHERE a.status = 'Open'
GROUP BY c.clinic_id, c.clinic_name
ORDER BY open_alerts DESC;

-- 4. Critical unresolved alerts

SELECT
    a.alert_id,
    p.patient_id,
    p.age,
    p.condition,
    d.device_type,
    c.clinic_name,
    a.alert_type,
    a.severity,
    a.status,
    a.alert_date
FROM alerts a
JOIN patients p 
    ON a.patient_id = p.patient_id
JOIN devices d 
    ON a.device_id = d.device_id
JOIN clinics c 
    ON p.clinic_id = c.clinic_id
WHERE a.severity = 'Critical'
  AND a.status IN ('Open', 'Escalated')
ORDER BY a.alert_date DESC;

-- 5. Average alert resolution time by clinic

SELECT
    c.clinic_name,
    ROUND(AVG(a.resolved_date - a.alert_date), 2) AS avg_resolution_days
FROM alerts a
JOIN patients p 
    ON a.patient_id = p.patient_id
JOIN clinics c 
    ON p.clinic_id = c.clinic_id
WHERE a.resolved_date IS NOT NULL
GROUP BY c.clinic_name
ORDER BY avg_resolution_days DESC;

-- 6. Percentage of alerts resolved within 24 hours

SELECT
    ROUND(
        100.0 * SUM(
            CASE 
                WHEN resolved_date IS NOT NULL 
                 AND resolved_date - alert_date <= 1 
                THEN 1 ELSE 0 
            END
        ) / COUNT(*), 
        2
    ) AS resolved_within_24_hours_percentage
FROM alerts;

-- 7. Missed transmission rate by device type

SELECT
    d.device_type,
    COUNT(*) AS total_transmissions,
    SUM(CASE WHEN t.transmission_status = 'Missed' THEN 1 ELSE 0 END) AS missed_transmissions,
    ROUND(
        100.0 * SUM(CASE WHEN t.transmission_status = 'Missed' THEN 1 ELSE 0 END) / COUNT(*),
        2
    ) AS missed_transmission_rate
FROM transmissions t
JOIN devices d 
    ON t.device_id = d.device_id
GROUP BY d.device_type
ORDER BY missed_transmission_rate DESC;

-- 8. Low battery devices

SELECT
    d.device_id,
    d.patient_id,
    d.device_type,
    d.manufacturer,
    MIN(t.battery_level) AS lowest_recorded_battery
FROM devices d
JOIN transmissions t 
    ON d.device_id = t.device_id
GROUP BY d.device_id, d.patient_id, d.device_type, d.manufacturer
HAVING MIN(t.battery_level) < 15
ORDER BY lowest_recorded_battery ASC;

-- 9. Most common diagnostic findings

SELECT
    finding_type,
    COUNT(*) AS total_findings
FROM diagnostic_findings
GROUP BY finding_type
ORDER BY total_findings DESC;

-- 10. Clinic workload based on alerts and appointments

SELECT
    c.clinic_name,
    COUNT(DISTINCT a.alert_id) AS total_alerts,
    COUNT(DISTINCT ap.appointment_id) AS total_appointments,
    COUNT(DISTINCT a.alert_id) + COUNT(DISTINCT ap.appointment_id) AS total_workload
FROM clinics c
LEFT JOIN patients p 
    ON c.clinic_id = p.clinic_id
LEFT JOIN alerts a 
    ON p.patient_id = a.patient_id
LEFT JOIN appointments ap 
    ON c.clinic_id = ap.clinic_id
GROUP BY c.clinic_name
ORDER BY total_workload DESC;

-- Monthly transmission trends
SELECT
    DATE_TRUNC('month', transmission_date)::DATE AS month,
    COUNT(*) AS total_transmissions,
    SUM(CASE WHEN transmission_status = 'Received' THEN 1 ELSE 0 END) AS received_transmissions,
    SUM(CASE WHEN transmission_status = 'Missed' THEN 1 ELSE 0 END) AS missed_transmissions,
    SUM(CASE WHEN transmission_status = 'Failed' THEN 1 ELSE 0 END) AS failed_transmissions
FROM transmissions
GROUP BY DATE_TRUNC('month', transmission_date)
ORDER BY month;

-- Alert resolution performance by clinic
SELECT
    c.clinic_name,
    COUNT(a.alert_id) AS total_alerts,
    SUM(CASE WHEN a.status = 'Open' THEN 1 ELSE 0 END) AS open_alerts,
    SUM(CASE WHEN a.status = 'Resolved' THEN 1 ELSE 0 END) AS resolved_alerts,
    SUM(CASE WHEN a.status = 'Escalated' THEN 1 ELSE 0 END) AS escalated_alerts,
    ROUND(
        AVG(CASE 
            WHEN a.resolved_date IS NOT NULL 
            THEN a.resolved_date - a.alert_date 
        END), 
        2
    ) AS avg_resolution_days
FROM alerts a
JOIN patients p 
    ON a.patient_id = p.patient_id
JOIN clinics c 
    ON p.clinic_id = c.clinic_id
GROUP BY c.clinic_name
ORDER BY open_alerts DESC;

-- Alerts resolved within 24 hours by clinic
SELECT
    c.clinic_name,
    COUNT(a.alert_id) AS total_alerts,
    SUM(
        CASE 
            WHEN a.resolved_date IS NOT NULL 
             AND a.resolved_date - a.alert_date <= 1
            THEN 1 ELSE 0 
        END
    ) AS resolved_within_24h,
    ROUND(
        100.0 * SUM(
            CASE 
                WHEN a.resolved_date IS NOT NULL 
                 AND a.resolved_date - a.alert_date <= 1
                THEN 1 ELSE 0 
            END
        ) / COUNT(a.alert_id),
        2
    ) AS resolved_within_24h_percentage
FROM alerts a
JOIN patients p 
    ON a.patient_id = p.patient_id
JOIN clinics c 
    ON p.clinic_id = c.clinic_id
GROUP BY c.clinic_name
ORDER BY resolved_within_24h_percentage ASC;

-- Critical open alerts requiring urgent review
SELECT
    a.alert_id,
    a.alert_date,
    a.alert_type,
    a.severity,
    a.status,
    p.patient_id,
    p.age,
    p.gender,
    p.condition,
    d.device_type,
    d.manufacturer,
    c.clinic_name
FROM alerts a
JOIN patients p 
    ON a.patient_id = p.patient_id
JOIN devices d 
    ON a.device_id = d.device_id
JOIN clinics c 
    ON p.clinic_id = c.clinic_id
WHERE a.severity = 'Critical'
  AND a.status IN ('Open', 'Escalated')
ORDER BY a.alert_date DESC;

-- Device risk score
WITH device_metrics AS (
    SELECT
        d.device_id,
        d.patient_id,
        d.device_type,
        d.manufacturer,
        COUNT(t.transmission_id) AS total_transmissions,
        SUM(CASE WHEN t.transmission_status IN ('Missed', 'Failed') THEN 1 ELSE 0 END) AS failed_or_missed_transmissions,
        MIN(t.battery_level) AS lowest_battery_level,
        COUNT(a.alert_id) AS total_alerts,
        SUM(CASE WHEN a.severity = 'Critical' THEN 1 ELSE 0 END) AS critical_alerts
    FROM devices d
    LEFT JOIN transmissions t 
        ON d.device_id = t.device_id
    LEFT JOIN alerts a 
        ON d.device_id = a.device_id
    GROUP BY d.device_id, d.patient_id, d.device_type, d.manufacturer
)

SELECT
    device_id,
    patient_id,
    device_type,
    manufacturer,
    total_transmissions,
    failed_or_missed_transmissions,
    lowest_battery_level,
    total_alerts,
    critical_alerts,
    (
        failed_or_missed_transmissions * 2
        + critical_alerts * 5
        + CASE WHEN lowest_battery_level < 15 THEN 10 ELSE 0 END
    ) AS device_risk_score
FROM device_metrics
ORDER BY device_risk_score DESC;

-- Patients with repeated missed transmissions
SELECT
    p.patient_id,
    p.age,
    p.gender,
    p.condition,
    c.clinic_name,
    d.device_type,
    COUNT(t.transmission_id) AS total_missed_transmissions
FROM transmissions t
JOIN patients p 
    ON t.patient_id = p.patient_id
JOIN devices d 
    ON t.device_id = d.device_id
JOIN clinics c 
    ON p.clinic_id = c.clinic_id
WHERE t.transmission_status = 'Missed'
GROUP BY 
    p.patient_id,
    p.age,
    p.gender,
    p.condition,
    c.clinic_name,
    d.device_type
HAVING COUNT(t.transmission_id) >= 3
ORDER BY total_missed_transmissions DESC;

-- Most common diagnostic findings by condition
SELECT
    p.condition,
    df.finding_type,
    COUNT(df.finding_id) AS total_findings
FROM diagnostic_findings df
JOIN patients p 
    ON df.patient_id = p.patient_id
GROUP BY p.condition, df.finding_type
ORDER BY p.condition, total_findings DESC;

-- Clinic workload score
SELECT
    c.clinic_name,
    COUNT(DISTINCT p.patient_id) AS total_patients,
    COUNT(DISTINCT d.device_id) AS total_devices,
    COUNT(DISTINCT a.alert_id) AS total_alerts,
    COUNT(DISTINCT ap.appointment_id) AS total_appointments,
    (
        COUNT(DISTINCT p.patient_id)
        + COUNT(DISTINCT d.device_id) * 2
        + COUNT(DISTINCT a.alert_id) * 3
        + COUNT(DISTINCT ap.appointment_id)
    ) AS workload_score
FROM clinics c
LEFT JOIN patients p 
    ON c.clinic_id = p.clinic_id
LEFT JOIN devices d 
    ON p.patient_id = d.patient_id
LEFT JOIN alerts a 
    ON p.patient_id = a.patient_id
LEFT JOIN appointments ap 
    ON c.clinic_id = ap.clinic_id
GROUP BY c.clinic_name
ORDER BY workload_score DESC;

-- Monthly alert trend by severity
SELECT
    DATE_TRUNC('month', alert_date)::DATE AS month,
    severity,
    COUNT(*) AS total_alerts
FROM alerts
GROUP BY DATE_TRUNC('month', alert_date), severity
ORDER BY month, severity;

-- Data quality checks
-- Missing patient references in devices
SELECT *
FROM devices d
LEFT JOIN patients p 
    ON d.patient_id = p.patient_id
WHERE p.patient_id IS NULL;

-- Transmissions with invalid battery level
SELECT *
FROM transmissions
WHERE battery_level < 0 
   OR battery_level > 100;

-- Alerts with resolved date before alert date
SELECT *
FROM alerts
WHERE resolved_date < alert_date;

-- Duplicate transmissions
SELECT
    transmission_id,
    COUNT(*)
FROM transmissions
GROUP BY transmission_id
HAVING COUNT(*) > 1;

-- Alerts missing severity or status
SELECT *
FROM alerts
WHERE severity IS NULL
   OR status IS NULL;