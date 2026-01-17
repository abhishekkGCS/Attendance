"""
Galactic Client Services
Employee Attendance Dashboard

Main entry point for the Streamlit application.
"""
import streamlit as st
from datetime import date, datetime, timedelta
import os

# Configure page
st.set_page_config(
    page_title="Galactic Client Services",
    page_icon="assets/logo.png",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Import after page config
from config import config
from services.session import init_session, is_authenticated, get_user, clear_session
from services.api_client import api_client, APIError
from components.auth_forms import render_login_form
from components.calendar_view import render_calendar, render_legend, render_month_selector, render_mini_dashboard_calendar


# Custom CSS
st.markdown("""
<style>
/* Global spacing and scrollbar */
.main .block-container {
    max-width: 100%;
    padding-top: 1rem;
    padding-bottom: 2rem;
    overflow-x: hidden;
}

/* Hide horizontal scrollbar globally */
::-webkit-scrollbar {
    width: 6px;
    height: 0px !important; /* Hide horizontal */
}

/* Force hide excess width */
div[data-testid="stAppViewContainer"] {
    overflow-x: hidden !important;
}

div[data-testid="stSidebar"] {
    overflow-x: hidden !important;
}

/* Header */
.app-header {
    background: linear-gradient(135deg, #1976D2 0%, #2196F3 100%);
    color: white;
    padding: 1.2rem 2rem;
    border-radius: 14px;
    margin-bottom: 1.5rem;
    box-shadow: 0 4px 20px rgba(33, 150, 243, 0.25);
}
.app-header h1 { margin: 0; font-size: 1.7rem; }
.app-header p { margin-top: .3rem; opacity: .9; }

/* Sidebar alignment */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #f8f9fa 0%, #ffffff 100%);
}
.sidebar-logo {
    text-align: center;
    margin-bottom: 1rem;
}
.sidebar-logo img {
    max-width: 110px;
}

/* Tables */
.week-table {
    width: 100%;
    border-collapse: collapse;
    margin: 1rem 0 2rem 0;
}
.week-table th, .week-table td {
    padding: 10px 12px;
    text-align: center;
}

/* Metrics */
.metric-box {
    text-align: center;
}

/* Buttons */
.stButton > button {
    width: 100%;
    border-radius: 10px;
    padding: .55rem 1rem;
    font-weight: 500;
}

/* Forms */
.stForm {
    padding-top: .5rem;
}

/* Cards */
.card {
    background: white;
    border-radius: 14px;
    padding: 1.2rem;
    box-shadow: 0 4px 20px rgba(0,0,0,0.08);
    margin-bottom: 1rem;
}
</style>
""", unsafe_allow_html=True)



def main():
    """Main application entry point."""
    
    # Initialize session
    init_session()
    
    if not is_authenticated():
        # Show login page
        render_login_form()
    else:
        # Show main dashboard
        render_dashboard()


def render_dashboard():
    """Render the main dashboard after login."""
    
    user = get_user()
    
    # Sidebar
    with st.sidebar:
        # Logo
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.image("assets/logo.png", use_container_width=True)
            
        st.markdown("""
    <div class="sidebar-logo">
    <h4>Galactic Client Services</h4>
    </div>
    """, unsafe_allow_html=True)

        st.divider()
        
        # User info
        st.markdown(f"**{user.get('full_name', 'User')}**")
        st.caption(f"{user.get('email', '')}")
        st.caption(f"{user.get('employee_code', '')} | {user.get('role', '').title()}")
        
        st.divider()
        
        # Simplified navigation
        page = st.radio(
            "Navigation",
            options=[
                "My Dashboard",
                "Raise Issue",
            ],
            label_visibility="collapsed",
        )
        
        st.divider()
        
        if st.button("Logout", use_container_width=True):
            try:
                api_client.logout()
            except:
                pass
            clear_session()
            st.rerun()
    
    # Main content
    if page == "My Dashboard":
        render_employee_dashboard()
    elif page == "Raise Issue":
        render_raise_issue()


def get_week_dates():
    """Get current week dates (Monday to Sunday)."""
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    return [monday + timedelta(days=i) for i in range(7)]


def get_status_class(code):
    """Get CSS class for attendance status."""
    if code in ["P", "WFH"]:
        return "status-present" if code == "P" else "status-wfh"
    elif code in ["AB", "NCNS", "ABSCOND"]:
        return "status-absent"
    elif code in ["UNSCHD", "HALF DAY", "CO"]:
        return "status-leave"
    elif code == "OFF":
        return "status-off"
    else:
        return "status-pending"


def get_status_label(code):
    """Get display label for attendance status."""
    labels = {
        "P": "Present",
        "AB": "Absent",
        "WFH": "WFH",
        "OFF": "Off",
        "UNSCHD": "Leave",
        "HALF DAY": "Half Day",
        "CO": "Comp Off",
        "NCNS": "NCNS",
        None: "—",
    }
    return labels.get(code, code or "—")


def render_employee_dashboard():
    """Render employee dashboard with weekly attendance view."""
    
    user = get_user()
    
    # Header
    st.markdown(f"""
    <div class="app-header">
        <h1>Welcome, {user.get('full_name', 'User')}!</h1>
        <p>Your attendance dashboard</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Get current week dates
    week_dates = get_week_dates()
    today = date.today()
    
    # Fetch attendance data for current month
    try:
        attendance_data = api_client.get_my_attendance(today.year, today.month)
    except APIError as e:
        st.error(f"Failed to load attendance: {e.message}")
        return
    except Exception as e:
        st.error(f"Connection error. Please check if backend is running.")
        return
    
    # Build day lookup
    days_lookup = {}
    for day in attendance_data.get("days", []):
        day_date = day.get("date")
        if isinstance(day_date, str):
            days_lookup[day_date] = day
    
    # Weekly Summary Section
    st.markdown("### This Week's Attendance")
    
    # Build week table HTML
    week_html = '<table class="week-table"><thead><tr>'
    for d in week_dates:
        is_today = d == today
        day_style = "font-weight: bold; color: #2196F3;" if is_today else ""
        week_html += f'<th style="{day_style}">{d.strftime("%a")}<br>{d.strftime("%d %b")}</th>'
    week_html += '</tr></thead><tbody><tr>'
    
    for d in week_dates:
        day_data = days_lookup.get(d.isoformat(), {})
        code = day_data.get("code")
        status_class = get_status_class(code)
        status_label = get_status_label(code)
        
        if d > today:
            week_html += '<td><span style="color: #ccc;">—</span></td>'
        else:
            week_html += f'<td><span class="{status_class}">{status_label}</span></td>'
    
    week_html += '</tr></tbody></table>'
    
    st.markdown(week_html, unsafe_allow_html=True)
    
    # Quick Stats
    st.markdown("### Monthly Summary")
    
    summary = attendance_data.get("summary", {})
    #col1, col2, col3, col4 = st.columns(4)
    
    col1, col2, col3, col4 = st.columns([1,1,1,1], gap="large")

    with col1:
        st.markdown('<div class="metric-box">', unsafe_allow_html=True)
        st.metric("Present", summary.get("P", 0))
        st.markdown('</div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="metric-box">', unsafe_allow_html=True)
        st.metric("Absent", summary.get("AB", 0))
        st.markdown('</div>', unsafe_allow_html=True)
    with col3:
        st.markdown('<div class="metric-box">', unsafe_allow_html=True)
        st.metric("WFH", summary.get("WFH", 0))
        st.markdown('</div>', unsafe_allow_html=True)
    with col4:
        st.markdown('<div class="metric-box">', unsafe_allow_html=True)
        st.metric("Off Days", summary.get("OFF", 0))
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.divider()
    
    # Calendar View
    st.markdown("### 🗓️ Attendance Calendar")
    
    # Initialize state for calendar navigation if not set
    if "calendar_date" not in st.session_state:
        st.session_state.calendar_date = date.today()
        
    cal_date = st.session_state.calendar_date
    
    # Fetch data if different from current dashboard view year/month
    # (Dashboard view loads `attendance_data` for `today` above)
    # If the user navigates the calendar, we need to fetch that month's data.
    
    cal_attendance = attendance_data
    if cal_date.year != today.year or cal_date.month != today.month:
        try:
            cal_attendance = api_client.get_my_attendance(cal_date.year, cal_date.month)
        except Exception:
            cal_attendance = {"days": [], "summary": {}}

    render_calendar(cal_attendance, cal_date.year, cal_date.month)
    
    st.divider()
    render_legend()


def render_mark_attendance():
    """Render attendance marking form."""
    
    st.markdown("""
    <div class="app-header">
        <h1>Mark Attendance</h1>
        <p>Submit your attendance for today</p>
    </div>
    """, unsafe_allow_html=True)
    
    today = date.today()
    
    st.info(f"Today's Date: **{today.strftime('%A, %B %d, %Y')}**")
    
    # Simplified attendance codes
    codes = [
        ("P", "Present"),
        ("WFH", "Work From Home"),
        ("AB", "Absent"),
        ("HALF DAY", "Half Day"),
        ("OFF", "Weekly Off"),
    ]
    
    with st.form("attendance_form"):
        selected_code = st.selectbox(
            "Attendance Status",
            options=[c[0] for c in codes],
            format_func=lambda x: next(c[1] for c in codes if c[0] == x),
        )
        
        reason = st.text_area(
            "Reason/Notes (optional)",
            placeholder="Add any notes...",
            max_chars=500,
        )
        
        login_hours = None
        if selected_code == "HALF DAY":
            login_hours = st.number_input(
                "Login Hours",
                min_value=0.0,
                max_value=24.0,
                value=7.0,
                step=0.5,
            )
        
        submitted = st.form_submit_button("Submit Attendance", use_container_width=True, type="primary")
        
        if submitted:
            with st.spinner("Submitting..."):
                try:
                    result = api_client.submit_attendance_request(
                        today.isoformat(),
                        selected_code,
                        reason,
                        login_hours,
                    )
                    st.success("Attendance submitted successfully!")
                except APIError as e:
                    st.error(f"Failed to submit: {e.message}")
                except Exception as e:
                    st.error(f"Connection error: {str(e)}")


def render_raise_issue():
    """Render issue raising form."""
    
    st.markdown("""
    <div class="app-header">
        <h1>Raise an Issue</h1>
        <p>Report attendance-related problems</p>
    </div>
    """, unsafe_allow_html=True)
    
    user = get_user()
    
    #col1, col2 = st.columns(2)
    st.markdown('<div class="card">', unsafe_allow_html=True)
    col1, col2 = st.columns([5,5], gap="large")
    st.markdown('</div>', unsafe_allow_html=True)
    
    with col1:
        st.markdown("### Email HR")
        st.markdown("Open your email client with pre-filled template.")
        
        related_date = st.date_input("Related Date (optional)", value=None)
        
        # Generate mailto link
        import urllib.parse
        subject = f"Attendance Issue – {user.get('employee_code', '')}"
        date_str = related_date.strftime('%Y-%m-%d') if related_date else "N/A"
        body = f"""Dear HR Team,

I am writing to report an attendance issue.

Employee Details:
- Name: {user.get('full_name', '')}
- Employee Code: {user.get('employee_code', '')}
- Related Date: {date_str}

Issue Description:
[Please describe your issue here]

Thank you,
{user.get('full_name', '')}"""
        
        mailto = f"mailto:hr@galactic-services.com?subject={urllib.parse.quote(subject)}&body={urllib.parse.quote(body)}"
        
        # Use HTML link styled as button
        st.markdown(f'''
        <a href="{mailto}" style="
            display: inline-block;
            width: 100%;
            padding: 0.5rem 1rem;
            background: linear-gradient(135deg, #1976D2 0%, #2196F3 100%);
            color: white;
            text-align: center;
            text-decoration: none;
            border-radius: 10px;
            font-weight: 500;
            margin-top: 1rem;
        ">Open Email Client</a>
        ''', unsafe_allow_html=True)
    
    with col2:
        st.markdown("### Log Issue in System")
        
        with st.form("issue_form"):
            issue_date = st.date_input("Related Date", value=date.today())
            description = st.text_area(
                "Issue Description",
                placeholder="Describe your issue...",
            )
            
            if st.form_submit_button("Submit Issue", use_container_width=True, type="primary"):
                if len(description) < 10:
                    st.error("Please provide more details")
                else:
                    try:
                        result = api_client.raise_issue(description, issue_date.isoformat())
                        st.success("Issue submitted!")
                    except APIError as e:
                        st.error(f"Failed: {e.message}")


if __name__ == "__main__":
    main()
