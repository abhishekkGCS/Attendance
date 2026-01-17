"""
Calendar View Component
Displays attendance in a calendar format with color coding.
"""
import streamlit as st
from datetime import date, timedelta
import calendar
from typing import List, Dict, Optional

# Attendance code colors and labels
ATTENDANCE_COLORS = {
    "P": {"bg": "#4CAF50", "text": "#fff", "label": "Present"},
    "AB": {"bg": "#F44336", "text": "#fff", "label": "Absent"},
    "UNSCHD": {"bg": "#FF9800", "text": "#fff", "label": "Unscheduled"},
    "NCNS": {"bg": "#9C27B0", "text": "#fff", "label": "No Call No Show"},
    "CO": {"bg": "#2196F3", "text": "#fff", "label": "Comp Off"},
    "WFH": {"bg": "#00BCD4", "text": "#fff", "label": "Work From Home"},
    "HALF DAY": {"bg": "#FFEB3B", "text": "#333", "label": "Half Day"},
    "ABSCOND": {"bg": "#795548", "text": "#fff", "label": "Absconded"},
    "TERMINATE": {"bg": "#607D8B", "text": "#fff", "label": "Terminated"},
    "RESIGNED": {"bg": "#9E9E9E", "text": "#fff", "label": "Resigned"},
    "OFF": {"bg": "#E0E0E0", "text": "#333", "label": "Weekly Off"},
    "CL": {"bg": "#8BC34A", "text": "#fff", "label": "Casual Leave"},
    "SL": {"bg": "#FFC107", "text": "#333", "label": "Sick Leave"},
    "PL": {"bg": "#CDDC39", "text": "#333", "label": "Paid Leave"},
}


def render_calendar(attendance_data: Dict, year: int, month: int):
    """
    Render interactive attendance calendar.
    
    Args:
        attendance_data: Monthly attendance response from API
        year: Year to display
        month: Month to display
    """
    if "cal_selected_date" not in st.session_state:
        st.session_state.cal_selected_date = None

    # Month Navigation
    col1, col2, col3 = st.columns([1, 4, 1])
    
    # Calculate Prev/Next
    curr_date = date(year, month, 1)
    prev_date = curr_date - timedelta(days=1)
    next_date = (curr_date + timedelta(days=32)).replace(day=1)
    
    with col1:
        if st.button("←", key=f"prev_m_{year}_{month}", help="Previous Month"):
            st.session_state.calendar_date = prev_date
            st.rerun()
            
    with col2:
        st.markdown(f"<h3 style='text-align: center; margin: 0;'>{calendar.month_name[month]} {year}</h3>", unsafe_allow_html=True)
            
    with col3:
        if st.button("→", key=f"next_m_{year}_{month}", help="Next Month"):
            st.session_state.calendar_date = next_date
            st.rerun()

    # Build day lookup
    days_lookup = {}
    for day in attendance_data.get("days", []):
        day_date = day.get("date")
        if isinstance(day_date, str):
            days_lookup[day_date] = day
        elif hasattr(day_date, "isoformat"):
            days_lookup[day_date.isoformat()] = day

    # Calendar Grid Header
    st.markdown("---")
    cols = st.columns(7)
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    for i, d in enumerate(days):
        cols[i].markdown(f"<div style='text-align: center; font-weight: bold; color: #666;'>{d}</div>", unsafe_allow_html=True)
    
    # Calendar Grid Body
    cal = calendar.Calendar(firstweekday=0)
    month_days = cal.monthdayscalendar(year, month)
    
    today = date.today()
    
    for week in month_days:
        cols = st.columns(7)
        for i, day_num in enumerate(week):
            if day_num == 0:
                cols[i].write("")
                continue
            
            day_date = date(year, month, day_num)
            day_key = day_date.isoformat()
            day_data = days_lookup.get(day_key, {})
            code = day_data.get("code")
            
            # Label
            label = f"{day_num}"
            if code:
                label += f"\n{code}"
            
            # Determine button style/type
            # Streamlit buttons are limited in styling, so we use the label content
            # or rely on the details panel to show full color info.
            # Using basic type="primary" if present
            btn_type = "primary" if code and code not in ["OFF", "AB"] else "secondary"
            if code == "AB":
                btn_type = "primary" # Highlight absent too? Streamlit only has primary/secondary
            
            # We can use emoji in label for status
            emoji = ""
            if code == "P": emoji = "✅ "
            elif code == "AB": emoji = "❌ "
            elif code == "WFH": emoji = "🏠 "
            elif code in ["CL", "SL", "PL", "UNSCHD"]: emoji = "🟡 "
            elif code == "OFF": emoji = "🏖️ "
            
            btn_label = f"{emoji}{day_num}"
            
            if cols[i].button(btn_label, key=f"cal_btn_{year}_{month}_{day_num}", use_container_width=True):
                st.session_state.cal_selected_date = {
                    "date": day_date,
                    "data": day_data
                }

    # Detail Panel
    if st.session_state.cal_selected_date:
        render_detail_panel(st.session_state.cal_selected_date)


def render_detail_panel(selection):
    """Render details for selected date."""
    sel_date = selection["date"]
    data = selection["data"]
    code = data.get("code")
    
    st.markdown("---")
    st.markdown(f"#### 📅 Attendance Details: {sel_date.strftime('%A, %d %B %Y')}")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        if code:
            info = ATTENDANCE_COLORS.get(code, {})
            st.metric("Status", info.get("label", code), delta=None)
            st.markdown(f"<div style='background-color: {info.get('bg', '#ccc')}; height: 4px; width: 100%; border-radius: 2px;'></div>", unsafe_allow_html=True)
        else:
            st.info("No attendance record found.")
            
    with col2:
        if code:
            st.markdown(f"**Code:** `{code}`")
            if data.get("login_hours"):
                 st.markdown(f"**Login Hours:** {data.get('login_hours')} hrs")
            if data.get("remarks"):
                st.markdown(f"**Remarks:** {data.get('remarks')}")
            if data.get("approved_by"):
                # Ideally fetch name, but ID is what we might have directly
                st.markdown(f"**Approved By:** {data.get('approved_by')}")
            
            # Leave specific fields if available in backend response
            # (Assuming remarks might contain reason if not separate field)
    

def render_legend():
    """Render attendance code legend."""
    st.markdown("#### 🏷️ Legend")
    cols = st.columns(6)
    codes = list(ATTENDANCE_COLORS.items())
    for i, (code, info) in enumerate(codes):
        col_idx = i % 6
        with cols[col_idx]:
             st.markdown(f"<span style='color:{info['bg']}; font-weight:bold;'>■</span> {code}", unsafe_allow_html=True)

def render_month_selector(year, month):
    # Backward compatibility stub if needed, but render_calendar handles its own nav now
    pass 

def render_mini_dashboard_calendar(attendance_data: Dict, year: int, month: int):
    """
    Render a compact, interactive mini calendar in the sidebar.
    
    Args:
        attendance_data: Monthly attendance data
        year: Year
        month: Month
    """
    if "selected_date_details" not in st.session_state:
        st.session_state.selected_date_details = None

    # Compact Month Selector
    col1, col2 = st.columns([2, 1])
    with col1:
        months = [
            (1, "Jan"), (2, "Feb"), (3, "Mar"), (4, "Apr"),
            (5, "May"), (6, "Jun"), (7, "Jul"), (8, "Aug"),
            (9, "Sep"), (10, "Oct"), (11, "Nov"), (12, "Dec")
        ]
        
        # Callback to update view
        def update_month():
            pass 

        sel_month = st.selectbox(
            "Month", 
            options=[m[0] for m in months], 
            format_func=lambda x: months[x-1][1],
            index=month-1,
            label_visibility="collapsed",
            key="mini_cal_month"
        )
    with col2:
        sel_year = st.number_input(
            "Year", 
            min_value=2020, 
            max_value=2030, 
            value=year, 
            label_visibility="collapsed",
            key="mini_cal_year"
        )

    # Build lookup
    days_lookup = {}
    for day in attendance_data.get("days", []):
        day_date = day.get("date")
        if isinstance(day_date, str):
            days_lookup[day_date] = day
    
    # Header
    cols = st.columns(7)
    days = ["M", "T", "W", "T", "F", "S", "S"]
    for i, d in enumerate(days):
        cols[i].markdown(f"<div style='text-align: center; font-size: 0.8rem; font-weight: bold;'>{d}</div>", unsafe_allow_html=True)
    
    # Calendar
    cal = calendar.Calendar(firstweekday=0)
    month_days = cal.monthdayscalendar(sel_year, sel_month)
    
    today = date.today()
    
    # Status Icons
    ICONS = {
        "P": "✅", "WFH": "🏠", "AB": "❌", "UNSCHD": "⏳", 
        "HALF DAY": "🌗", "OFF": "🏖️", "CO": "🔄", "NCNS": "🚫"
    }
    
    for week in month_days:
        cols = st.columns(7)
        for i, day_num in enumerate(week):
            if day_num == 0:
                cols[i].write("")
                continue
                
            day_date = date(sel_year, sel_month, day_num)
            day_key = day_date.isoformat()
            day_data = days_lookup.get(day_key, {})
            code = day_data.get("code")
            
            icon = ICONS.get(code, str(day_num))
            if not code and day_date > today:
                icon = str(day_num)
            elif not code:
                icon = str(day_num)
                
            # Button for the day
            # Use columns key to avoid duplicates
            if cols[i].button(icon, key=f"btn_{sel_year}_{sel_month}_{day_num}", help=f"{day_date.strftime('%d %b %Y')}: {code or 'No Record'}", use_container_width=True):
                st.session_state.selected_date_details = {
                    "date": day_date,
                    "data": day_data
                }
    
    st.divider()
    
    # Selected Details View
    if st.session_state.selected_date_details:
        sel_date = st.session_state.selected_date_details["date"]
        sel_data = st.session_state.selected_date_details["data"]
        
        st.markdown(f"**Date:** {sel_date.strftime('%A, %d %B %Y')}")
        
        code = sel_data.get("code")
        if code:
            st.info(f"Status: **{ATTENDANCE_COLORS.get(code, {}).get('label', code)}**")
            # Show times if available
            if sel_data.get("check_in"):
                st.caption(f"Check In: {sel_data.get('check_in')}")
            if sel_data.get("check_out"):
                st.caption(f"Check Out: {sel_data.get('check_out')}")
        else:
            st.warning("No attendance marked")
            
        # Edit Access (Mockup for role check)
        # In real app, check st.session_state.user['role']
        from services.session import get_user
        user = get_user()
        if user and user.get("role") in ["supervisor", "admin"]:
            with st.expander("Edit Attendance"):
                 st.text_input("New Status", key="edit_status")
                 st.button("Update", key="update_btn")

    return sel_year, sel_month
