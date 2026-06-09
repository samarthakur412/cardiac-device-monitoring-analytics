DROP TABLE IF EXISTS appointments;
DROP TABLE IF EXISTS diagnostic_findings;
DROP TABLE IF EXISTS alerts;
DROP TABLE IF EXISTS transmissions;
DROP TABLE IF EXISTS devices;
DROP TABLE IF EXISTS patients;
DROP TABLE IF EXISTS clinicians;
DROP TABLE IF EXISTS clinics;

CREATE TABLE clinics (
    clinic_id VARCHAR(10) PRIMARY KEY,
    clinic_name VARCHAR(100),
    state VARCHAR(10),
    number_of_clinicians INT
);

CREATE TABLE clinicians (
    clinician_id VARCHAR(10) PRIMARY KEY,
    clinician_name VARCHAR(100),
    clinic_id VARCHAR(10),
    role VARCHAR(50),
    FOREIGN KEY (clinic_id) REFERENCES clinics(clinic_id)
);

CREATE TABLE patients (
    patient_id VARCHAR(10) PRIMARY KEY,
    age INT,
    gender VARCHAR(20),
    city VARCHAR(100),
    state VARCHAR(10),
    condition VARCHAR(100),
    enrollment_date DATE,
    clinic_id VARCHAR(10),
    FOREIGN KEY (clinic_id) REFERENCES clinics(clinic_id)
);

CREATE TABLE devices (
    device_id VARCHAR(10) PRIMARY KEY,
    patient_id VARCHAR(10),
    device_type VARCHAR(50),
    manufacturer VARCHAR(50),
    implant_date DATE,
    device_status VARCHAR(20),
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
);

CREATE TABLE transmissions (
    transmission_id VARCHAR(10) PRIMARY KEY,
    device_id VARCHAR(10),
    patient_id VARCHAR(10),
    transmission_date DATE,
    transmission_status VARCHAR(30),
    battery_level NUMERIC(5,2),
    signal_quality VARCHAR(30),
    FOREIGN KEY (device_id) REFERENCES devices(device_id),
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
);

CREATE TABLE alerts (
    alert_id VARCHAR(10) PRIMARY KEY,
    transmission_id VARCHAR(10),
    patient_id VARCHAR(10),
    device_id VARCHAR(10),
    alert_date DATE,
    alert_type VARCHAR(100),
    severity VARCHAR(30),
    status VARCHAR(30),
    resolved_date DATE,
    FOREIGN KEY (transmission_id) REFERENCES transmissions(transmission_id),
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id),
    FOREIGN KEY (device_id) REFERENCES devices(device_id)
);

CREATE TABLE diagnostic_findings (
    finding_id VARCHAR(10) PRIMARY KEY,
    patient_id VARCHAR(10),
    device_id VARCHAR(10),
    finding_date DATE,
    finding_type VARCHAR(100),
    clinical_action VARCHAR(100),
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id),
    FOREIGN KEY (device_id) REFERENCES devices(device_id)
);

CREATE TABLE appointments (
    appointment_id VARCHAR(10) PRIMARY KEY,
    patient_id VARCHAR(10),
    clinic_id VARCHAR(10),
    clinician_id VARCHAR(10),
    appointment_date DATE,
    appointment_status VARCHAR(30),
    appointment_reason VARCHAR(100),
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id),
    FOREIGN KEY (clinic_id) REFERENCES clinics(clinic_id),
    FOREIGN KEY (clinician_id) REFERENCES clinicians(clinician_id)
);