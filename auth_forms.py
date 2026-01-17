"""
Authentication Form Components
Login and OTP verification UI.
"""
import streamlit as st
from services.api_client import api_client, APIError
from services.session import set_tokens, set_user


def render_login_form():
    """Render the OTP login form."""
    
    st.markdown("""
    <style>
    .login-container {
        max-width: 400px;
        margin: 0 auto;
        padding: 2rem;
    }
    .login-header {
        text-align: center;
        margin-bottom: 2rem;
    }
    .login-header h1 {
        font-size: 1.8rem;
        color: #2196F3;
        margin-bottom: 0.5rem;
        margin-top: 1rem;
    }
    .login-header p {
        color: #666;
        font-size: 0.95rem;
    }
    .login-section-title {
        color: #2196F3;
        font-size: 1.3rem;
        margin-bottom: 0.5rem;
    }
    .otp-info {
        background: #E3F2FD;
        border: 1px solid #2196F3;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
        text-align: center;
    }
    .otp-info p {
        color: #1565C0;
        margin: 0;
    }
    .centered-logo {
        display: flex;
        justify-content: center;
        margin-bottom: 1rem;
    }
    </style>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # Centered Logo and Header
        import base64
        
        try:
            with open("assets/logo.png", "rb") as f:
                data = base64.b64encode(f.read()).decode("utf-8")
                img_html = f'<img src="data:image/png;base64,{data}" style="width: 180px; display: block; margin: 0 auto; margin-bottom: 1rem;">'
        except Exception:
            img_html = ""

        st.markdown(f"""
        <div class="login-header">
            {img_html}
            <h1>Galactic Client Services</h1>
            <p>Employee Attendance Dashboard</p>
        </div>
        """, unsafe_allow_html=True)
        
        if not st.session_state.get("otp_requested", False):
            # Email input form
            render_email_form()
        else:
            # OTP verification form
            render_otp_form()


def render_email_form():
    """Render email input for OTP request."""
    
    st.markdown('<h3 class="login-section-title">Login with Email</h3>', unsafe_allow_html=True)
    st.caption("Enter your official employee email to receive a one-time password.")
    
    with st.form("email_form", clear_on_submit=False):
        email = st.text_input(
            "Email Address",
            placeholder="your.name@galactic-services.com",
            key="login_email",
        )
        
        submitted = st.form_submit_button("Send OTP", use_container_width=True, type="primary")
        
        if submitted:
            if not email:
                st.error("Please enter your email address")
            elif "@" not in email:
                st.error("Please enter a valid email address")
            else:
                with st.spinner("Sending OTP..."):
                    try:
                        result = api_client.request_otp(email)
                        st.session_state.otp_requested = True
                        st.session_state.otp_email = email
                        st.success(f"OTP sent to {result.get('email', email)}")
                        st.rerun()
                    except APIError as e:
                        st.error(f"Failed to send OTP: {e.message}")
                    except Exception as e:
                        st.error(f"Connection error. Please ensure the backend is running.")
    
    st.markdown("""
    <div class="otp-info">
        <p><strong>No password required!</strong></p>
        <p style="font-size: 0.85rem; margin-top: 0.5rem;">
            We'll send a 6-digit code to your email for secure login.
        </p>
    </div>
    """, unsafe_allow_html=True)


def render_otp_form():
    """Render OTP verification form."""
    
    email = st.session_state.get("otp_email", "")
    
    st.markdown('<h3 class="login-section-title">Enter OTP</h3>', unsafe_allow_html=True)
    st.caption(f"We sent a code to **{email}**")
    
    with st.form("otp_form", clear_on_submit=False):
        otp = st.text_input(
            "One-Time Password",
            max_chars=6,
            placeholder="Enter 6-digit code",
            key="login_otp",
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            back = st.form_submit_button("Back", use_container_width=True)
        
        with col2:
            verify = st.form_submit_button("Verify", use_container_width=True, type="primary")
        
        if back:
            st.session_state.otp_requested = False
            st.session_state.otp_email = ""
            st.rerun()
        
        if verify:
            if not otp or len(otp) != 6:
                st.error("Please enter a valid 6-digit OTP")
            else:
                with st.spinner("Verifying..."):
                    try:
                        # Verify OTP and get tokens
                        result = api_client.verify_otp(email, otp)
                        set_tokens(result["access_token"], result["refresh_token"])
                        
                        # Get user info
                        user_info = api_client.get_current_user()
                        set_user(user_info)
                        
                        st.success(f"Welcome, {user_info.get('full_name', 'User')}!")
                        st.rerun()
                        
                    except APIError as e:
                        st.error(f"Verification failed: {e.message}")
                    except Exception as e:
                        st.error(f"Connection error: {str(e)}")
    
    st.markdown("""
    <div class="otp-info">
        <p style="font-size: 0.85rem;">
            OTP expires in 5 minutes. Check your email inbox.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Resend OTP option
    if st.button("Didn't receive code? Resend OTP"):
        with st.spinner("Resending..."):
            try:
                api_client.request_otp(email)
                st.success("New OTP sent!")
            except APIError as e:
                st.error(e.message)
