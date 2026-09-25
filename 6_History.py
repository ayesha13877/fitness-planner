import streamlit as st
from datetime import date

import db
import auth

st.set_page_config(page_title="History", page_icon="🗓️", layout="centered")
auth.require_login()
user_id = auth.current_user_id()
profile = db.get_profile(user_id)
if not profile or not profile.get("onboarded"):
    st.warning("Please finish onboarding first.")
    st.stop()

st.title("🗓️ History")

picked_date = st.date_input("Select a date", value=date.today())
d_str = str(picked_date)

meals = db.get_meals(user_id, d_str)
exercises = db.get_exercise_logs(user_id, d_str)
weights = [w for w in db.get_weights(user_id) if w["log_date"] == d_str]
water = db.get_water_today(user_id, d_str)

st.subheader(f"Meals — {d_str}")
if meals:
    total_cal = sum(m["calories"] for m in meals)
    total_prot = sum(m["protein"] for m in meals)
    st.caption(f"Total: {round(total_cal)} kcal · {round(total_prot)} g protein")
    for m in meals:
        with st.container(border=True):
            c1, c2 = st.columns([3, 1])
            with c1:
                new_name = st.text_input("Food", value=m["food_name"], key=f"name_{m['id']}", label_visibility="collapsed")
                nc1, nc2 = st.columns(2)
                new_cal = nc1.number_input("kcal", value=float(m["calories"]), key=f"cal_{m['id']}")
                new_prot = nc2.number_input("protein g", value=float(m["protein"]), key=f"prot_{m['id']}")
            with c2:
                if st.button("Save", key=f"savem_{m['id']}"):
                    db.update_meal(m["id"], food_name=new_name, calories=new_cal, protein=new_prot)
                    st.rerun()
                if st.button("Delete", key=f"delm_{m['id']}"):
                    db.delete_meal(m["id"])
                    st.rerun()
else:
    st.caption("No meals logged this day.")
    with st.form(f"add_past_meal_{d_str}"):
        name = st.text_input("Food name")
        cal = st.number_input("Calories", min_value=0.0)
        prot = st.number_input("Protein (g)", min_value=0.0)
        add = st.form_submit_button("Add meal for this date")
    if add and name:
        db.add_meal(user_id, name, cal, prot, log_date=d_str)
        st.rerun()

st.subheader(f"Exercise — {d_str}")
if exercises:
    for e in exercises:
        c1, c2 = st.columns([3, 1])
        c1.write(f"{e['exercise_name']} — {e['sets'] or '-'} sets × {e['reps'] or '-'} reps, {e['duration_min'] or '-'} min")
        if c2.button("Delete", key=f"dele_{e['id']}"):
            db.delete_exercise_log(e["id"])
            st.rerun()
else:
    st.caption("No exercise logged this day.")
    with st.form(f"add_past_ex_{d_str}"):
        ename = st.text_input("Exercise name")
        add_e = st.form_submit_button("Add exercise for this date")
    if add_e and ename:
        db.add_exercise_log(user_id, ename, log_date=d_str)
        st.rerun()

st.subheader(f"Weight — {d_str}")
if weights:
    for w in weights:
        c1, c2 = st.columns([3, 1])
        new_w = c1.number_input("kg", value=float(w["weight_kg"]), key=f"histw_{w['id']}")
        if c2.button("Save", key=f"savehw_{w['id']}"):
            db.update_weight_log(w["id"], new_w, w["note"])
            st.rerun()
else:
    st.caption("No weight logged this day.")

st.subheader(f"Water — {d_str}")
st.write(f"{water} ml logged")

st.caption("Any edits here automatically feed into the Weekly Report — nothing to recalculate manually.")
