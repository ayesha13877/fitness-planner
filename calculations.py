"""
Core fitness math: BMR (Mifflin-St Jeor), TDEE, calorie & protein targets,
goal-progress percentage. Kept separate from the UI so it's easy to unit test.
"""

ACTIVITY_MULTIPLIERS = {
    "Sedentary (little/no exercise)": 1.2,
    "Lightly active (1-3 days/week)": 1.375,
    "Moderately active (3-5 days/week)": 1.55,
    "Very active (6-7 days/week)": 1.725,
    "Extremely active (physical job/2x training)": 1.9,
}

GOALS = ["Weight Loss", "Weight Gain", "Muscle Building", "Maintenance"]


def bmr_mifflin(sex: str, weight_kg: float, height_cm: float, age: int) -> float:
    base = 10 * weight_kg + 6.25 * height_cm - 5 * age
    return base + 5 if sex == "Male" else base - 161


def tdee(bmr: float, activity_level: str) -> float:
    return bmr * ACTIVITY_MULTIPLIERS.get(activity_level, 1.2)


def calorie_target(tdee_val: float, goal: str, weight_kg: float, goal_weight_kg: float) -> int:
    """
    Weight Loss -> ~15% deficit (capped so it never drops below a safe floor).
    Weight Gain / Muscle Building -> ~12% surplus.
    Maintenance -> TDEE.
    """
    if goal == "Weight Loss":
        target = tdee_val * 0.85
        floor = 1200 if weight_kg and weight_kg < 60 else 1500
        target = max(target, floor)
    elif goal in ("Weight Gain", "Muscle Building"):
        target = tdee_val * 1.12
    else:
        target = tdee_val
    return round(target)


def protein_target(weight_kg: float, goal: str) -> int:
    """Grams of protein/day. Higher end for muscle building / weight loss (satiety + muscle retention)."""
    if goal == "Muscle Building":
        g_per_kg = 2.0
    elif goal == "Weight Loss":
        g_per_kg = 1.8
    elif goal == "Weight Gain":
        g_per_kg = 1.6
    else:
        g_per_kg = 1.4
    return round(weight_kg * g_per_kg)


def goal_progress_pct(start_weight: float, current_weight: float, goal_weight: float) -> float:
    """Handles both weight-loss and weight-gain directions correctly."""
    if start_weight == goal_weight:
        return 100.0
    total_change_needed = goal_weight - start_weight
    change_so_far = current_weight - start_weight
    pct = (change_so_far / total_change_needed) * 100
    return max(0.0, min(100.0, round(pct, 1)))


def rolling_average(values: list, window: int = 7) -> list:
    """Simple trailing rolling average; returns list same length as input (None where not enough data)."""
    out = []
    for i in range(len(values)):
        window_vals = values[max(0, i - window + 1): i + 1]
        out.append(round(sum(window_vals) / len(window_vals), 2))
    return out


def full_targets(sex, weight_kg, height_cm, age, activity_level, goal, goal_weight_kg):
    bmr = bmr_mifflin(sex, weight_kg, height_cm, age)
    tdee_val = tdee(bmr, activity_level)
    cal_target = calorie_target(tdee_val, goal, weight_kg, goal_weight_kg)
    prot_target = protein_target(weight_kg, goal)
    return {
        "bmr": round(bmr),
        "tdee": round(tdee_val),
        "calorie_target": cal_target,
        "protein_target": prot_target,
    }
