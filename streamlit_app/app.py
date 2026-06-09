import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from pathlib import Path


# ---------------------------------------------------------
# Page Config
# ---------------------------------------------------------
st.set_page_config(
    page_title="Cardiac Device Monitoring Analytics",
    page_icon="❤️",
    layout="wide"
)


# ---------------------------------------------------------
# Styling
# ---------------------------------------------------------
st.markdown(
    """
    <style>
    .main {
        background-color: #F8FAFC;
    }

    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
    }

    .metric-card {
        background-color: white;
        padding: 18px;
        border-radius: 14px;
        box-shadow: 0px 2px 8px rgba(0,0,0,0.08);
        border-left: 5px solid #0F766E;
    }

    .metric-label {
        font-size: 14px;
        color: #64748B;
        margin-bottom: 5px;
    }

    .metric-value {
        font-size: 26px;
        font-weight: 700;
        color: #0F172A;
    }
    
    h1, h2, h3, h4, h5, h6 {
        color: #F8FAFC !important;
    }

    p, label, span {
        color: #F8FAFC;
    }

    .section-title {
        font-size: 24px;
        font-weight: 700;
        color: #F8FAFC;
        margin-top: 20px;
        margin-bottom: 10px;
    }

    .insight-box {
        background-color: #ECFDF5;
        padding: 16px;
        border-radius: 12px;
        border-left: 5px solid #10B981;
        color: #064E3B;
        font-size: 15px;
    }

    .warning-box {
        background-color: #FEF2F2;
        padding: 16px;
        border-radius: 12px;
        border-left: 5px solid #EF4444;
        color: #7F1D1D;
        font-size: 15px;
    }
    </style>
    """,
    unsafe_allow_html=True
)


# ---------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------
@st.cache_data
def load_data():
    base_path = Path(__file__).resolve().parents[1] / "data" / "raw"

    patients = pd.read_csv(base_path / "patients.csv", parse_dates=["enrollment_date"])
    clinics = pd.read_csv(base_path / "clinics.csv")
    clinicians = pd.read_csv(base_path / "clinicians.csv")
    devices = pd.read_csv(base_path / "devices.csv", parse_dates=["implant_date"])
    transmissions = pd.read_csv(base_path / "transmissions.csv", parse_dates=["transmission_date"])
    alerts = pd.read_csv(base_path / "alerts.csv", parse_dates=["alert_date", "resolved_date"])
    findings = pd.read_csv(base_path / "diagnostic_findings.csv", parse_dates=["finding_date"])
    appointments = pd.read_csv(base_path / "appointments.csv", parse_dates=["appointment_date"])

    return patients, clinics, clinicians, devices, transmissions, alerts, findings, appointments


def metric_card(label, value):
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


def format_percentage(value):
    return f"{value:.2f}%"


def create_alert_summary(alerts, patients, clinics, devices):
    alert_summary = (
        alerts
        .merge(patients[["patient_id", "age", "gender", "condition", "clinic_id"]], on="patient_id", how="left")
        .merge(clinics[["clinic_id", "clinic_name", "state"]], on="clinic_id", how="left")
        .merge(devices[["device_id", "device_type", "manufacturer"]], on="device_id", how="left")
    )

    alert_summary["resolution_days"] = (
        alert_summary["resolved_date"] - alert_summary["alert_date"]
    ).dt.days

    alert_summary["month"] = alert_summary["alert_date"].dt.to_period("M").astype(str)

    return alert_summary


def create_transmission_summary(transmissions, patients, clinics, devices):
    transmission_summary = (
        transmissions
        .merge(patients[["patient_id", "age", "gender", "condition", "clinic_id"]], on="patient_id", how="left")
        .merge(clinics[["clinic_id", "clinic_name", "state"]], on="clinic_id", how="left")
        .merge(devices[["device_id", "device_type", "manufacturer"]], on="device_id", how="left")
    )

    transmission_summary["month"] = transmission_summary["transmission_date"].dt.to_period("M").astype(str)

    return transmission_summary


def create_device_risk_table(transmission_summary, alert_summary):
    transmission_metrics = transmission_summary.groupby(
        ["device_id", "patient_id", "device_type", "manufacturer", "clinic_name"],
        as_index=False
    ).agg(
        total_transmissions=("transmission_id", "count"),
        failed_or_missed_transmissions=("transmission_status", lambda x: x.isin(["Failed", "Missed"]).sum()),
        lowest_battery_level=("battery_level", "min"),
        average_battery_level=("battery_level", "mean")
    )

    alert_metrics = alert_summary.groupby("device_id", as_index=False).agg(
        total_alerts=("alert_id", "count"),
        critical_alerts=("severity", lambda x: (x == "Critical").sum()),
        open_alerts=("status", lambda x: (x == "Open").sum())
    )

    risk = transmission_metrics.merge(alert_metrics, on="device_id", how="left")
    risk[["total_alerts", "critical_alerts", "open_alerts"]] = risk[
        ["total_alerts", "critical_alerts", "open_alerts"]
    ].fillna(0)

    risk["device_risk_score"] = (
        risk["failed_or_missed_transmissions"] * 2
        + risk["critical_alerts"] * 5
        + risk["open_alerts"] * 3
        + np.where(risk["lowest_battery_level"] < 15, 10, 0)
    )

    risk["risk_level"] = pd.cut(
        risk["device_risk_score"],
        bins=[-1, 10, 25, 50, 999],
        labels=["Low", "Medium", "High", "Critical"]
    )

    return risk.sort_values("device_risk_score", ascending=False)


def download_button(df, filename, label):
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label=label,
        data=csv,
        file_name=filename,
        mime="text/csv"
    )


# ---------------------------------------------------------
# Load Data
# ---------------------------------------------------------
patients, clinics, clinicians, devices, transmissions, alerts, findings, appointments = load_data()

alert_summary = create_alert_summary(alerts, patients, clinics, devices)
transmission_summary = create_transmission_summary(transmissions, patients, clinics, devices)
device_risk = create_device_risk_table(transmission_summary, alert_summary)


# ---------------------------------------------------------
# Header
# ---------------------------------------------------------
st.title("❤️ Cardiac Device Remote Monitoring Analytics")
st.caption(
    "Interactive healthcare SaaS analytics dashboard for monitoring transmissions, alerts, device risk, and clinic workload."
)


# ---------------------------------------------------------
# Sidebar Filters
# ---------------------------------------------------------
st.sidebar.title("Dashboard Filters")

states = sorted(alert_summary["state"].dropna().unique())
selected_states = st.sidebar.multiselect("State", states, default=states)

clinics_list = sorted(alert_summary[alert_summary["state"].isin(selected_states)]["clinic_name"].dropna().unique())
selected_clinics = st.sidebar.multiselect("Clinic", clinics_list, default=clinics_list)

device_types = sorted(alert_summary["device_type"].dropna().unique())
selected_device_types = st.sidebar.multiselect("Device Type", device_types, default=device_types)

severity_list = sorted(alert_summary["severity"].dropna().unique())
selected_severity = st.sidebar.multiselect("Severity", severity_list, default=severity_list)

status_list = sorted(alert_summary["status"].dropna().unique())
selected_status = st.sidebar.multiselect("Alert Status", status_list, default=status_list)

min_date = alert_summary["alert_date"].min().date()
max_date = alert_summary["alert_date"].max().date()

selected_date_range = st.sidebar.date_input(
    "Alert Date Range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

if isinstance(selected_date_range, tuple) and len(selected_date_range) == 2:
    start_date, end_date = selected_date_range
else:
    start_date, end_date = min_date, max_date


# ---------------------------------------------------------
# Apply Filters
# ---------------------------------------------------------
filtered_alerts = alert_summary[
    (alert_summary["state"].isin(selected_states)) &
    (alert_summary["clinic_name"].isin(selected_clinics)) &
    (alert_summary["device_type"].isin(selected_device_types)) &
    (alert_summary["severity"].isin(selected_severity)) &
    (alert_summary["status"].isin(selected_status)) &
    (alert_summary["alert_date"].dt.date >= start_date) &
    (alert_summary["alert_date"].dt.date <= end_date)
]

filtered_transmissions = transmission_summary[
    (transmission_summary["state"].isin(selected_states)) &
    (transmission_summary["clinic_name"].isin(selected_clinics)) &
    (transmission_summary["device_type"].isin(selected_device_types))
]

filtered_device_risk = device_risk[
    (device_risk["clinic_name"].isin(selected_clinics)) &
    (device_risk["device_type"].isin(selected_device_types))
]


# ---------------------------------------------------------
# KPI Calculations
# ---------------------------------------------------------
total_patients = filtered_alerts["patient_id"].nunique()
total_devices = filtered_transmissions["device_id"].nunique()
total_transmissions = len(filtered_transmissions)
total_alerts = len(filtered_alerts)

open_alerts = filtered_alerts[filtered_alerts["status"] == "Open"].shape[0]
critical_alerts = filtered_alerts[filtered_alerts["severity"] == "Critical"].shape[0]

missed_transmissions = filtered_transmissions[
    filtered_transmissions["transmission_status"] == "Missed"
].shape[0]

missed_rate = (missed_transmissions / total_transmissions * 100) if total_transmissions > 0 else 0

avg_resolution_days = filtered_alerts["resolution_days"].mean()
avg_resolution_days = 0 if pd.isna(avg_resolution_days) else avg_resolution_days

low_battery_devices = filtered_transmissions[
    filtered_transmissions["battery_level"] < 15
]["device_id"].nunique()


# ---------------------------------------------------------
# KPI Cards
# ---------------------------------------------------------
st.markdown('<div class="section-title">Executive Overview</div>', unsafe_allow_html=True)

kpi1, kpi2, kpi3, kpi4 = st.columns(4)
with kpi1:
    metric_card("Total Patients", f"{total_patients:,}")
with kpi2:
    metric_card("Total Devices", f"{total_devices:,}")
with kpi3:
    metric_card("Total Transmissions", f"{total_transmissions:,}")
with kpi4:
    metric_card("Total Alerts", f"{total_alerts:,}")

kpi5, kpi6, kpi7, kpi8 = st.columns(4)
with kpi5:
    metric_card("Open Alerts", f"{open_alerts:,}")
with kpi6:
    metric_card("Critical Alerts", f"{critical_alerts:,}")
with kpi7:
    metric_card("Missed Transmission Rate", format_percentage(missed_rate))
with kpi8:
    metric_card("Avg Resolution Days", f"{avg_resolution_days:.2f}")


# ---------------------------------------------------------
# Executive Summary
# ---------------------------------------------------------
st.markdown('<div class="section-title">Auto-Generated Executive Summary</div>', unsafe_allow_html=True)

highest_risk_device = filtered_device_risk.iloc[0] if len(filtered_device_risk) > 0 else None

if highest_risk_device is not None:
    summary_text = f"""
    The filtered dataset contains <b>{total_alerts:,} alerts</b> across <b>{total_devices:,} devices</b> and <b>{total_patients:,} patients</b>.
    There are currently <b>{open_alerts:,} open alerts</b> and <b>{critical_alerts:,} critical alerts</b>.
    The missed transmission rate is <b>{missed_rate:.2f}%</b>, while the average alert resolution time is <b>{avg_resolution_days:.2f} days</b>.
    The highest-risk device is <b>{highest_risk_device['device_id']}</b>, with a risk score of <b>{highest_risk_device['device_risk_score']}</b>.
    """
else:
    summary_text = "No data available for the selected filters."

st.markdown(f'<div class="insight-box">{summary_text}</div>', unsafe_allow_html=True)


# ---------------------------------------------------------
# Tabs
# ---------------------------------------------------------
tab1, tab2, tab3, tab4, tab5 = st.tabs(
    [
        "📈 Trends",
        "🚨 Alert Management",
        "🔋 Device Risk",
        "🏥 Clinic Operations",
        "⬇️ Export Data"
    ]
)


# ---------------------------------------------------------
# Tab 1: Trends
# ---------------------------------------------------------
with tab1:
    st.markdown("### Monthly Monitoring Trends")

    col1, col2 = st.columns(2)

    monthly_transmissions = filtered_transmissions.groupby(
        ["month", "transmission_status"],
        as_index=False
    ).agg(total_transmissions=("transmission_id", "count"))

    fig_transmissions = px.line(
        monthly_transmissions,
        x="month",
        y="total_transmissions",
        color="transmission_status",
        markers=True,
        title="Monthly Transmissions by Status"
    )

    col1.plotly_chart(fig_transmissions, use_container_width=True)

    monthly_alerts = filtered_alerts.groupby(
        ["month", "severity"],
        as_index=False
    ).agg(total_alerts=("alert_id", "count"))

    fig_alerts = px.line(
        monthly_alerts,
        x="month",
        y="total_alerts",
        color="severity",
        markers=True,
        title="Monthly Alerts by Severity"
    )

    col2.plotly_chart(fig_alerts, use_container_width=True)

    col3, col4 = st.columns(2)

    severity_counts = filtered_alerts.groupby("severity", as_index=False).agg(
        total_alerts=("alert_id", "count")
    )

    fig_severity = px.pie(
        severity_counts,
        names="severity",
        values="total_alerts",
        hole=0.45,
        title="Alert Distribution by Severity"
    )

    col3.plotly_chart(fig_severity, use_container_width=True)

    status_counts = filtered_alerts.groupby("status", as_index=False).agg(
        total_alerts=("alert_id", "count")
    )

    fig_status = px.bar(
        status_counts,
        x="status",
        y="total_alerts",
        title="Alerts by Status",
        text_auto=True
    )

    col4.plotly_chart(fig_status, use_container_width=True)


# ---------------------------------------------------------
# Tab 2: Alert Management
# ---------------------------------------------------------
with tab2:
    st.markdown("### Alert Management Command Center")

    alert_col1, alert_col2, alert_col3 = st.columns(3)

    escalated_alerts = filtered_alerts[filtered_alerts["status"] == "Escalated"].shape[0]
    resolved_24h = filtered_alerts[
        (filtered_alerts["resolution_days"].notna()) &
        (filtered_alerts["resolution_days"] <= 1)
    ].shape[0]
    resolved_24h_pct = (resolved_24h / total_alerts * 100) if total_alerts > 0 else 0

    with alert_col1:
        metric_card("Escalated Alerts", f"{escalated_alerts:,}")
    with alert_col2:
        metric_card("Resolved Within 24H", format_percentage(resolved_24h_pct))
    with alert_col3:
        metric_card("Critical Open Alerts", f"{filtered_alerts[(filtered_alerts['severity'] == 'Critical') & (filtered_alerts['status'] == 'Open')].shape[0]:,}")

    col1, col2 = st.columns(2)

    open_by_clinic = (
        filtered_alerts[filtered_alerts["status"] == "Open"]
        .groupby("clinic_name", as_index=False)
        .agg(open_alerts=("alert_id", "count"))
        .sort_values("open_alerts", ascending=False)
        .head(10)
    )

    fig_open_clinic = px.bar(
        open_by_clinic,
        x="open_alerts",
        y="clinic_name",
        orientation="h",
        title="Top Clinics by Open Alerts",
        text_auto=True
    )

    fig_open_clinic.update_layout(yaxis={"categoryorder": "total ascending"})
    col1.plotly_chart(fig_open_clinic, use_container_width=True)

    alert_type_counts = filtered_alerts.groupby("alert_type", as_index=False).agg(
        total_alerts=("alert_id", "count")
    ).sort_values("total_alerts", ascending=False)

    fig_alert_type = px.bar(
        alert_type_counts,
        x="total_alerts",
        y="alert_type",
        orientation="h",
        title="Alerts by Type",
        text_auto=True
    )

    fig_alert_type.update_layout(yaxis={"categoryorder": "total ascending"})
    col2.plotly_chart(fig_alert_type, use_container_width=True)

    st.markdown("### Critical / Escalated Alert Worklist")

    critical_worklist = filtered_alerts[
        (filtered_alerts["severity"].isin(["Critical", "High"])) &
        (filtered_alerts["status"].isin(["Open", "Escalated"]))
    ][
        [
            "alert_id",
            "alert_date",
            "clinic_name",
            "patient_id",
            "device_id",
            "device_type",
            "alert_type",
            "severity",
            "status"
        ]
    ].sort_values(["severity", "alert_date"], ascending=[True, False])

    st.dataframe(critical_worklist, use_container_width=True, height=350)


# ---------------------------------------------------------
# Tab 3: Device Risk
# ---------------------------------------------------------
with tab3:
    st.markdown("### Device Risk Scoring")

    risk_col1, risk_col2, risk_col3 = st.columns(3)

    critical_risk_devices = filtered_device_risk[
        filtered_device_risk["risk_level"] == "Critical"
    ].shape[0]

    high_risk_devices = filtered_device_risk[
        filtered_device_risk["risk_level"] == "High"
    ].shape[0]

    with risk_col1:
        metric_card("Low Battery Devices", f"{low_battery_devices:,}")
    with risk_col2:
        metric_card("High Risk Devices", f"{high_risk_devices:,}")
    with risk_col3:
        metric_card("Critical Risk Devices", f"{critical_risk_devices:,}")

    col1, col2 = st.columns(2)

    risk_counts = filtered_device_risk.groupby("risk_level", as_index=False).agg(
        total_devices=("device_id", "count")
    )

    fig_risk = px.bar(
        risk_counts,
        x="risk_level",
        y="total_devices",
        title="Devices by Risk Level",
        text_auto=True
    )

    col1.plotly_chart(fig_risk, use_container_width=True)

    battery_by_type = filtered_transmissions.groupby("device_type", as_index=False).agg(
        avg_battery=("battery_level", "mean")
    )

    fig_battery = px.bar(
        battery_by_type,
        x="device_type",
        y="avg_battery",
        title="Average Battery Level by Device Type",
        text_auto=".2f"
    )

    col2.plotly_chart(fig_battery, use_container_width=True)

    st.markdown("### Top Device Risk Table")

    st.dataframe(
        filtered_device_risk[
            [
                "device_id",
                "patient_id",
                "clinic_name",
                "device_type",
                "manufacturer",
                "total_transmissions",
                "failed_or_missed_transmissions",
                "lowest_battery_level",
                "total_alerts",
                "critical_alerts",
                "open_alerts",
                "device_risk_score",
                "risk_level"
            ]
        ].head(50),
        use_container_width=True,
        height=400
    )


# ---------------------------------------------------------
# Tab 4: Clinic Operations
# ---------------------------------------------------------
with tab4:
    st.markdown("### Clinic Operations and Workload")

    clinic_base = patients.merge(
        clinics[["clinic_id", "clinic_name", "state"]],
        on="clinic_id",
        how="left",
        suffixes=("_patient", "_clinic")
    )

    # After merge, clinic state may appear as state_clinic
    if "state_clinic" in clinic_base.columns:
        clinic_base = clinic_base.rename(columns={"state_clinic": "clinic_state"})
    elif "state" in clinic_base.columns:
        clinic_base = clinic_base.rename(columns={"state": "clinic_state"})
    else:
        clinic_base["clinic_state"] = "Unknown"

    clinic_workload = (
        clinic_base
        .groupby(["clinic_id", "clinic_name", "clinic_state"], as_index=False)
        .agg(total_patients=("patient_id", "nunique"))
    )

    clinic_alerts = alert_summary.groupby("clinic_id", as_index=False).agg(
        total_alerts=("alert_id", "count"),
        open_alerts=("status", lambda x: (x == "Open").sum())
    )

    clinic_appointments = appointments.groupby("clinic_id", as_index=False).agg(
        total_appointments=("appointment_id", "count")
    )

    clinic_clinicians = clinicians.groupby("clinic_id", as_index=False).agg(
        total_clinicians=("clinician_id", "count")
    )

    clinic_workload = (
        clinic_workload
        .merge(clinic_alerts, on="clinic_id", how="left")
        .merge(clinic_appointments, on="clinic_id", how="left")
        .merge(clinic_clinicians, on="clinic_id", how="left")
        .fillna(0)
    )

    clinic_workload = clinic_workload[
        clinic_workload["clinic_name"].isin(selected_clinics)
    ]

    clinic_workload["alerts_per_clinician"] = (
        clinic_workload["total_alerts"] / clinic_workload["total_clinicians"].replace(0, np.nan)
    ).fillna(0)

    clinic_workload["workload_score"] = (
        clinic_workload["total_patients"]
        + clinic_workload["total_alerts"] * 3
        + clinic_workload["total_appointments"]
        + clinic_workload["alerts_per_clinician"] * 5
    )

    col1, col2 = st.columns(2)

    top_workload = clinic_workload.sort_values("workload_score", ascending=False).head(10)

    fig_workload = px.bar(
        top_workload,
        x="workload_score",
        y="clinic_name",
        orientation="h",
        title="Top Clinics by Workload Score",
        text_auto=".2f"
    )

    fig_workload.update_layout(yaxis={"categoryorder": "total ascending"})
    col1.plotly_chart(fig_workload, use_container_width=True)

    fig_alerts_clinician = px.bar(
        top_workload,
        x="alerts_per_clinician",
        y="clinic_name",
        orientation="h",
        title="Alerts per Clinician",
        text_auto=".2f"
    )

    fig_alerts_clinician.update_layout(yaxis={"categoryorder": "total ascending"})
    col2.plotly_chart(fig_alerts_clinician, use_container_width=True)

    st.markdown("### Clinic Workload Summary")

    st.dataframe(
        clinic_workload[
            [
                "clinic_name",
                "clinic_state",
                "total_patients",
                "total_alerts",
                "open_alerts",
                "total_appointments",
                "total_clinicians",
                "alerts_per_clinician",
                "workload_score"
            ]
        ].sort_values("workload_score", ascending=False),
        use_container_width=True,
        height=400
    )


# ---------------------------------------------------------
# Tab 5: Export Data
# ---------------------------------------------------------
with tab5:
    st.markdown("### Export Filtered Data")

    st.write("Download filtered datasets for stakeholder reporting or additional analysis.")

    col1, col2, col3 = st.columns(3)

    with col1:
        download_button(filtered_alerts, "filtered_alerts.csv", "Download Filtered Alerts")

    with col2:
        download_button(filtered_transmissions, "filtered_transmissions.csv", "Download Filtered Transmissions")

    with col3:
        download_button(filtered_device_risk, "device_risk_scores.csv", "Download Device Risk Scores")

    st.markdown("### Filtered Alert Data Preview")
    st.dataframe(filtered_alerts.head(100), use_container_width=True, height=350)