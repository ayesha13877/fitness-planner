import streamlit as st
import json
import csv
import io
from datetime import date

import db
import auth
import calculations as calc

st.set_page_config(page_title="Settings", page_icon="⚙️", layout="centered")
auth.require_login()
user_id = auth.current_user_id()
profile = db.get_profile(user_id)
if not profile or not profile.get("onboarded"):
    st.warning("Please finish onboarding first.")
    st.stop()

st.title("⚙️ Settings")

tabs = st.tabs(["Profile & Targets", "Preferences", "AI", "Export / Import", "Account"])

# ---------- Profile & targets ----------
with tabs[0]:
    with st.form("profile_settings"):
        age = st.number_input("Age", value=int(profile["age"] or 22), min_value=13, max_value=90)
        sex = st.selectbox("Sex", ["Female", "Male"], index=0 if profile["sex"] == "Female" else 1)
        height_cm = st.number_input("Height (cm)", value=float(profile["height_cm"] or 165))
        goal_weight = st.number_input("Goal weight (kg)", value=float(profile["goal_weight_kg"] or 60))
        activity = st.selectbox(
            "Activity level", list(calc.ACTIVITY_MULTIPLIERS.keys()),
            index=list(calc.ACTIVITY_MULTIPLIERS.keys()).index(profile["activity_level"])
            if profile["activity_level"] in calc.ACTIVITY_MULTIPLIERS else 0,
        )
        goal = st.selectbox("Goal", calc.GOALS, index=calc.GOALS.index(profile["goal"]) if profile["goal"] in calc.GOALS else 0)
        recalc = st.form_submit_button("Save & Recalculate Targets")
    if recalc:
        targets = calc.full_targets(sex, profile["weight_kg"], height_cm, age, activity, goal, goal_weight)
        db.upsert_profile(
            user_id, age=age, sex=sex, height_cm=height_cm, goal_weight_kg=goal_weight,
            activity_level=activity, goal=goal,
            calorie_target=targets["calorie_target"], protein_target=targets["protein_target"],
        )
        st.success(f"Updated. New targets: {targets['calorie_target']} kcal / {targets['protein_target']} g protein.")
        st.rerun()

# ---------- Preferences ----------
with tabs[1]:
    with st.form("prefs_settings"):
        units = st.selectbox("Units", ["kg", "lb"], index=0 if profile["units"] == "kg" else 1)
        theme = st.selectbox("Theme", ["light", "dark"], index=0 if profile["theme"] == "light" else 1)
        water_target = st.number_input("Daily water target (ml)", value=int(profile["water_target_ml"] or 2500), step=100)
        step_target = st.number_input("Daily step target", value=int(profile["step_target"] or 8000), step=500)
        save_prefs = st.form_submit_button("Save Preferences")
    if save_prefs:
        db.upsert_profile(user_id, units=units, theme=theme, water_target_ml=water_target, step_target=step_target)
        st.success("Preferences saved.")
        st.rerun()
    st.caption("Reminder-style prompts (e.g. “Have you logged today's meals?”) appear on your Dashboard — this app can't send real phone notifications without an external service.")

# ---------- AI ----------
with tabs[2]:
    ai_enabled = st.toggle("Enable AI features (meal analyzer, smart suggestions, assistant)", value=bool(profile["ai_enabled"]))
    key_input = st.text_input("Groq API key (optional — only needed for AI features)", value=st.session_state.get("groq_api_key", ""), type="password")
    if st.button("Save AI Settings"):
        db.upsert_profile(user_id, ai_enabled=1 if ai_enabled else 0)
        st.session_state["groq_api_key"] = key_input
        st.success("AI settings saved.")
        st.rerun()
    st.caption("Without a key, all AI-labeled buttons fall back gracefully (e.g. meal suggestions still work from your local food database).")
    st.markdown("**Analyze Food Photo** — disabled: no vision API is configured in this deployment. This feature is wired to activate automatically once one is added.")

# ---------- Export / Import ----------
with tabs[3]:
    st.markdown("**Export**")
    meals = db.get_meals(user_id)
    exercises = db.get_exercise_logs(user_id)
    weights = db.get_weights(user_id)

    def to_csv(rows):
        if not rows:
            return ""
        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
        return buf.getvalue()

    c1, c2, c3 = st.columns(3)
    c1.download_button("Meals CSV", to_csv(meals), file_name="meals.csv", disabled=not meals)
    c2.download_button("Exercise CSV", to_csv(exercises), file_name="exercise.csv", disabled=not exercises)
    c3.download_button("Weight CSV", to_csv(weights), file_name="weight.csv", disabled=not weights)

    full_backup = {
        "profile": profile,
        "meals": meals,
        "exercises": exercises,
        "weights": weights,
        "custom_foods": db.get_custom_foods(user_id),
        "saved_meals": db.get_saved_meals(user_id),
        "exported_on": str(date.today()),
    }
    st.download_button("Full JSON Backup", json.dumps(full_backup, indent=2), file_name="fittrack_backup.json")

    st.markdown("**Import backup**")
    uploaded = st.file_uploader("Upload a previously exported JSON backup", type=["json"])
    if uploaded:
        try:
            data = json.load(uploaded)
            assert "meals" in data and "exercises" in data and "weights" in data
            st.warning(f"This backup contains {len(data['meals'])} meals, {len(data['exercises'])} exercise logs, {len(data['weights'])} weight entries.")
            confirm = st.checkbox("I understand this will ADD these entries to my current data (existing entries are kept, nothing is overwritten).")
            if confirm and st.button("Import Now"):
                for m in data["meals"]:
                    db.add_meal(user_id, m["food_name"], m["calories"], m["protein"], m.get("carbs", 0), m.get("fat", 0), m["log_date"], m.get("source", "import"))
                for e in data["exercises"]:
                    db.add_exercise_log(user_id, e["exercise_name"], e.get("sets"), e.get("reps"), e.get("duration_min"), e.get("calories_est", 0), e["log_date"])
                for w in data["weights"]:
                    db.add_weight(user_id, w["weight_kg"], w["log_date"], w.get("note", ""))
                st.success("Import complete.")
                st.rerun()
        except Exception as ex:
            st.error(f"Invalid backup file: {ex}")

# ---------- Account ----------
with tabs[4]:
    st.write(f"Logged in as **{st.session_state['username']}**")
    if st.button("Log Out"):
        auth.logout()
        st.rerun()

    st.divider()
    st.markdown("**Delete Account**")
    st.caption("This permanently deletes your account and all logged data. This cannot be undone.")
    confirm_delete = st.text_input("Type DELETE to confirm")
    if st.button("Delete My Account", type="primary", disabled=confirm_delete != "DELETE"):
        db.execute("DELETE FROM users WHERE id = ?", (user_id,))
        # profiles/logs cascade via ON DELETE CASCADE (foreign_keys pragma is enabled per-connection)
        for table in ("profiles", "weight_logs", "meals", "custom_foods", "saved_meals",
                      "exercise_logs", "water_logs", "step_logs", "sleep_logs", "mood_logs", "milestones"):
            db.execute(f"DELETE FROM {table} WHERE user_id = ?", (user_id,))
        auth.logout()
        st.success("Account deleted.")
        st.rerun()
