# FitTrack — Personal Fitness & Nutrition Tracker

## Run it
```
pip install -r requirements.txt
streamlit run app.py
```
Opens at http://localhost:8501

## First use
1. Sign up → log in
2. Onboarding wizard: goal → personal info → activity level/timeline → your calculated plan
3. Dashboard is your home base; sidebar has all other pages

## What's implemented
Auth (bcrypt hashed passwords, session-based), full onboarding, calorie/protein
targets (Mifflin-St Jeor BMR + activity multiplier), meal logging (food search,
custom foods, saved meals/recipes, AI meal analyzer, smart suggestion, leftover-
calorie builder), exercise logging (library + filters, rule-based workout
generator, manual log), weight/water/steps/sleep/mood logging, dashboard with
progress bars + streaks, weekly report with factual insights + charts, editable
history for any past day, CSV/JSON export + JSON import, settings (targets,
units, theme, AI key), account deletion. SQLite is the single source of truth;
AI (optional, via Groq — set a key in Settings) only ever proposes estimates
the user must confirm before they're saved.

## Known simplifications (by design, per spec §39/40)
- Photo meal detection: UI stub only — wire in a vision API to activate.
- Dark mode: basic CSS override, not a full design system.
- Notifications: in-app prompts only (no real push — Streamlit can't do that
  without an external service).
- Workout generator: rule-based (filters + balancing), not ML.
