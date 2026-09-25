import streamlit as st
from datetime import date

import db
import auth
import calculations as calc

st.set_page_config(page_title="Weight / Water / Steps", page_icon="⚖️", layout="centered")
auth.require_login()
user_id = auth.current_user_id()
profile = db.get_profile(user_id)
if not profile or not profile.get("onboarded"):
    st.warning("Please finish onboarding first.")
    st.stop()

today = str(date.today())
st.title("⚖️ Weight, Water & More")

tabs = st.tabs(["Weight", "Water", "Steps", "Sleep (optional)", "Mood & Energy (optional)"])

# ---------- Weight ----------
with tabs[0]:
    with st.form("weight_form"):
        w = st.number_input("Today's weight (kg)", min_value=20.0, max_value=300.0, step=0.1)
        note = st.text_input("Note (optional)")
        log_w = st.form_submit_button("Log Weight")
    if log_w and w:
        db.add_weight(user_id, w, today, note)
        db.upsert_profile(user_id, weight_kg=w)
        milestones = db.get_milestones(user_id)
        for m in milestones:
            goal_direction_hit = (
                (profile["goal"] == "Weight Loss" and w <= m["weight_kg"]) or
                (profile["goal"] != "Weight Loss" and w >= m["weight_kg"])
            )
            if not m["achieved"] and goal_direction_hit:
                db.mark_milestone_achieved(m["id"])
                st.balloons()
                st.success(f"🎉 Milestone reached: {m['weight_kg']} kg!")
        st.success("Weight logged.")
        st.rerun()

    weights = db.get_weights(user_id)
    if weights:
        vals = [w_["weight_kg"] for w_ in weights]
        rolling = calc.rolling_average(vals, 7)
        st.markdown("**Weight history (with 7-day rolling average)**")
        try:
            import pandas as pd
            df = pd.DataFrame({
                "date": [w_["log_date"] for w_ in weights],
                "weight": vals,
                "7-day avg": rolling,
            }).set_index("date")
            st.line_chart(df)
        except ImportError:
            st.write(list(zip([w_["log_date"] for w_ in weights], vals)))

        st.markdown("**Edit / delete a past entry**")
        for w_ in reversed(weights[-10:]):
            with st.container(border=True):
                c1, c2, c3 = st.columns([2, 1, 1])
                c1.write(f"{w_['log_date']}: {w_['weight_kg']} kg  {('· ' + w_['note']) if w_['note'] else ''}")
                new_val = c2.number_input("kg", value=float(w_["weight_kg"]), key=f"editw_{w_['id']}", label_visibility="collapsed")
                if c3.button("Save", key=f"savew_{w_['id']}"):
                    db.update_weight_log(w_["id"], new_val, w_["note"])
                    st.rerun()

    st.markdown("**Milestones**")
    with st.form("milestone_form"):
        m_weight = st.number_input("Add a milestone weight (kg)", min_value=20.0, max_value=300.0, step=0.5)
        add_m = st.form_submit_button("Add Milestone")
    if add_m:
        db.add_milestone(user_id, m_weight)
        st.success("Milestone added.")
        st.rerun()
    for m in db.get_milestones(user_id):
        status = "✅" if m["achieved"] else "⬜"
        st.write(f"{status} {m['weight_kg']} kg")

# ---------- Water ----------
with tabs[1]:
    water_today = db.get_water_today(user_id, today)
    st.write(f"**{water_today} / {profile['water_target_ml']} ml**")
    st.progress(min(water_today / profile["water_target_ml"], 1.0) if profile["water_target_ml"] else 0)
    c1, c2, c3 = st.columns(3)
    if c1.button("+250 ml", key="w1"):
        db.add_water(user_id, 250); st.rerun()
    if c2.button("+500 ml", key="w2"):
        db.add_water(user_id, 500); st.rerun()
    if c3.button("+1 L", key="w3"):
        db.add_water(user_id, 1000); st.rerun()

# ---------- Steps ----------
with tabs[2]:
    with st.form("steps_form"):
        steps = st.number_input("Steps today", min_value=0, step=100)
        log_s = st.form_submit_button("Save Steps")
    if log_s:
        db.set_steps(user_id, steps, today)
        st.success("Steps saved.")
        st.rerun()
    recent = db.get_steps(user_id, 7)
    if recent:
        avg = round(sum(r["steps"] for r in recent) / len(recent))
        st.metric("7-day average steps", avg)
        for r in recent:
            st.write(f"- {r['log_date']}: {r['steps']} steps")

# ---------- Sleep ----------
with tabs[3]:
    with st.form("sleep_form"):
        hours = st.number_input("Hours slept last night", min_value=0.0, max_value=16.0, step=0.5)
        log_sl = st.form_submit_button("Save Sleep")
    if log_sl:
        db.set_sleep(user_id, hours, today)
        st.success("Sleep saved.")
        st.rerun()
    recent_sleep = db.get_sleep(user_id, 7)
    if recent_sleep:
        vals = [r["sleep_hours"] for r in recent_sleep if r["sleep_hours"] is not None]
        if vals:
            st.metric("7-day average sleep", f"{round(sum(vals)/len(vals), 1)} hrs")

# ---------- Mood & Energy ----------
with tabs[4]:
    with st.form("mood_form"):
        mood = st.slider("Mood (1-5)", 1, 5, 3)
        energy = st.slider("Energy (1-5)", 1, 5, 3)
        notes = st.text_area("Notes (optional)")
        log_m = st.form_submit_button("Save")
    if log_m:
        db.set_mood(user_id, mood, energy, notes, today)
        st.success("Saved.")
        st.rerun()
    st.caption("This can help you notice patterns between nutrition, exercise, sleep and energy over time — it's not a medical assessment.")
