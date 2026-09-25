import streamlit as st
from datetime import date

import db
import auth
import calculations as calc

st.set_page_config(page_title="FitTrack", page_icon="🏋️", layout="centered")
db.init_db()

# ---------- theme ----------
def apply_theme(theme: str):
    if theme == "dark":
        st.markdown(
            """<style>
            .stApp { background-color: #111418; color: #f0f0f0; }
            div[data-testid="stMetric"] { background:#1c2026; border-radius:10px; padding:10px; }
            </style>""",
            unsafe_allow_html=True,
        )


user_id = auth.current_user_id()
profile = db.get_profile(user_id) if user_id else None
apply_theme(profile["theme"] if profile else "light")

st.title("🏋️ FitTrack — Fitness & Nutrition Tracker")

# ============================================================
# NOT LOGGED IN -> login / signup
# ============================================================
if not user_id:
    tab_login, tab_signup = st.tabs(["Log In", "Sign Up"])

    with tab_login:
        with st.form("login_form"):
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Log In", use_container_width=True)
        if submitted:
            ok, msg = auth.login(u, p)
            if ok:
                st.rerun()
            else:
                st.error(msg)

    with tab_signup:
        with st.form("signup_form"):
            u2 = st.text_input("Choose a username")
            p2 = st.text_input("Choose a password", type="password")
            p2b = st.text_input("Confirm password", type="password")
            submitted2 = st.form_submit_button("Create Account", use_container_width=True)
        if submitted2:
            if p2 != p2b:
                st.error("Passwords don't match.")
            else:
                ok, msg = auth.signup(u2, p2)
                if ok:
                    st.success(msg + " Please log in.")
                else:
                    st.error(msg)
    st.stop()

# ============================================================
# LOGGED IN, NOT ONBOARDED -> onboarding wizard
# ============================================================
if not profile or not profile.get("onboarded"):
    st.subheader(f"Welcome, {st.session_state['username']}! Let's set up your plan.")

    step = st.session_state.get("onboard_step", 1)

    if step == 1:
        st.markdown("**Step 1 of 4 — What is your goal?**")
        goal = st.radio("Goal", calc.GOALS, horizontal=False)
        if st.button("Next →"):
            st.session_state["onboard_data"] = {"goal": goal}
            st.session_state["onboard_step"] = 2
            st.rerun()

    elif step == 2:
        st.markdown("**Step 2 of 4 — Personal information**")
        with st.form("personal_info"):
            name = st.text_input("Name", value=st.session_state["username"])
            age = st.number_input("Age", min_value=13, max_value=90, value=22)
            sex = st.selectbox("Sex (for calorie calculation)", ["Female", "Male"])
            height_cm = st.number_input("Height (cm)", min_value=120.0, max_value=230.0, value=165.0)
            weight_kg = st.number_input("Current weight (kg)", min_value=30.0, max_value=250.0, value=60.0)
            goal_weight_kg = st.number_input("Goal weight (kg)", min_value=30.0, max_value=250.0, value=55.0)
            next2 = st.form_submit_button("Next →")
        if next2:
            st.session_state["onboard_data"].update(
                name=name, age=age, sex=sex, height_cm=height_cm,
                weight_kg=weight_kg, goal_weight_kg=goal_weight_kg,
            )
            st.session_state["onboard_step"] = 3
            st.rerun()

    elif step == 3:
        st.markdown("**Step 3 of 4 — Activity level & timeline**")
        with st.form("activity_form"):
            activity = st.selectbox("Activity level", list(calc.ACTIVITY_MULTIPLIERS.keys()))
            timeline = st.slider("Timeline (weeks) to reach your goal", 4, 52, 12)
            next3 = st.form_submit_button("Calculate My Plan →")
        if next3:
            st.session_state["onboard_data"].update(activity_level=activity, timeline_weeks=timeline)
            st.session_state["onboard_step"] = 4
            st.rerun()

    elif step == 4:
        d = st.session_state["onboard_data"]
        targets = calc.full_targets(
            d["sex"], d["weight_kg"], d["height_cm"], d["age"], d["activity_level"],
            d["goal"], d["goal_weight_kg"],
        )
        st.markdown("**Step 4 of 4 — Your Plan**")
        c1, c2 = st.columns(2)
        c1.metric("Daily Calorie Target", f"{targets['calorie_target']} kcal")
        c2.metric("Daily Protein Target", f"{targets['protein_target']} g")
        st.caption(f"Estimated maintenance (TDEE): {targets['tdee']} kcal/day")
        st.info(
            f"Goal: **{d['goal']}** · {d['weight_kg']} kg → {d['goal_weight_kg']} kg "
            f"over ~{d['timeline_weeks']} weeks"
        )
        st.caption("You can change any of this later in Settings.")

        if st.button("✅ Start Tracking", type="primary", use_container_width=True):
            db.upsert_profile(
                user_id,
                name=d["name"], age=d["age"], sex=d["sex"], height_cm=d["height_cm"],
                weight_kg=d["weight_kg"], goal_weight_kg=d["goal_weight_kg"],
                start_weight_kg=d["weight_kg"], activity_level=d["activity_level"],
                goal=d["goal"], timeline_weeks=d["timeline_weeks"],
                calorie_target=targets["calorie_target"], protein_target=targets["protein_target"],
                water_target_ml=2500, step_target=8000, units="kg", theme="light",
                ai_enabled=1, onboarded=1,
            )
            db.add_weight(user_id, d["weight_kg"], note="Starting weight")
            for key in ("onboard_step", "onboard_data"):
                st.session_state.pop(key, None)
            st.success("Plan created! Opening your dashboard...")
            st.rerun()
    st.stop()

# ============================================================
# LOGGED IN + ONBOARDED -> welcome / navigation
# ============================================================
st.success(f"Welcome back, {profile['name'] or st.session_state['username']}! 👋")
st.write("Use the sidebar to go to your **Dashboard**, log meals/exercise/weight, or view your **Weekly Report**.")

today_meals = db.get_meals(user_id, str(date.today()))
today_cals = sum(m["calories"] for m in today_meals)
c1, c2, c3 = st.columns(3)
c1.metric("Calories today", f"{round(today_cals)} / {profile['calorie_target']}")
c2.metric("Goal", profile["goal"])
c3.metric("Current weight", f"{profile['weight_kg']} kg")

st.page_link("pages/1_Dashboard.py", label="➡️ Go to Dashboard", icon="📊")

with st.sidebar:
    st.write(f"👤 **{st.session_state['username']}**")
    if st.button("Log Out"):
        auth.logout()
        st.rerun()
