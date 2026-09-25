import streamlit as st
from datetime import date, timedelta

import db
import auth

st.set_page_config(page_title="Weekly Report", page_icon="📈", layout="centered")
auth.require_login()
user_id = auth.current_user_id()
profile = db.get_profile(user_id)
if not profile or not profile.get("onboarded"):
    st.warning("Please finish onboarding first.")
    st.stop()

st.title("📈 Weekly Report")

end = date.today()
start = end - timedelta(days=6)
date_range = [str(start + timedelta(days=i)) for i in range(7)]

all_meals = db.get_meals(user_id)
week_meals = [m for m in all_meals if m["log_date"] in date_range]
all_exercise = db.get_exercise_logs(user_id)
week_exercise = [e for e in all_exercise if e["log_date"] in date_range]
all_weights = db.get_weights(user_id)
week_weights = [w for w in all_weights if w["log_date"] in date_range]

daily_cals = {}
daily_prot = {}
for m in week_meals:
    daily_cals[m["log_date"]] = daily_cals.get(m["log_date"], 0) + m["calories"]
    daily_prot[m["log_date"]] = daily_prot.get(m["log_date"], 0) + m["protein"]

logged_days = set(daily_cals.keys()) | {e["log_date"] for e in week_exercise}

st.caption(f"{start} → {end}")

if not week_meals and not week_exercise and not week_weights:
    st.info("Not enough data yet this week. Log a few meals, workouts or weigh-ins to see your report.")
    st.stop()

# ---------- factual summary ----------
if daily_cals:
    avg_cal = round(sum(daily_cals.values()) / len(daily_cals))
    st.write(f"Average calorie intake was **{avg_cal} kcal/day** (across {len(daily_cals)} logged day(s)).")
if daily_prot:
    avg_prot = round(sum(daily_prot.values()) / len(daily_prot))
    st.write(f"Average protein intake was **{avg_prot} g/day**.")

exercise_days = {e["log_date"] for e in week_exercise}
st.write(f"You logged exercise on **{len(exercise_days)} of 7** days this week.")

if week_weights:
    vals = [w["weight_kg"] for w in week_weights]
    st.write(f"Your weight entries ranged from **{min(vals)}–{max(vals)} kg** this week.")

st.divider()

# ---------- patterns ----------
st.subheader("Patterns")
if daily_cals:
    highest_cal_day = max(daily_cals, key=daily_cals.get)
    lowest_cal_day = min(daily_cals, key=daily_cals.get)
    st.write(f"- Highest-calorie day: **{highest_cal_day}** ({round(daily_cals[highest_cal_day])} kcal)")
    st.write(f"- Lowest-calorie day: **{lowest_cal_day}** ({round(daily_cals[lowest_cal_day])} kcal)")
if daily_prot:
    highest_prot_day = max(daily_prot, key=daily_prot.get)
    st.write(f"- Highest-protein day: **{highest_prot_day}** ({round(daily_prot[highest_prot_day])} g)")
if week_exercise:
    ex_minutes = {}
    for e in week_exercise:
        ex_minutes[e["log_date"]] = ex_minutes.get(e["log_date"], 0) + (e["duration_min"] or 0)
    most_active_day = max(ex_minutes, key=ex_minutes.get)
    st.write(f"- Most active day: **{most_active_day}** ({round(ex_minutes[most_active_day])} min)")

st.caption("These are factual observations from your logs, not conclusions about *why* your weight changed.")

st.divider()

# ---------- charts ----------
st.subheader("This Week's Calories")
try:
    import pandas as pd
    cal_series = {d: daily_cals.get(d, 0) for d in date_range}
    df = pd.DataFrame({"date": list(cal_series.keys()), "calories": list(cal_series.values())}).set_index("date")
    st.bar_chart(df)
except ImportError:
    st.write(daily_cals)

st.subheader("Weekly Calendar")
cols = st.columns(7)
day_labels = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]
for i, d in enumerate(date_range):
    mark = "✅" if d in logged_days else "—"
    cols[i].write(f"**{day_labels[i]}**\n\n{mark}")
