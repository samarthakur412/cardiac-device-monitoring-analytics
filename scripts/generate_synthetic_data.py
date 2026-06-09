import pandas as pd
import numpy as np
from faker import Faker
import random
from datetime import datetime, timedelta
import os

fake = Faker()
random.seed(42)
np.random.seed(42)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DATA_DIR = os.path.join(BASE_DIR, "data", "raw")
os.makedirs(RAW_DATA_DIR, exist_ok=True)

NUM_PATIENTS = 500
NUM_CLINICS = 20
NUM_CLINICIANS = 80
NUM_DEVICES = 500
NUM_TRANSMISSIONS = 10000
NUM_ALERTS = 2000
NUM_FINDINGS = 1000
NUM_APPOINTMENTS = 1500

states = ["CA", "TX", "NY", "FL", "IL", "PA", "OH", "GA", "NC", "MI"]

conditions = [
    "Atrial Fibrillation",
    "Bradycardia",
    "Heart Failure",
    "Syncope",
    "Ventricular Tachycardia"
]

device_types = ["Pacemaker", "ICD", "CRT-D", "Loop Recorder"]

manufacturers = ["Medtronic", "Boston Scientific", "Abbott", "Biotronik"]

transmission_statuses = ["Received", "Missed", "Delayed", "Failed"]

alert_types = [
    "High Atrial Burden",
    "Possible AF Episode",
    "Low Battery",
    "Lead Impedance Issue",
    "Missed Transmission",
    "High Ventricular Rate"
]

severities = ["Low", "Medium", "High", "Critical"]

alert_statuses = ["Open", "Resolved", "Escalated"]

finding_types = [
    "Suspected AF",
    "No Significant Event",
    "Bradycardia Episode",
    "Tachycardia Episode",
    "Battery Replacement Needed"
]

clinical_actions = [
    "No Action Needed",
    "Schedule Follow-up",
    "Medication Review",
    "Device Check Required",
    "Urgent Clinical Review"
]

roles = ["Cardiologist", "Device Nurse", "Electrophysiologist", "Technician"]

appointment_statuses = ["Completed", "Scheduled", "Cancelled", "No Show"]


def random_date(start_date, end_date):
    delta = end_date - start_date
    random_days = random.randint(0, delta.days)
    return start_date + timedelta(days=random_days)


start_date = datetime(2024, 1, 1)
end_date = datetime(2026, 3, 31)


# -----------------------------
# Clinics
# -----------------------------
clinics = []

for i in range(1, NUM_CLINICS + 1):
    clinics.append({
        "clinic_id": f"C{i:03d}",
        "clinic_name": f"{fake.city()} Cardiac Care Center",
        "state": random.choice(states),
        "number_of_clinicians": random.randint(3, 10)
    })

clinics_df = pd.DataFrame(clinics)


# -----------------------------
# Clinicians
# -----------------------------
clinicians = []

for i in range(1, NUM_CLINICIANS + 1):
    clinic = random.choice(clinics)["clinic_id"]

    clinicians.append({
        "clinician_id": f"CL{i:03d}",
        "clinician_name": fake.name(),
        "clinic_id": clinic,
        "role": random.choice(roles)
    })

clinicians_df = pd.DataFrame(clinicians)


# -----------------------------
# Patients
# -----------------------------
patients = []

for i in range(1, NUM_PATIENTS + 1):
    clinic = random.choice(clinics)["clinic_id"]

    patients.append({
        "patient_id": f"P{i:04d}",
        "age": random.randint(35, 90),
        "gender": random.choice(["Male", "Female"]),
        "city": fake.city(),
        "state": random.choice(states),
        "condition": random.choice(conditions),
        "enrollment_date": random_date(start_date, end_date).date(),
        "clinic_id": clinic
    })

patients_df = pd.DataFrame(patients)


# -----------------------------
# Devices
# -----------------------------
devices = []

for i in range(1, NUM_DEVICES + 1):
    patient = patients_df.iloc[i - 1]
    implant_date = random_date(datetime(2018, 1, 1), datetime(2025, 12, 31)).date()

    devices.append({
        "device_id": f"D{i:04d}",
        "patient_id": patient["patient_id"],
        "device_type": random.choice(device_types),
        "manufacturer": random.choice(manufacturers),
        "implant_date": implant_date,
        "device_status": random.choice(["Active", "Active", "Active", "Inactive"])
    })

devices_df = pd.DataFrame(devices)


# -----------------------------
# Transmissions
# -----------------------------
transmissions = []

for i in range(1, NUM_TRANSMISSIONS + 1):
    device = devices_df.sample(1).iloc[0]
    transmission_date = random_date(start_date, end_date)

    status = random.choices(
        transmission_statuses,
        weights=[75, 10, 10, 5],
        k=1
    )[0]

    transmissions.append({
        "transmission_id": f"T{i:05d}",
        "device_id": device["device_id"],
        "patient_id": device["patient_id"],
        "transmission_date": transmission_date.date(),
        "transmission_status": status,
        "battery_level": round(random.uniform(5, 100), 2),
        "signal_quality": random.choice(["Good", "Moderate", "Poor"])
    })

transmissions_df = pd.DataFrame(transmissions)


# -----------------------------
# Alerts
# -----------------------------
alerts = []

for i in range(1, NUM_ALERTS + 1):
    transmission = transmissions_df.sample(1).iloc[0]

    alert_date = pd.to_datetime(transmission["transmission_date"])
    status = random.choices(
        alert_statuses,
        weights=[25, 65, 10],
        k=1
    )[0]

    if status == "Resolved":
        resolved_date = alert_date + timedelta(hours=random.randint(2, 96))
    elif status == "Escalated":
        resolved_date = alert_date + timedelta(hours=random.randint(24, 120))
    else:
        resolved_date = None

    alerts.append({
        "alert_id": f"A{i:05d}",
        "transmission_id": transmission["transmission_id"],
        "patient_id": transmission["patient_id"],
        "device_id": transmission["device_id"],
        "alert_date": alert_date.date(),
        "alert_type": random.choice(alert_types),
        "severity": random.choices(
            severities,
            weights=[35, 35, 20, 10],
            k=1
        )[0],
        "status": status,
        "resolved_date": resolved_date.date() if resolved_date else None
    })

alerts_df = pd.DataFrame(alerts)


# -----------------------------
# Diagnostic Findings
# -----------------------------
findings = []

for i in range(1, NUM_FINDINGS + 1):
    device = devices_df.sample(1).iloc[0]

    findings.append({
        "finding_id": f"F{i:05d}",
        "patient_id": device["patient_id"],
        "device_id": device["device_id"],
        "finding_date": random_date(start_date, end_date).date(),
        "finding_type": random.choice(finding_types),
        "clinical_action": random.choice(clinical_actions)
    })

findings_df = pd.DataFrame(findings)


# -----------------------------
# Appointments
# -----------------------------
appointments = []

for i in range(1, NUM_APPOINTMENTS + 1):
    patient = patients_df.sample(1).iloc[0]
    clinic_id = patient["clinic_id"]

    clinic_clinicians = clinicians_df[clinicians_df["clinic_id"] == clinic_id]

    if len(clinic_clinicians) > 0:
        clinician = clinic_clinicians.sample(1).iloc[0]["clinician_id"]
    else:
        clinician = clinicians_df.sample(1).iloc[0]["clinician_id"]

    appointments.append({
        "appointment_id": f"AP{i:05d}",
        "patient_id": patient["patient_id"],
        "clinic_id": clinic_id,
        "clinician_id": clinician,
        "appointment_date": random_date(start_date, end_date).date(),
        "appointment_status": random.choice(appointment_statuses),
        "appointment_reason": random.choice([
            "Routine Follow-up",
            "Alert Follow-up",
            "Device Check",
            "Battery Review",
            "Symptom Review"
        ])
    })

appointments_df = pd.DataFrame(appointments)


# -----------------------------
# Save CSV files
# -----------------------------
clinics_df.to_csv(os.path.join(RAW_DATA_DIR, "clinics.csv"), index=False)
clinicians_df.to_csv(os.path.join(RAW_DATA_DIR, "clinicians.csv"), index=False)
patients_df.to_csv(os.path.join(RAW_DATA_DIR, "patients.csv"), index=False)
devices_df.to_csv(os.path.join(RAW_DATA_DIR, "devices.csv"), index=False)
transmissions_df.to_csv(os.path.join(RAW_DATA_DIR, "transmissions.csv"), index=False)
alerts_df.to_csv(os.path.join(RAW_DATA_DIR, "alerts.csv"), index=False)
findings_df.to_csv(os.path.join(RAW_DATA_DIR, "diagnostic_findings.csv"), index=False)
appointments_df.to_csv(os.path.join(RAW_DATA_DIR, "appointments.csv"), index=False)

print("Synthetic cardiac device monitoring dataset created successfully.")
print(f"Files saved in: {RAW_DATA_DIR}")

print("\nDataset Summary:")
print(f"Clinics: {len(clinics_df)}")
print(f"Clinicians: {len(clinicians_df)}")
print(f"Patients: {len(patients_df)}")
print(f"Devices: {len(devices_df)}")
print(f"Transmissions: {len(transmissions_df)}")
print(f"Alerts: {len(alerts_df)}")
print(f"Diagnostic Findings: {len(findings_df)}")
print(f"Appointments: {len(appointments_df)}")