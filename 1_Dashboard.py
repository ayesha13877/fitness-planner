import streamlit as st
from datetime import date, timedelta

import db
import auth
import calculations as calc

st.set_page_config(page_title="Dashboard", page_icon="📊", layout="centered")
auth.require_login()
user_id = auth.current_user_id()
profile = db.get_profile(user_id)
if not profile or not profile.get("onboarded"):
    st.warning("Please finish onboarding first.")
    st.stop()

today = str(date.today())
st.title("📊 Dashboard")

# ---------- today's numbers ----------
meals_today = db.get_meals(user_id, today)
cals_today = sum(m["calories"] for m in meals_today)
protein_today = sum(m["protein"] for m in meals_today)
exercises_today = db.get_exercise_logs(user_id, today)
water_today = db.get_water_today(user_id, today)

cal_target = profile["calorie_target"]
prot_target = profile["protein_target"]
water_target = profile["water_target_ml"]

# ---------- streaks ----------
logged_dates = set(db.get_logged_dates(user_id))
def compute_streak(dates_set):
    streak = 0
    d = date.today()
    while str(d) in dates_set:
        streak += 1
        d -= timedelta(days=1)
    return streak

logging_streak = compute_streak(logged_dates)
exercise_dates = {e["log_date"] for e in db.get_exercise_logs(user_id)}
exercise_streak = compute_streak(exercise_dates)

# ---------- top metrics ----------
weights = db.get_weights(user_id)
current_weight = weights[-1]["weight_kg"] if weights else profile["weight_kg"]
weight_remaining = round(current_weight - profile["goal_weight_kg"], 1)

r1c1, r1c2, r1c3, r1c4 = st.columns(4)
r1c1.metric("Current weight", f"{current_weight} kg")
r1c2.metric("Goal weight", f"{profile['goal_weight_kg']} kg")
r1c3.metric("Remaining", f"{abs(weight_remaining)} kg")
r1c4.metric("🔥 Logging streak", f"{logging_streak} day(s)")

st.divider()

# ---------- calorie budget ----------
st.subheader("Calorie Budget")
remaining_cals = cal_target - cals_today
st.progress(min(cals_today / cal_target, 1.0) if cal_target else 0)
st.write(f"**{round(cals_today)} / {cal_target} kcal**")
if remaining_cals < 0:
    st.info(f"Daily target exceeded by {abs(round(remaining_cals))} kcal. That happens — tomorrow's a fresh count.")
else:
    st.caption(f"{round(remaining_cals)} kcal remaining today")

# ---------- protein ----------
st.subheader("Protein Tracker")
remaining_protein = prot_target - protein_today
st.progress(min(protein_today / prot_target, 1.0) if prot_target else 0)
st.write(f"**{round(protein_today)} / {prot_target} g**")
if remaining_protein > 0:
    st.caption(f"You have approximately {round(remaining_protein)} g protein remaining today.")
    if remaining_protein > 15:
        st.caption("Suggestions: boiled eggs, grilled chicken, daal, yogurt, or a whey shake.")

# ---------- goal progress ----------
st.subheader("Goal Progress")
pct = calc.goal_progress_pct(profile["start_weight_kg"] or current_weight, current_weight, profile["goal_weight_kg"])
st.progress(pct / 100)
st.write(f"START {profile['start_weight_kg']} kg → CURRENT {current_weight} kg → GOAL {profile['goal_weight_kg']} kg  ·  **{pct}%**")

st.divider()

# ---------- water ----------
st.subheader("💧 Water")
st.progress(min(water_today / water_target, 1.0) if water_target else 0)
st.write(f"{water_today} / {water_target} ml")
wc1, wc2, wc3 = st.columns(3)
if wc1.button("+250 ml"):
    db.add_water(user_id, 250); st.rerun()
if wc2.button("+500 ml"):
    db.add_water(user_id, 500); st.rerun()
if wc3.button("+1 L"):
    db.add_water(user_id, 1000); st.rerun()

st.divider()

# ---------- today's exercise ----------
st.subheader("🏃 Today's Exercise")
if exercises_today:
    for e in exercises_today:
        st.write(f"- {e['exercise_name']} ({e['sets'] or '-'} sets × {e['reps'] or '-'} reps, {e['duration_min'] or '-'} min)")
    st.caption(f"🔥 Exercise streak: {exercise_streak} day(s)")
else:
    st.caption("No exercise logged yet today.")

st.divider()

# ---------- quick actions ----------
st.subheader("Quick Actions")
qc1, qc2, qc3 = st.columns(3)
qc1.page_link("pages/2_Log_Meal.py", label="🍽️ Add Meal")
qc2.page_link("pages/3_Log_Exercise.py", label="🏋️ Add Exercise")
qc3.page_link("pages/4_Weight_Water_Steps.py", label="⚖️ Log Weight")
