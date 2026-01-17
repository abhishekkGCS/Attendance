"""
Attendance Table Component
Displays attendance in a tabular format.
"""
import streamlit as st
import pandas as pd
from typing import Dict, List


def render_attendance_table(attendance_data: Dict):
    """
    Render attendance as a styled table.
    
    Args:
        attendance_data: Monthly attendance response from API
    """
    
    days = attendance_data.get("days", [])
    
    if not days:
        st.info("No attendance data for this period.")
        return
    
    # Convert to DataFrame
    records = []
    for day in days:
        day_date = day.get("date")
        if isinstance(day_date, str):
            date_str = day_date
        else:
            date_str = day_date.isoformat() if hasattr(day_date, "isoformat") else str(day_date)
        
        records.append({
            "Date": date_str,
            "Day": pd.to_datetime(date_str).strftime("%A"),
            "Status": day.get("code") or "—",
            "Weekend": "Yes" if day.get("is_weekend") else "No",
            "Pending": "⏳" if day.get("pending_request") else "",
        })
    
    df = pd.DataFrame(records)
    
    # Style the table
    def style_status(val):
        colors = {
            "P": "background-color: #4CAF50; color: white;",
            "AB": "background-color: #F44336; color: white;",
            "UNSCHD": "background-color: #FF9800; color: white;",
            "NCNS": "background-color: #9C27B0; color: white;",
            "CO": "background-color: #2196F3; color: white;",
            "WFH": "background-color: #00BCD4; color: white;",
            "HALF DAY": "background-color: #FFEB3B; color: black;",
            "ABSCOND": "background-color: #795548; color: white;",
            "TERMINATE": "background-color: #607D8B; color: white;",
            "RESIGNED": "background-color: #9E9E9E; color: white;",
            "OFF": "background-color: #E0E0E0; color: black;",
        }
        return colors.get(val, "")
    
    styled_df = df.style.applymap(style_status, subset=["Status"])
    
    st.dataframe(
        styled_df,
        use_container_width=True,
        hide_index=True,
        height=400,
    )


def render_summary_stats(attendance_data: Dict):
    """Render attendance summary statistics."""
    
    summary = attendance_data.get("summary", {})
    
    if not summary:
        return
    
    st.markdown("#### 📈 Monthly Summary")
    
    # Create columns for stats
    cols = st.columns(min(len(summary), 6))
    
    code_names = {
        "P": "Present",
        "AB": "Absent",
        "OFF": "Off Days",
        "WFH": "Work From Home",
        "HALF DAY": "Half Days",
        "NCNS": "No Call No Show",
    }
    
    for i, (code, count) in enumerate(summary.items()):
        if i < 6:  # Show first 6
            with cols[i]:
                label = code_names.get(code, code)
                st.metric(label, count)


def render_pending_requests(requests: List[Dict]):
    """Render pending attendance requests table."""
    
    if not requests:
        st.info("No pending requests.")
        return
    
    st.markdown("#### ⏳ Pending Requests")
    
    records = []
    for req in requests:
        records.append({
            "ID": str(req.get("id", ""))[:8],
            "Date": req.get("request_date"),
            "Requested Status": req.get("requested_code"),
            "Reason": req.get("reason", "")[:30] + "..." if len(req.get("reason", "")) > 30 else req.get("reason", ""),
            "Submitted": req.get("created_at", "")[:10] if req.get("created_at") else "",
        })
    
    df = pd.DataFrame(records)
    st.dataframe(df, use_container_width=True, hide_index=True)
