CREATE OR REPLACE VIEW vw_alert_summary AS
SELECT
    a.alert_id,
    a.alert_date,
    a.alert_type,
    a.severity,
    a.status,
    a.resolved_date,
    CASE 
        WHEN a.resolved_date IS NOT NULL 
        THEN a.resolved_date - a.alert_date
        ELSE NULL
    END AS resolution_days,
    p.patient_id,
    p.age,
    p.gender,
    p.condition,
    c.clinic_id,
    c.clinic_name,
    c.state,
    d.device_id,
    d.device_type,
    d.manufacturer
FROM alerts a
JOIN patients p 
    ON a.patient_id = p.patient_id
JOIN clinics c 
    ON p.clinic_id = c.clinic_id
JOIN devices d 
    ON a.device_id = d.device_id;

CREATE OR REPLACE VIEW vw_transmission_summary AS
SELECT
    t.transmission_id,
    t.transmission_date,
    t.transmission_status,
    t.battery_level,
    t.signal_quality,
    p.patient_id,
    p.age,
    p.gender,
    p.condition,
    c.clinic_id,
    c.clinic_name,
    c.state,
    d.device_id,
    d.device_type,
    d.manufacturer
FROM transmissions t
JOIN patients p 
    ON t.patient_id = p.patient_id
JOIN clinics c 
    ON p.clinic_id = c.clinic_id
JOIN devices d 
    ON t.device_id = d.device_id;

CREATE OR REPLACE VIEW vw_clinic_workload AS
SELECT
    c.clinic_id,
    c.clinic_name,
    c.state,
    COUNT(DISTINCT p.patient_id) AS total_patients,
    COUNT(DISTINCT d.device_id) AS total_devices,
    COUNT(DISTINCT a.alert_id) AS total_alerts,
    COUNT(DISTINCT ap.appointment_id) AS total_appointments,
    COUNT(DISTINCT cl.clinician_id) AS total_clinicians,
    ROUND(
        COUNT(DISTINCT a.alert_id)::NUMERIC 
        / NULLIF(COUNT(DISTINCT cl.clinician_id), 0),
        2
    ) AS alerts_per_clinician
FROM clinics c
LEFT JOIN patients p 
    ON c.clinic_id = p.clinic_id
LEFT JOIN devices d 
    ON p.patient_id = d.patient_id
LEFT JOIN alerts a 
    ON p.patient_id = a.patient_id
LEFT JOIN appointments ap 
    ON c.clinic_id = ap.clinic_id
LEFT JOIN clinicians cl 
    ON c.clinic_id = cl.clinic_id
GROUP BY c.clinic_id, c.clinic_name, c.state;