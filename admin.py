import streamlit as st
import database as db

def admin_panel():
    st.markdown("""
    <div class="arena-badge"><div class="arena-dot"></div>ADMIN ACCESS</div>
    """, unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center;'>Admin Command Center</h1>", unsafe_allow_html=True)
    
    # Secure server-side verification of admin status
    user = db.get_user(st.session_state.get('username'))
    if not user or not user['is_admin']:
        st.error("Access denied. Command Center is strictly for Admins.")
        st.session_state['is_admin'] = False
        return

    users = db.get_all_users()

    # ── OVERVIEW STATS ──
    total_users = len(users)
    pending_count = len([u for u in users if not u['is_approved']])
    winners_count = len([u for u in users if u['has_broken_guardrail']])
    testers_count = len([u for u in users if u.get('role') == 'tester'])
    regular_count = len([u for u in users if u.get('role') == 'user'])
    active_sessions = len([u for u in users if u.get('session_token')])

    st.markdown(f"""
    <div class="stat-grid" style="grid-template-columns: repeat(3, 1fr);">
        <div class="stat-card"><div class="stat-label">// TOTAL USERS</div><div class="stat-value">{total_users}</div></div>
        <div class="stat-card{' win' if pending_count else ''}"><div class="stat-label">// PENDING APPROVAL</div><div class="stat-value">{pending_count}</div></div>
        <div class="stat-card win"><div class="stat-label">// GUARDRAILS FULLY BROKEN</div><div class="stat-value">{winners_count}</div></div>
    </div>
    <div class="stat-grid" style="grid-template-columns: repeat(3, 1fr);">
        <div class="stat-card"><div class="stat-label">// TESTERS</div><div class="stat-value">{testers_count}</div></div>
        <div class="stat-card"><div class="stat-label">// REGULAR USERS</div><div class="stat-value">{regular_count}</div></div>
        <div class="stat-card"><div class="stat-label">// ACTIVE SESSIONS</div><div class="stat-value">{active_sessions}</div></div>
    </div>
    """, unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════
    # MAIN ADMIN TABS
    # ══════════════════════════════════════════════════════════════════
    main_tabs = st.tabs([
        "⚙️ Guardrail Settings",
        "🛡️ Pending Approvals",
        "🧪 Tester Management",
        "📊 User Database",
        "🔍 Chat Transcripts",
        "🧪 Test Models",
        "❌ Danger Zone"
    ])

    # ──────────────────────────────────────────────────────────────────
    # TAB 1: GUARDRAIL SETTINGS
    # ──────────────────────────────────────────────────────────────────
    with main_tabs[0]:
        st.header("⚙️ Global Guardrail Settings")
        settings = db.get_settings()

        tab_badges = [('badge-g', '500 PTS · EASY'), ('badge-y', '800 PTS · MEDIUM'), ('badge-r', '1200 PTS · HARD')]
        g_tabs = st.tabs(["Guardrail 1", "Guardrail 2", "Guardrail 3"])
        
        for i, tab in enumerate(g_tabs):
            gid = i + 1
            g_data = settings.get(gid, {})
            with tab:
                b_class, b_text = tab_badges[i]
                st.markdown(f'<span class="badge {b_class}">{b_text}</span>', unsafe_allow_html=True)
                with st.form(f"settings_form_{gid}"):
                    st.subheader(g_data.get('guardrail_name', f"Guardrail {gid}"))
                    st.caption("🔒 The forbidden word below is only ever revealed to Admins and Testers — never to regular users.")
                    current_endpoint = g_data.get('api_endpoint', 'openrouter')
                    endpoint_idx = 0 if current_endpoint == 'openrouter' else 1
                    selected_endpoint = st.selectbox("API Endpoint", ["OpenRouter", "Transfer Station"], index=endpoint_idx, key=f"endpoint_{gid}")
                    api_endpoint_val = 'openrouter' if selected_endpoint == 'OpenRouter' else 'transfer_station'
                    import main
                    if api_endpoint_val == 'transfer_station':
                        all_models_admin = main.fetch_transfer_station_models()
                    else:
                        all_models_admin = main.fetch_openrouter_models()
                    
                    saved_model = g_data.get('model_name', '')
                    model_opts_admin = all_models_admin.copy()
                    
                    # Try to set index to the saved model if valid, else default to the first valid model (index 0)
                    default_idx = 0
                    if saved_model in model_opts_admin:
                        default_idx = model_opts_admin.index(saved_model)
                    
                    if not model_opts_admin:
                        m_name = st.text_input("Model Name", value=saved_model)
                    else:
                        m_name = st.selectbox("Model Name", options=model_opts_admin, index=default_idx)
                    s_prompt = st.text_area("System Prompt", value=g_data.get('system_prompt', ''), height=150)
                    f_word = st.text_input("Forbidden Word", value=g_data.get('forbidden_word', ''))
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        temp = st.slider("Temperature", 0.0, 2.0, float(g_data.get('temperature', 0.7)), 0.05)
                        tp = st.slider("Top P", 0.0, 1.0, float(g_data.get('top_p', 0.9)), 0.01)
                    with col2:
                        tokens = st.slider("Max Tokens", 128, 4096, int(g_data.get('max_tokens', 512)), 64)
                        rp = st.slider("Repetition Penalty", 0.0, 2.0, float(g_data.get('rep_pen', 1.0)), 0.1)
                    
                    if st.form_submit_button(f"Deploy Settings for Guardrail {gid}", width='stretch'):
                        db.update_guardrail_settings(gid, m_name, s_prompt, f_word, temp, tokens, tp, rp, api_endpoint_val)
                        st.success(f"Global Settings for Guardrail {gid} successfully deployed!")

    # ──────────────────────────────────────────────────────────────────
    # TAB 2: PENDING APPROVALS
    # ──────────────────────────────────────────────────────────────────
    with main_tabs[1]:
        st.header("🛡️ Pending Approvals")
        pending_users = [u for u in users if not u['is_approved']]
        if pending_users:
            st.markdown(f'<span class="badge badge-y">{len(pending_users)} AWAITING REVIEW</span>', unsafe_allow_html=True)
            
            # Bulk approve all button
            if st.button("✅ Approve ALL Pending Users", type="primary", width='stretch'):
                for u in pending_users:
                    db.approve_user(u['id'])
                st.success(f"All {len(pending_users)} pending users have been approved!")
                st.rerun()
            
            st.divider()
            
            for u in pending_users:
                role_badge_class = 'badge-p' if u['role'] == 'tester' else 'badge-y'
                with st.expander(f"Review Profile: {u['username']} ({u['name']})"):
                    st.markdown(f'<span class="badge {role_badge_class}">{u["role"].upper()}</span>', unsafe_allow_html=True)
                    col_info1, col_info2 = st.columns(2)
                    with col_info1:
                        st.write(f"**Email:** {u['email']}")
                        st.write(f"**Phone:** {u['phone_no']}")
                    with col_info2:
                        st.write(f"**Requested Role:** `{u['role']}`")
                        if u['role'] == "tester":
                            st.write(f"**NU ID:** {u['nu_id']}")
                        else:
                            st.write(f"**University:** {u['university']}")
                            st.write(f"**Roll No:** {u['roll_no']}")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("✅ Approve", key=f"approve_{u['id']}", type="primary", width='stretch'):
                            db.approve_user(u['id'])
                            st.success(f"{u['username']} has been approved!")
                            st.rerun()
                    with col2:
                        if st.button("❌ Reject & Delete", key=f"reject_{u['id']}", width='stretch'):
                            db.delete_user(u['id'])
                            st.error(f"{u['username']} rejected and deleted.")
                            st.rerun()
        else:
            st.info("No pending approvals. All caught up!")

    # ──────────────────────────────────────────────────────────────────
    # TAB 3: TESTER MANAGEMENT (COMPLETE)
    # ──────────────────────────────────────────────────────────────────
    with main_tabs[2]:
        st.header("🧪 Tester Management")
        
        tester_list = [u for u in users if u.get('role') == 'tester']
        regular_list = [u for u in users if u.get('role') == 'user']
        
        # ── Tester Stats ──
        approved_testers = [t for t in tester_list if t['is_approved']]
        pending_testers = [t for t in tester_list if not t['is_approved']]
        active_testers = [t for t in tester_list if t.get('session_token')]
        
        st.markdown(f"""
        <div class="stat-grid" style="grid-template-columns: repeat(4, 1fr);">
            <div class="stat-card"><div class="stat-label">// TOTAL TESTERS</div><div class="stat-value">{len(tester_list)}</div></div>
            <div class="stat-card"><div class="stat-label">// APPROVED</div><div class="stat-value">{len(approved_testers)}</div></div>
            <div class="stat-card{' win' if pending_testers else ''}"><div class="stat-label">// PENDING</div><div class="stat-value">{len(pending_testers)}</div></div>
            <div class="stat-card"><div class="stat-label">// ACTIVE NOW</div><div class="stat-value">{len(active_testers)}</div></div>
        </div>
        """, unsafe_allow_html=True)
        
        tester_sub_tabs = st.tabs(["📋 Tester Roster", "➕ Create Tester", "🔄 Promote User → Tester", "⚡ Quick Actions"])
        
        # ── Sub-Tab 1: Tester Roster ──
        with tester_sub_tabs[0]:
            st.subheader("📋 All Registered Testers")
            if tester_list:
                tester_table = []
                for t in tester_list:
                    session_status = "🟢 Online" if t.get('session_token') else "⚫ Offline"
                    tester_table.append({
                        "ID": t['id'],
                        "Username": t['username'],
                        "Name": t['name'] or "—",
                        "NU ID": t.get('nu_id') or "—",
                        "Email": t.get('email') or "—",
                        "Phone": t.get('phone_no') or "—",
                        "Approved": "✅" if t['is_approved'] else "⏳",
                        "Winner": "🏆" if t['has_broken_guardrail'] else "—",
                        "Session": session_status,
                    })
                st.dataframe(tester_table, width='stretch')
                
                # ── Individual Tester Actions ──
                st.divider()
                st.subheader("🔧 Manage Individual Tester")
                tester_options = {f"{t['username']} ({t['name']})": t for t in tester_list}
                selected_tester_key = st.selectbox(
                    "Select Tester", 
                    options=["-- Select Tester --"] + list(tester_options.keys()),
                    key="manage_tester_sel"
                )
                
                if selected_tester_key != "-- Select Tester --":
                    sel_tester = tester_options[selected_tester_key]
                    
                    st.markdown(f"""
                    <div class="arena-card">
                        <span style="color:var(--purple);letter-spacing:2px;font-size:11px;">// TESTER PROFILE</span><br>
                        <span style="color:var(--yellow);font-family:'Orbitron',sans-serif;font-size:1.1rem;">{sel_tester['username']}</span><br>
                        <span style="color:var(--muted);font-size:11px;letter-spacing:1px;">
                            NAME: {sel_tester['name'] or '—'} · 
                            NU ID: {sel_tester.get('nu_id') or '—'} · 
                            EMAIL: {sel_tester.get('email') or '—'}
                        </span>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    col_a, col_b, col_c, col_d = st.columns(4)
                    
                    with col_a:
                        if not sel_tester['is_approved']:
                            if st.button("✅ Approve", key=f"t_approve_{sel_tester['id']}", width='stretch'):
                                db.approve_user(sel_tester['id'])
                                st.success(f"{sel_tester['username']} approved!")
                                st.rerun()
                        else:
                            st.success("Already Approved")
                    
                    with col_b:
                        if st.button("🔁 Reset Password", key=f"t_reset_{sel_tester['id']}", width='stretch'):
                            st.session_state[f'show_reset_{sel_tester["id"]}'] = True
                    
                    with col_c:
                        if st.button("🚪 Force Logout", key=f"t_kick_{sel_tester['id']}", width='stretch'):
                            db.kick_user_session(sel_tester['id'])
                            st.success(f"{sel_tester['username']} session invalidated! They must re-login.")
                            st.rerun()
                    
                    with col_d:
                        if st.button("⬇️ Demote to User", key=f"t_demote_{sel_tester['id']}", width='stretch'):
                            db.update_user_role(sel_tester['id'], 'user')
                            st.warning(f"{sel_tester['username']} demoted to regular user.")
                            st.rerun()
                    
                    # Password reset form (shown when button is clicked)
                    if st.session_state.get(f'show_reset_{sel_tester["id"]}'):
                        with st.form(f"reset_pass_form_{sel_tester['id']}"):
                            new_pass = st.text_input("New Password", type="password", key=f"new_pass_{sel_tester['id']}")
                            if st.form_submit_button("Confirm Password Reset", width='stretch'):
                                if new_pass and len(new_pass) >= 6:
                                    db.reset_user_password(sel_tester['id'], new_pass)
                                    db.kick_user_session(sel_tester['id'])
                                    st.success(f"Password reset for {sel_tester['username']}. Their session has been invalidated.")
                                    st.session_state.pop(f'show_reset_{sel_tester["id"]}', None)
                                    st.rerun()
                                else:
                                    st.error("Password must be at least 6 characters.")
                    
                    # Chat history for this tester
                    st.divider()
                    chats = db.get_chats(sel_tester['id'])
                    if chats:
                        with st.expander(f"💬 Chat History ({len(chats)} messages)", expanded=False):
                            for chat in chats:
                                with st.chat_message(chat['role']):
                                    st.caption(chat['timestamp'])
                                    st.write(chat['content'])
                    else:
                        st.info("No chat history for this tester.")
            else:
                st.info("No testers registered yet.")
        
        # ── Sub-Tab 2: Create New Tester ──
        with tester_sub_tabs[1]:
            st.subheader("➕ Create New Tester Account")
            st.caption("Create a pre-approved tester account that can log in immediately.")
            
            with st.form("create_tester_form"):
                ct_col1, ct_col2 = st.columns(2)
                with ct_col1:
                    ct_username = st.text_input("Username")
                    ct_password = st.text_input("Password", type="password")
                    ct_name = st.text_input("Full Name")
                with ct_col2:
                    ct_email = st.text_input("Email")
                    ct_phone = st.text_input("Phone")
                    ct_nu_id = st.text_input("NU ID (Format: 2xI-xxxx)")
                
                if st.form_submit_button("Create Tester Account", type="primary", width='stretch'):
                    if not ct_username or not ct_password or not ct_name:
                        st.error("Username, Password, and Name are required.")
                    elif len(ct_password) < 6:
                        st.error("Password must be at least 6 characters.")
                    elif db.get_user(ct_username):
                        st.error(f"Username '{ct_username}' is already taken.")
                    else:
                        db.create_user(
                            username=ct_username,
                            password=ct_password,
                            name=ct_name,
                            email=ct_email or None,
                            role='tester',
                            phone_no=ct_phone or None,
                            nu_id=ct_nu_id or None,
                            is_admin=False
                        )
                        db.approve_user(db.get_user(ct_username)['id'])
                        st.success(f"✅ Tester '{ct_username}' created and auto-approved! They can log in now.")
                        st.rerun()
        
        # ── Sub-Tab 3: Promote Regular User to Tester ──
        with tester_sub_tabs[2]:
            st.subheader("🔄 Promote Regular User → Tester")
            st.caption("Upgrade an existing regular user to tester role. They will gain access to tester controls (model overrides, forbidden word visibility).")
            
            if regular_list:
                promote_options = {f"{u['username']} ({u['name']})": u for u in regular_list}
                promote_sel = st.selectbox(
                    "Select User to Promote",
                    options=["-- Select User --"] + list(promote_options.keys()),
                    key="promote_sel"
                )
                
                if promote_sel != "-- Select User --":
                    promote_user = promote_options[promote_sel]
                    st.markdown(f"""
                    <div class="arena-card">
                        <span style="color:var(--purple);letter-spacing:2px;font-size:11px;">// CURRENT PROFILE</span><br>
                        <span style="color:var(--muted);font-size:11px;letter-spacing:1px;">
                            USERNAME: <span style="color:var(--yellow)">{promote_user['username']}</span> · 
                            ROLE: <span style="color:var(--yellow)">{promote_user['role']}</span> · 
                            UNIVERSITY: <span style="color:var(--yellow)">{promote_user.get('university') or '—'}</span>
                        </span>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if st.button(f"⬆️ Promote {promote_user['username']} to Tester", type="primary", width='stretch'):
                        db.update_user_role(promote_user['id'], 'tester')
                        db.kick_user_session(promote_user['id'])
                        st.success(f"✅ {promote_user['username']} is now a Tester! Their session has been reset — they need to re-login to see tester controls.")
                        st.rerun()
            else:
                st.info("No regular users available to promote.")
        
        # ── Sub-Tab 4: Quick Actions ──
        with tester_sub_tabs[3]:
            st.subheader("⚡ Bulk Tester Actions")
            
            col_q1, col_q2 = st.columns(2)
            
            with col_q1:
                st.markdown("""
                <div class="arena-card">
                    <span style="color:var(--purple);letter-spacing:2px;font-size:11px;">// APPROVE ALL TESTERS</span><br>
                    <span style="color:var(--muted);font-size:11px;">Instantly approve all pending tester registrations.</span>
                </div>
                """, unsafe_allow_html=True)
                if pending_testers:
                    if st.button(f"✅ Approve All {len(pending_testers)} Pending Testers", type="primary", width='stretch'):
                        for t in pending_testers:
                            db.approve_user(t['id'])
                        st.success(f"All {len(pending_testers)} testers approved!")
                        st.rerun()
                else:
                    st.info("No pending testers.")
            
            with col_q2:
                st.markdown("""
                <div class="arena-card">
                    <span style="color:var(--purple);letter-spacing:2px;font-size:11px;">// FORCE LOGOUT ALL TESTERS</span><br>
                    <span style="color:var(--muted);font-size:11px;">Kick all testers out. They must re-login.</span>
                </div>
                """, unsafe_allow_html=True)
                if active_testers:
                    if st.button(f"🚪 Force Logout All {len(active_testers)} Active Testers", width='stretch'):
                        for t in active_testers:
                            db.kick_user_session(t['id'])
                        st.success(f"All {len(active_testers)} tester sessions invalidated!")
                        st.rerun()
                else:
                    st.info("No active tester sessions.")
            
            st.divider()
            
            col_q3, col_q4 = st.columns(2)
            
            with col_q3:
                st.markdown("""
                <div class="arena-card">
                    <span style="color:var(--purple);letter-spacing:2px;font-size:11px;">// FORCE LOGOUT ALL USERS</span><br>
                    <span style="color:var(--muted);font-size:11px;">Kick every single user (testers + regular) off the app.</span>
                </div>
                """, unsafe_allow_html=True)
                all_active = [u for u in users if u.get('session_token') and not u.get('is_admin')]
                if all_active:
                    if st.button(f"🚪 Force Logout ALL {len(all_active)} Users", width='stretch'):
                        for u in all_active:
                            db.kick_user_session(u['id'])
                        st.success(f"All {len(all_active)} user sessions invalidated!")
                        st.rerun()
                else:
                    st.info("No active user sessions.")
            
            with col_q4:
                st.markdown("""
                <div class="arena-card">
                    <span style="color:var(--purple);letter-spacing:2px;font-size:11px;">// RESET ALL WINNERS</span><br>
                    <span style="color:var(--muted);font-size:11px;">Clear all guardrail-broken flags. Competition restarts.</span>
                </div>
                """, unsafe_allow_html=True)
                all_winners = [u for u in users if u['has_broken_guardrail'] and not u.get('is_admin')]
                if all_winners:
                    if st.button(f"🔄 Reset All {len(all_winners)} Winners", width='stretch'):
                        for u in all_winners:
                            db.update_user_status(u['id'], False)
                            db.kick_user_session(u['id'])
                        st.success(f"All {len(all_winners)} winners reset! Their sessions were invalidated.")
                        st.rerun()
                else:
                    st.info("No winners to reset.")

    # ──────────────────────────────────────────────────────────────────
    # TAB 4: USER DATABASE
    # ──────────────────────────────────────────────────────────────────
    with main_tabs[3]:
        st.header("📊 User Database")
        if users:
            clean_users = []
            for u in users:
                session_status = "🟢" if u.get('session_token') else "⚫"
                clean_users.append({
                    "ID": u['id'],
                    "Username": u['username'],
                    "Name": u.get('name') or "—",
                    "Role": u['role'],
                    "Status": "✅ Approved" if u['is_approved'] else "⏳ Pending",
                    "Winner": "🏆 Yes" if u['has_broken_guardrail'] else "❌ No",
                    "Session": session_status,
                })
            st.dataframe(clean_users, width='stretch')
        else:
            st.info("No users found.")

    # ──────────────────────────────────────────────────────────────────
    # TAB 5: CHAT TRANSCRIPTS
    # ──────────────────────────────────────────────────────────────────
    with main_tabs[4]:
        st.header("🔍 View Chat Transcripts")
        user_options = {f"{u['username']} ({u['role']}) {'🏅' if u['has_broken_guardrail'] else ''}": u['id'] for u in users}
        if user_options:
            selected_user = st.selectbox("Select User Profile", options=["-- Select User --"] + list(user_options.keys()))
            if selected_user != "-- Select User --":
                user_id = user_options[selected_user]
                chats = db.get_chats(user_id)
                if chats:
                    st.markdown(f'<span class="badge badge-p">{len(chats)} MESSAGES</span>', unsafe_allow_html=True)
                    with st.expander(f"Chat History for {selected_user}", expanded=True):
                        for chat in chats:
                            with st.chat_message(chat['role']):
                                st.caption(chat['timestamp'])
                                st.write(chat['content'])
                else:
                    st.info("No chat transcripts found for this user.")

    # ──────────────────────────────────────────────────────────────────
    # TAB 6: TEST TRANSFER STATION MODELS
    # ──────────────────────────────────────────────────────────────────
    with main_tabs[5]:
        st.header("🧪 Test Transfer Station Models")
        st.caption("Tests chat models from Transfer Station (MakerEnd). Only models from OpenAI (gpt-), Claude (claude-), and Gemini (gemini-) that return a valid response are tested and shown.")
        
        import requests
        import os
        
        TS_KEY = os.getenv("TRANSFER_STATION_API_KEY", "")
        TS_URL = "https://makerend.com/v1"
        
        if not TS_KEY:
            st.error("⚠️ TRANSFER_STATION_API_KEY is not set in .env. Cannot test models.")
        else:
            def is_chat_model(model_id: str) -> bool:
                mid = model_id.lower()
                
                # Check for desired prefixes (only gpt-5.6 and gpt-6)
                is_desired_provider = 'gpt-5.6' in mid or 'gpt-6' in mid
                if not is_desired_provider:
                    return False
                    
                # Exclude specific sub-types (image, audio, embedding, etc.)
                EXCLUDED_SUBSTRINGS = (
                    'embedding', 'reranker', 'rerank', 'tts', 'whisper', 'audio',
                    'speech', 'voice', 'upload', 'video', 'image', 'lipsync', 'jev-',
                    'vision', 'realtime', 'transcribe', 'astra'
                )
                if any(s in mid for s in EXCLUDED_SUBSTRINGS):
                    return False
                return True
            
            col_fetch, col_status = st.columns([1, 2])
            with col_fetch:
                fetch_btn = st.button("📡 Fetch & Test All Chat Models", type="primary", width='stretch')
            
            if fetch_btn:
                with st.spinner("Fetching model list from Transfer Station..."):
                    try:
                        resp = requests.get(
                            f"{TS_URL}/models",
                            headers={"Authorization": f"Bearer {TS_KEY}"},
                            timeout=15
                        )
                        resp.raise_for_status()
                        all_models = sorted([m["id"] for m in resp.json().get("data", [])], key=lambda x: x.lower())
                    except Exception as e:
                        st.error(f"Failed to fetch models: {e}")
                        all_models = []
                
                chat_models = [m for m in all_models if is_chat_model(m)]
                st.info(f"Found **{len(chat_models)}** OpenAI/Claude/Gemini chat-capable models out of {len(all_models)} total. Testing each...")
                
                results = []
                progress = st.progress(0, text="Testing models...")
                
                for idx, model_id in enumerate(chat_models):
                    progress.progress((idx + 1) / len(chat_models), text=f"Testing {model_id} ({idx+1}/{len(chat_models)})...")
                    try:
                        test_resp = requests.post(
                            f"{TS_URL}/chat/completions",
                            headers={
                                "Authorization": f"Bearer {TS_KEY}",
                                "Content-Type": "application/json",
                            },
                            json={
                                "model": model_id,
                                "messages": [{"role": "user", "content": "Say hello in one word."}],
                                "max_tokens": 20,
                                "temperature": 0.1,
                                "stream": False,
                            },
                            timeout=30
                        )
                        if test_resp.status_code == 200:
                            data = test_resp.json()
                            reply = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                            if reply and len(reply.strip()) > 0:
                                results.append({"Model": model_id, "Status": "✅ Working", "Response": reply.strip()[:80]})
                            else:
                                results.append({"Model": model_id, "Status": "⚠️ Empty Response", "Response": "—"})
                        else:
                            err = ""
                            try:
                                err = test_resp.json().get("error", {}).get("message", str(test_resp.status_code))
                            except Exception:
                                err = str(test_resp.status_code)
                            results.append({"Model": model_id, "Status": "❌ Failed", "Response": err[:80]})
                    except Exception as e:
                        results.append({"Model": model_id, "Status": "❌ Error", "Response": str(e)[:80]})
                
                progress.empty()
                
                working = [r for r in results if r["Status"] == "✅ Working"]
                failed = [r for r in results if r["Status"] != "✅ Working"]
                
                st.markdown(f"""
                <div class="stat-grid" style="grid-template-columns: repeat(3, 1fr);">
                    <div class="stat-card win"><div class="stat-label">// WORKING</div><div class="stat-value">{len(working)}</div></div>
                    <div class="stat-card"><div class="stat-label">// FAILED</div><div class="stat-value">{len(failed)}</div></div>
                    <div class="stat-card"><div class="stat-label">// TOTAL TESTED</div><div class="stat-value">{len(results)}</div></div>
                </div>
                """, unsafe_allow_html=True)
                
                if working:
                    st.subheader("✅ Working Models")
                    st.dataframe(working, width='stretch')
                
                if failed:
                    with st.expander(f"❌ Failed/Empty Models ({len(failed)})", expanded=False):
                        st.dataframe(failed, width='stretch')

    # ──────────────────────────────────────────────────────────────────
    # TAB 7: DANGER ZONE
    # ──────────────────────────────────────────────────────────────────
    with main_tabs[6]:
        st.header("❌ Danger Zone")
        normal_users = {f"{u['username']} ({u['name']})": u for u in users if not u['is_admin']}
        if normal_users:
            st.warning("⚠️ Deleting a user is permanent. All chat history will be completely wiped from the database.")
            del_sel = st.selectbox("Select User to Delete", options=["-- Select User --"] + list(normal_users.keys()), key="del_sel")
            if del_sel != "-- Select User --":
                u_data = normal_users[del_sel]
                st.markdown(f"""
                <div class="arena-card" style="border-left-color: var(--red);">
                    <span style="color:var(--red);letter-spacing:2px;font-size:11px;">// CONFIRM DELETION</span><br>
                    <span style="color:var(--muted);font-size:11px;">
                        USERNAME: <span style="color:var(--yellow)">{u_data['username']}</span> · 
                        ROLE: <span style="color:var(--yellow)">{u_data['role']}</span> · 
                        NAME: <span style="color:var(--yellow)">{u_data.get('name') or '—'}</span>
                    </span>
                </div>
                """, unsafe_allow_html=True)
                if st.button(f"🗑️ Permanently Delete {u_data['username']}", type="primary"):
                    db.delete_user(u_data['id'])
                    st.success(f"{u_data['username']} was permanently deleted.")
                    st.rerun()