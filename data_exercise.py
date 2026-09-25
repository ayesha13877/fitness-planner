"""
Exercise library + a simple rule-based workout generator (no ML needed).
"""

EXERCISE_DB = [
    {"name": "Push-ups", "muscle_group": "Chest", "difficulty": "Beginner", "equipment": "None", "location": "Home", "sets": 3, "reps": 12, "duration_min": 6, "cal_per_min": 7},
    {"name": "Bodyweight squats", "muscle_group": "Legs", "difficulty": "Beginner", "equipment": "None", "location": "Home", "sets": 3, "reps": 15, "duration_min": 6, "cal_per_min": 8},
    {"name": "Plank", "muscle_group": "Core", "difficulty": "Beginner", "equipment": "None", "location": "Home", "sets": 3, "reps": None, "duration_min": 3, "cal_per_min": 5},
    {"name": "Lunges", "muscle_group": "Legs", "difficulty": "Beginner", "equipment": "None", "location": "Home", "sets": 3, "reps": 12, "duration_min": 6, "cal_per_min": 7},
    {"name": "Jumping jacks", "muscle_group": "Full body / Cardio", "difficulty": "Beginner", "equipment": "None", "location": "Home", "sets": 3, "reps": 30, "duration_min": 5, "cal_per_min": 9},
    {"name": "Burpees", "muscle_group": "Full body / Cardio", "difficulty": "Intermediate", "equipment": "None", "location": "Home", "sets": 3, "reps": 10, "duration_min": 6, "cal_per_min": 10},
    {"name": "Mountain climbers", "muscle_group": "Core / Cardio", "difficulty": "Intermediate", "equipment": "None", "location": "Home", "sets": 3, "reps": 20, "duration_min": 5, "cal_per_min": 9},
    {"name": "Glute bridges", "muscle_group": "Glutes", "difficulty": "Beginner", "equipment": "None", "location": "Home", "sets": 3, "reps": 15, "duration_min": 5, "cal_per_min": 6},
    {"name": "Dumbbell rows", "muscle_group": "Back", "difficulty": "Intermediate", "equipment": "Dumbbells", "location": "Home", "sets": 3, "reps": 12, "duration_min": 6, "cal_per_min": 7},
    {"name": "Dumbbell shoulder press", "muscle_group": "Shoulders", "difficulty": "Intermediate", "equipment": "Dumbbells", "location": "Home", "sets": 3, "reps": 10, "duration_min": 6, "cal_per_min": 7},
    {"name": "Bench press", "muscle_group": "Chest", "difficulty": "Intermediate", "equipment": "Barbell", "location": "Gym", "sets": 4, "reps": 8, "duration_min": 8, "cal_per_min": 6},
    {"name": "Deadlift", "muscle_group": "Back / Legs", "difficulty": "Advanced", "equipment": "Barbell", "location": "Gym", "sets": 4, "reps": 6, "duration_min": 10, "cal_per_min": 8},
    {"name": "Lat pulldown", "muscle_group": "Back", "difficulty": "Intermediate", "equipment": "Machine", "location": "Gym", "sets": 3, "reps": 10, "duration_min": 6, "cal_per_min": 6},
    {"name": "Leg press", "muscle_group": "Legs", "difficulty": "Intermediate", "equipment": "Machine", "location": "Gym", "sets": 4, "reps": 10, "duration_min": 8, "cal_per_min": 7},
    {"name": "Treadmill jog", "muscle_group": "Cardio", "difficulty": "Beginner", "equipment": "Treadmill", "location": "Gym", "sets": 1, "reps": None, "duration_min": 20, "cal_per_min": 10},
    {"name": "Brisk walking", "muscle_group": "Cardio", "difficulty": "Beginner", "equipment": "None", "location": "Home", "sets": 1, "reps": None, "duration_min": 30, "cal_per_min": 5},
    {"name": "Yoga flow (mobility)", "muscle_group": "Mobility", "difficulty": "Beginner", "equipment": "Mat", "location": "Home", "sets": 1, "reps": None, "duration_min": 20, "cal_per_min": 3},
    {"name": "Cycling", "muscle_group": "Cardio / Legs", "difficulty": "Beginner", "equipment": "Bicycle", "location": "Gym", "sets": 1, "reps": None, "duration_min": 25, "cal_per_min": 8},
]


def filter_exercises(location=None, difficulty=None, equipment=None):
    results = EXERCISE_DB
    if location and location != "Any":
        results = [e for e in results if e["location"] == location]
    if difficulty and difficulty != "Any":
        results = [e for e in results if e["difficulty"] == difficulty]
    if equipment == "No equipment":
        results = [e for e in results if e["equipment"] == "None"]
    return results


def generate_workout(goal: str, minutes: int, equipment: str, difficulty: str):
    """
    Simple rule-based generator: pick exercises matching filters until the
    time budget is used, mixing muscle groups for a balanced session.
    """
    pool = filter_exercises(
        location="Home" if equipment == "No equipment" else None,
        difficulty=None if difficulty == "Any" else difficulty,
        equipment=equipment,
    )
    if goal == "Muscle Building":
        pool = sorted(pool, key=lambda e: e["muscle_group"] not in ("Chest", "Back", "Legs", "Shoulders", "Glutes"))
    elif goal in ("Weight Loss",):
        pool = sorted(pool, key=lambda e: "Cardio" not in e["muscle_group"])

    workout = []
    time_used = 0
    seen_groups = set()
    for ex in pool:
        if time_used >= minutes:
            break
        if ex["muscle_group"] in seen_groups and len(workout) >= 3:
            continue
        workout.append(ex)
        seen_groups.add(ex["muscle_group"])
        time_used += ex["duration_min"]

    if not workout and pool:
        workout = pool[:3]
    return workout
