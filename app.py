
import streamlit as st
import pandas as pd
from datetime import datetime
from services.attendance_service import process_attendance_event
from datetime import date
from services.attendance_service import get_daily_summary

from database.employee_service import (
    add_employee,
    get_employees,
    get_employee_count,
)

from services.attendance_service import (
    get_attendance_events,
    get_attendance_sessions,
)

st.set_page_config(
    page_title="AI Employee Attendance",
    page_icon="👤",
    layout="wide",
)

st.title("AI Employee Recognition & Attendance")
st.caption("Contactless employee access and attendance management")

# Dashboard metrics
try:
    employee_count = get_employee_count()
    employees = get_employees()

    col1, col2, col3 = st.columns(3)

    col1.metric("Active Employees", employee_count)
    col2.metric("Present Today", 0)
    col3.metric("Attendance Events Today", 0)

except Exception as error:
    st.error(f"Could not load employee data: {error}")
    st.stop()

st.divider()

# Employee registration
st.subheader("Register New Employee")

with st.form("employee_registration"):
    employee_code = st.text_input(
        "Employee Code",
        placeholder="Example: EMP001",
    )

    full_name = st.text_input(
        "Full Name",
        placeholder="Enter employee name",
    )

    department = st.text_input(
        "Department",
        placeholder="Example: IT",
    )

    submitted = st.form_submit_button("Register Employee")

    if submitted:
        if not employee_code.strip() or not full_name.strip():
            st.warning("Employee code and full name are required.")

        else:
            success, message = add_employee(
                employee_code.strip(),
                full_name.strip(),
                department.strip(),
            )

            if success:
                st.success(message)
                st.rerun()
            else:
                st.error(message)

st.divider()

# Employee list
st.subheader("Registered Employees")

if employees:
    employee_df = pd.DataFrame(employees)

    st.dataframe(
        employee_df,
        use_container_width=True,
        hide_index=True,
    )
else:
    st.info("No employees registered yet. Add your first employee above.")

st.caption("Face recognition and attendance processing will be integrated next.")


st.divider()

st.subheader("Attendance Event Simulator")

st.caption(
    "Testing only: simulate entrance and departure events. "
    "No physical door or camera is connected."
)

if employees:
    selected_employee = st.selectbox(
        "Select Employee",
        employees,
        format_func=lambda emp: (
            f"{emp['employee_code']} - {emp['full_name']}"
        ),
        key="attendance_employee",
    )

    event_type = st.radio(
        "Event",
        ["ENTRY", "EXIT"],
        horizontal=True,
    )

    has_bag = st.checkbox(
        "Employee is carrying a bag",
        value=True,
    )

    event_time = st.datetime_input(
        "Simulated event date and time",
        value=datetime.now(),
    )

    if st.button("Process Attendance Event"):
        success, message = process_attendance_event(
            employee_id=selected_employee["employee_id"],
            event_type=event_type,
            has_bag=has_bag,
            event_time=event_time,
        )

        if success:
            st.success(message)
        else:
            st.warning(message)

else:
    st.info("Register an employee before simulating attendance.")

st.header("Attendance Records")

events = get_attendance_events()
sessions = get_attendance_sessions()

st.subheader("Recent Events")

if events:
    st.dataframe(events, use_container_width=True)
else:
    st.info("No attendance events recorded yet.")

st.subheader("Attendance Sessions")

if sessions:
    st.dataframe(sessions, use_container_width=True)
else:
    st.info("No attendance sessions recorded yet.")

st.header("Daily Attendance Summary")

selected_date = st.date_input(
    "Select attendance date",
    value=date.today()
)

summary = get_daily_summary(selected_date)

col1, col2, col3, col4 = st.columns(4)

col1.metric("Entries", summary["entries_today"])
col2.metric("Employees Entered", summary["employees_entered"])
col3.metric("Open Sessions", summary["open_sessions"])
col4.metric("Completed Today", summary["completed_today"])


