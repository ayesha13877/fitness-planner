import streamlit as st
from datetime import date

import db
import auth
import ai_assistant as ai

st.set_page_config(page_title="AI Assistant", page_icon="🤖", layout="centered")
auth.require_login()
user_id = auth.current_user_id()
profile = db.get_profile(user_id)
if not profile or not profile.get("onboarded"):
    st.warning("Please finish onboarding first.")
    st.stop()

st.title("🤖 AI Fitness Assistant")
st.caption("Answers use your live stats but nothing said here is saved as a log — add anything useful yourself via the logging pages.")

api_key = st.session_state.get("groq_api_key")

if not profile.get("ai_enabled"):
    st.info("AI features are turned off. Enable them in Settings.")
    st.stop()

if not ai.ai_available(api_key):
    st.warning(
        "No Groq API key configured, so the assistant can't respond right now. "
        "Add a key in Settings to enable this (the rest of the app works fine without it)."
    )

today = str(date.today())
meals_today = db.get_meals(user_id, today)
cals_today = sum(m["calories"] for m in meals_today)
protein_today = sum(m["protein"] for m in meals_today)
context = {
    "goal": profile["goal"],
    "calorie_target": profile["calorie_target"],
    "calories_remaining": round(profile["calorie_target"] - cals_today),
    "protein_target": profile["protein_target"],
    "protein_remaining": round(profile["protein_target"] - protein_today),
    "current_weight_kg": profile["weight_kg"],
    "goal_weight_kg": profile["goal_weight_kg"],
}

st.caption(
    f"Context in use → goal: {context['goal']}, "
    f"calories remaining: {context['calories_remaining']}, "
    f"protein remaining: {context['protein_remaining']} g"
)

if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []

for role, text in st.session_state["chat_history"]:
    with st.chat_message(role):
        st.write(text)

q = st.chat_input("Ask about meals, workouts, or your progress...")
if q:
    st.session_state["chat_history"].append(("user", q))
    with st.chat_message("user"):
        st.write(q)
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            result = ai.ask_assistant(q, context, api_key)
        answer = result["answer"] or result["error"]
        st.write(answer)
    st.session_state["chat_history"].append(("assistant", answer))

st.caption("Example questions: “What can I eat for dinner?”, “How can I increase protein?”, “Give me a 30-minute home workout.”")
