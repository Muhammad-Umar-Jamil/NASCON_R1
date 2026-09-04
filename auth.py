import streamlit as st
import database as db
import re
import uuid

def login():
    st.markdown("#### // SECURE ACCESS TERMINAL<br>COMPETITOR AUTH", unsafe_allow_html=True)
    with st.form("login_form"):
        username = st.text_input("TEAM ID / CALLSIGN", key="login_username")
        password = st.text_input("ACCESS CODE", type="password", key="login_password")
        submitted = st.form_submit_button("INITIATE ACCESS", use_container_width=True)
        
        if submitted:
            if not username or not password:
                st.warning("Please provide both username and password.")
                return

            user = db.get_user(username)
            if user and db.check_password(password, user['password_hash']):
                new_token = str(uuid.uuid4())
                db.update_session_token(user['id'], new_token)
                
                st.session_state['user_id'] = user['id']
                st.session_state['username'] = user['username']
                st.session_state['name'] = user['name']
                st.session_state['role'] = user['role']
                st.session_state['is_admin'] = user['is_admin']
                st.session_state['is_approved'] = user['is_approved']
                st.session_state['has_broken_guardrail'] = user['has_broken_guardrail']
                st.session_state['session_token'] = new_token
                st.session_state['broken_guardrails'] = set()
                st.success("Access Granted! Welcome back.")
                st.rerun()
            else:
                st.error("Invalid credentials. Try again.")

def signup():
    st.markdown("#### // SYSTEM REGISTRATION<br>NEW COMPETITOR", unsafe_allow_html=True)
    
    role = st.selectbox("OPERATIVE CLASS", ["user", "tester"], help="Testers must have an NU ID. Users must have a University Roll No.")
    
    with st.form("signup_form"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("FULL DESIGNATION")
            new_user = st.text_input("CALLSIGN (USERNAME)")
            email = st.text_input("COMM LINK (EMAIL)")
            
        with col2:
            new_password = st.text_input("ACCESS CODE (PASSWORD)", type="password")
            phone_no = st.text_input("SECURE COMM (PHONE)")
            
            if role == "tester":
                nu_id = st.text_input("NU ID (Format: 2xI-xxxx)", help="Example: 21I-0453")
                university = None
                roll_no = None
            else:
                nu_id = None
                university = st.text_input("University Name")
                roll_no = st.text_input("University Roll No.")
            
        submitted = st.form_submit_button("TRANSMIT REGISTRATION", use_container_width=True)
        
        if submitted:
            name = name.strip() if name else ""
            new_user = new_user.strip() if new_user else ""
            email = email.strip() if email else ""
            phone_no = phone_no.strip() if phone_no else ""
            
            if not name or not new_user or not new_password or not email or not phone_no:
                st.warning("Please fill in all the basic required fields.")
                return
                
            if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
                st.error("Invalid email format.")
                return
            
            if not re.match(r"^[a-zA-Z0-9_-]{3,30}$", new_user):
                st.error("Username must be 3-30 characters and contain only letters, numbers, underscores, and hyphens.")
                return
                
            if len(new_password) < 6:
                st.error("Password must be at least 6 characters long.")
                return
                
            if role == "tester":
                if not nu_id:
                    st.warning("Testers must provide an NU ID.")
                    return
                if not re.match(r"^2\dI-\d{4}$", nu_id):
                    st.error("Invalid NU ID Format. It must match the format 2xI-xxxx (e.g. 21I-1234).")
                    return
            else:
                if not university or not roll_no:
                    st.warning("Users must provide a University Name and Roll No.")
                    return

            if db.get_user(new_user):
                st.error("This username is already taken. Choose another.")
            else:
                db.create_user(
                    username=new_user, 
                    password=new_password, 
                    name=name, 
                    email=email, 
                    role=role, 
                    phone_no=phone_no, 
                    nu_id=nu_id,
                    university=university,
                    roll_no=roll_no
                )
                st.success("Registration Sent! An Admin must approve your profile before you can talk to the AI.")
                st.balloons()
