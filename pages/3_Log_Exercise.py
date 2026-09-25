import streamlit as st
from datetime import date

import db
import auth
from data_exercise import EXERCISE_DB, filter_exercises, generate_workout

st.set_page_config(page_title="Log Exercise", page_icon="🏋️", layout="centered")
auth.require_login()
user_id = auth.current_user_id()
profile = db.get_profile(user_id)
if not profile or not profile.get("onboarded"):
    st.warning("Please finish onboarding first.")
    st.stop()

today = str(date.today())
st.title("🏋️ Log Exercise")

tabs = st.tabs(["Exercise Library", "Generate Workout", "Manual Log"])

# ---------- 1. Library ----------
with tabs[0]:
    c1, c2, c3 = st.columns(3)
    location = c1.selectbox("Location", ["Any", "Home", "Gym"])
    difficulty = c2.selectbox("Difficulty", ["Any", "Beginner", "Intermediate", "Advanced"])
    equipment = c3.selectbox("Equipment", ["Any", "No equipment"])
    results = filter_exercises(location, difficulty, equipment)
    for i, e in enumerate(results):
        with st.container(border=True):
            c1, c2 = st.columns([3, 1])
            c1.write(
                f"**{e['name']}** — {e['muscle_group']} · {e['difficulty']} · {e['equipment']}  \n"
                f"{e['sets']} sets × {e['reps'] or '-'} reps, ~{e['duration_min']} min"
            )
            if c2.button("Log this", key=f"log_lib_{i}"):
                cal_est = e["duration_min"] * e["cal_per_min"]
                db.add_exercise_log(user_id, e["name"], e["sets"], e["reps"], e["duration_min"], cal_est, today)
                st.success(f"Logged {e['name']}")
                st.rerun()

# ---------- 2. Workout generator ----------
with tabs[1]:
    with st.form("workout_gen"):
        goal_choice = st.selectbox("Goal", ["Weight Loss", "Muscle Building", "Maintenance"], index=0)
        minutes = st.slider("Available time (minutes)", 10, 60, 30)
        eq = st.selectbox("Equipment", ["No equipment", "Any"])
        diff = st.selectbox("Difficulty", ["Any", "Beginner", "Intermediate", "Advanced"])
        gen = st.form_submit_button("Generate Workout")
    if gen:
        st.session_state["generated_workout"] = generate_workout(goal_choice, minutes, eq, diff)

    if "generated_workout" in st.session_state:
        workout = st.session_state["generated_workout"]
        st.markdown("**Your generated workout:**")
        for i, e in enumerate(list(workout)):
            with st.container(border=True):
                c1, c2, c3 = st.columns([3, 1, 1])
                c1.write(f"**{e['name']}** — {e['muscle_group']}  \n{e['sets']} sets × {e['reps'] or '-'} reps, ~{e['duration_min']} min")
                if c2.button("Remove", key=f"rm_{i}"):
                    workout.pop(i)
                    st.rerun()
        if st.button("Save Full Workout to Today"):
            for e in workout:
                cal_est = e["duration_min"] * e["cal_per_min"]
                db.add_exercise_log(user_id, e["name"], e["sets"], e["reps"], e["duration_min"], cal_est, today)
            st.success("Workout saved.")
            del st.session_state["generated_workout"]
            st.rerun()
        st.caption("Rest & recovery matter too — you don't need an intense workout every day.")

# ---------- 3. Manual log ----------
with tabs[2]:
    with st.form("manual_exercise"):
        name = st.text_input("Exercise name")
        sets = st.number_input("Sets", min_value=0, step=1)
        reps = st.number_input("Reps", min_value=0, step=1)
        duration = st.number_input("Duration (minutes)", min_value=0.0, step=1.0)
        cal_est = st.number_input("Estimated calories burned (optional)", min_value=0.0, step=1.0)
        add = st.form_submit_button("Log Exercise")
    if add:
        if not name:
            st.error("Name is required.")
        else:
            db.add_exercise_log(user_id, name, sets, reps, duration, cal_est, today)
            st.success(f"Logged {name}")
            st.rerun()

st.divider()
st.subheader("Today's Exercise Log")
for e in db.get_exercise_logs(user_id, today):
    with st.container(border=True):
        c1, c2 = st.columns([4, 1])
        c1.write(f"**{e['exercise_name']}** — {e['sets'] or '-'} sets × {e['reps'] or '-'} reps, {e['duration_min'] or '-'} min")
        if c2.button("🗑️", key=f"del_ex_{e['id']}"):
            db.delete_exercise_log(e["id"])
            st.rerun()
