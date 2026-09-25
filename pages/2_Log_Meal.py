import streamlit as st
from datetime import date

import db
import auth
import ai_assistant as ai
from data_food import FOOD_DB, search_food

st.set_page_config(page_title="Log Meal", page_icon="🍽️", layout="centered")
auth.require_login()
user_id = auth.current_user_id()
profile = db.get_profile(user_id)
if not profile or not profile.get("onboarded"):
    st.warning("Please finish onboarding first.")
    st.stop()

today = str(date.today())
meals_today = db.get_meals(user_id, today)
cals_today = sum(m["calories"] for m in meals_today)
protein_today = sum(m["protein"] for m in meals_today)
cal_remaining = profile["calorie_target"] - cals_today
prot_remaining = profile["protein_target"] - protein_today
api_key = st.session_state.get("groq_api_key")

st.title("🍽️ Log a Meal")
st.caption(f"Remaining today: **{round(cal_remaining)} kcal** · **{round(prot_remaining)} g protein**")

tabs = st.tabs(["Search Food", "Custom Food", "Saved Meals", "AI Meal Analyzer", "Suggest a Meal", "Build from Leftover Calories"])

# ---------- 1. Food search ----------
with tabs[0]:
    q = st.text_input("Search food", placeholder="e.g. egg")
    results = search_food(q) + db.get_custom_foods(user_id) if q else []
    for i, f in enumerate(results):
        with st.container(border=True):
            c1, c2 = st.columns([3, 1])
            c1.write(f"**{f['name']}** — {f.get('serving','custom')}  \n{round(f['calories'])} kcal · {round(f['protein'])} g protein")
            if c2.button("Add to Meal", key=f"add_search_{i}"):
                db.add_meal(user_id, f["name"], f["calories"], f["protein"], f.get("carbs", 0), f.get("fat", 0), today, source="database")
                st.success(f"Added {f['name']}")
                st.rerun()
    if q and not results:
        st.info("No matches. Try Custom Food to add it yourself.")

# ---------- 2. Custom food ----------
with tabs[1]:
    with st.form("custom_food_form"):
        name = st.text_input("Food name")
        serving = st.text_input("Serving size", placeholder="e.g. 100g")
        calories = st.number_input("Calories", min_value=0.0, step=1.0)
        protein = st.number_input("Protein (g)", min_value=0.0, step=1.0)
        carbs = st.number_input("Carbohydrates (g) — optional", min_value=0.0, step=1.0)
        fat = st.number_input("Fat (g) — optional", min_value=0.0, step=1.0)
        c1, c2 = st.columns(2)
        save_only = c1.form_submit_button("Save to My Foods")
        save_and_add = c2.form_submit_button("Save & Add to Today")
    if save_only or save_and_add:
        if not name:
            st.error("Name is required.")
        else:
            db.add_custom_food(user_id, name, serving, calories, protein, carbs, fat)
            st.success(f"Saved '{name}' to your food database.")
            if save_and_add:
                db.add_meal(user_id, name, calories, protein, carbs, fat, today, source="custom")
                st.success("Added to today's meals.")
            st.rerun()

    st.markdown("**Your custom foods**")
    for f in db.get_custom_foods(user_id):
        st.write(f"- {f['name']} ({f['serving']}) — {round(f['calories'])} kcal, {round(f['protein'])} g protein")

# ---------- 3. Saved meals (recipes) ----------
with tabs[2]:
    st.markdown("Create a saved meal (recipe) from ingredients already in your food database.")
    with st.form("recipe_form"):
        recipe_name = st.text_input("Meal name", placeholder="e.g. Chicken Roti Dinner")
        ingredient_query = st.text_input("Search ingredients to add (search food, then list below)")
        st.caption("Tip: search & note calories/protein for each ingredient, then enter the totals below.")
        total_cal = st.number_input("Total calories", min_value=0.0, step=1.0)
        total_prot = st.number_input("Total protein (g)", min_value=0.0, step=1.0)
        total_carb = st.number_input("Total carbs (g)", min_value=0.0, step=1.0)
        total_fat = st.number_input("Total fat (g)", min_value=0.0, step=1.0)
        ingredients_text = st.text_area("Ingredients list (one per line)", placeholder="2 roti\nChicken curry\nSalad\nYogurt")
        save_recipe = st.form_submit_button("Save Meal")
    if save_recipe:
        if not recipe_name:
            st.error("Meal name is required.")
        else:
            db.add_saved_meal(user_id, recipe_name, total_cal, total_prot, total_carb, total_fat, ingredients_text)
            st.success(f"Saved meal '{recipe_name}'.")
            st.rerun()

    st.markdown("**Your saved meals**")
    for sm in db.get_saved_meals(user_id):
        with st.container(border=True):
            c1, c2 = st.columns([3, 1])
            c1.write(f"**{sm['name']}** — {round(sm['calories'])} kcal · {round(sm['protein'])} g protein\n\n{sm['ingredients']}")
            if c2.button("Add to Today", key=f"add_recipe_{sm['id']}"):
                db.add_meal(user_id, sm["name"], sm["calories"], sm["protein"], sm["carbs"], sm["fat"], today, source="saved_meal")
                st.success(f"Added {sm['name']}")
                st.rerun()

# ---------- 4. AI meal analyzer ----------
with tabs[3]:
    if not profile.get("ai_enabled"):
        st.info("AI features are turned off. Enable them in Settings.")
    else:
        desc = st.text_area("Describe what you ate", placeholder="I ate 2 rotis, one bowl chicken curry and a glass of lassi.")
        if st.button("Estimate Nutrition"):
            if not desc.strip():
                st.error("Please describe your meal.")
            else:
                with st.spinner("Estimating..."):
                    result = ai.analyze_meal_text(desc, api_key)
                if not result["ok"]:
                    st.warning(result["error"] + " (Add a Groq API key in Settings to enable this.)")
                else:
                    st.session_state["ai_estimate"] = result["estimate"]
                    st.session_state["ai_estimate_desc"] = desc

        if "ai_estimate" in st.session_state:
            est = st.session_state["ai_estimate"]
            st.warning("⚠️ AI estimate — actual values may vary depending on recipe and portion size. Review before saving.")
            with st.form("confirm_ai_estimate"):
                c1, c2 = st.columns(2)
                cal = c1.number_input("Calories", value=float(est.get("calories", 0)))
                prot = c2.number_input("Protein (g)", value=float(est.get("protein", 0)))
                c3, c4 = st.columns(2)
                carb = c3.number_input("Carbs (g)", value=float(est.get("carbs", 0)))
                fat = c4.number_input("Fat (g)", value=float(est.get("fat", 0)))
                confirm = st.form_submit_button("Confirm & Save to Today")
            if confirm:
                db.add_meal(user_id, st.session_state.get("ai_estimate_desc", "AI-estimated meal"), cal, prot, carb, fat, today, source="ai_estimate")
                st.success("Saved.")
                del st.session_state["ai_estimate"]
                st.rerun()

# ---------- 5. Smart meal suggestion ----------
with tabs[4]:
    st.write(f"Calories remaining: **{round(cal_remaining)} kcal**  ·  Protein remaining: **{round(prot_remaining)} g**")
    if st.button("Suggest a meal for me"):
        result = ai.suggest_meal(cal_remaining, prot_remaining, profile["goal"], FOOD_DB, api_key if profile.get("ai_enabled") else None)
        if result["text"]:
            st.success(result["text"])
        if result["candidates"]:
            st.markdown("**Options from your food database:**")
            for f in result["candidates"]:
                st.write(f"- {f['name']} — {f['calories']} kcal, {f['protein']} g protein ({f['serving']})")
        else:
            st.info("No great matches found — try logging a smaller earlier meal, or check Search Food for more options.")

# ---------- 6. Leftover calorie meal builder ----------
with tabs[5]:
    with st.form("leftover_builder"):
        max_cal = st.number_input("Maximum calories", min_value=0, value=max(int(cal_remaining), 0), step=10)
        min_prot = st.number_input("Minimum protein (g)", min_value=0, value=20, step=5)
        build = st.form_submit_button("Build Meal")
    if build:
        combos = []
        sorted_foods = sorted(FOOD_DB, key=lambda f: -f["protein"] / max(f["calories"], 1))
        running_cal, running_prot, picked = 0, 0, []
        for f in sorted_foods:
            if running_cal + f["calories"] <= max_cal:
                picked.append(f)
                running_cal += f["calories"]
                running_prot += f["protein"]
            if running_prot >= min_prot:
                break
        if picked:
            st.success(f"Suggested combo: {running_cal} kcal, {round(running_prot)} g protein")
            for f in picked:
                st.write(f"- {f['name']} ({f['serving']}) — {f['calories']} kcal, {f['protein']} g protein")
            if st.button("Add all to today's meals"):
                for f in picked:
                    db.add_meal(user_id, f["name"], f["calories"], f["protein"], f.get("carbs", 0), f.get("fat", 0), today, source="leftover_builder")
                st.success("Added.")
                st.rerun()
        else:
            st.info("Couldn't fit a combo within that calorie budget — try raising the max calories.")

st.divider()
st.subheader("Today's Logged Meals")
for m in meals_today:
    with st.container(border=True):
        c1, c2 = st.columns([4, 1])
        c1.write(f"**{m['food_name']}** — {round(m['calories'])} kcal · {round(m['protein'])} g protein  \n_source: {m['source']}_")
        if c2.button("🗑️", key=f"del_meal_{m['id']}"):
            db.delete_meal(m["id"])
            st.rerun()
