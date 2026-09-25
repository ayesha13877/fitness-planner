"""
Preset food database used for search + smart meal suggestions.
Values are approximate per stated serving (used for estimates, not medical accuracy).
"""

FOOD_DB = [
    {"name": "Boiled egg", "serving": "1 large (50g)", "calories": 78, "protein": 6, "carbs": 0.6, "fat": 5},
    {"name": "Fried egg", "serving": "1 large", "calories": 90, "protein": 6, "carbs": 0.4, "fat": 7},
    {"name": "Omelette (2 eggs)", "serving": "1 omelette", "calories": 190, "protein": 13, "carbs": 2, "fat": 14},
    {"name": "Roti (whole wheat)", "serving": "1 medium", "calories": 120, "protein": 3, "carbs": 22, "fat": 2},
    {"name": "Chicken curry (home-style)", "serving": "1 cup (~200g)", "calories": 280, "protein": 26, "carbs": 8, "fat": 16},
    {"name": "Chicken breast (grilled)", "serving": "100g", "calories": 165, "protein": 31, "carbs": 0, "fat": 4},
    {"name": "Daal (lentils)", "serving": "1 cup", "calories": 230, "protein": 18, "carbs": 40, "fat": 1},
    {"name": "White rice (cooked)", "serving": "1 cup", "calories": 205, "protein": 4, "carbs": 45, "fat": 0.5},
    {"name": "Chicken biryani", "serving": "1 plate (~300g)", "calories": 450, "protein": 22, "carbs": 55, "fat": 15},
    {"name": "Yogurt (plain)", "serving": "1 cup", "calories": 150, "protein": 8, "carbs": 11, "fat": 8},
    {"name": "Lassi (sweet)", "serving": "1 glass (250ml)", "calories": 220, "protein": 6, "carbs": 30, "fat": 8},
    {"name": "Salad (mixed veg)", "serving": "1 bowl", "calories": 60, "protein": 2, "carbs": 12, "fat": 0.5},
    {"name": "Grilled fish", "serving": "100g", "calories": 150, "protein": 28, "carbs": 0, "fat": 4},
    {"name": "Paneer (cooked)", "serving": "100g", "calories": 265, "protein": 18, "carbs": 6, "fat": 20},
    {"name": "Banana", "serving": "1 medium", "calories": 105, "protein": 1, "carbs": 27, "fat": 0.4},
    {"name": "Apple", "serving": "1 medium", "calories": 95, "protein": 0.5, "carbs": 25, "fat": 0.3},
    {"name": "Almonds", "serving": "10 pieces", "calories": 70, "protein": 2.5, "carbs": 2.5, "fat": 6},
    {"name": "Peanut butter", "serving": "1 tbsp", "calories": 95, "protein": 4, "carbs": 3, "fat": 8},
    {"name": "Oats (cooked with water)", "serving": "1 bowl", "calories": 150, "protein": 5, "carbs": 27, "fat": 3},
    {"name": "Milk (full fat)", "serving": "1 glass (250ml)", "calories": 150, "protein": 8, "carbs": 12, "fat": 8},
    {"name": "Whey protein shake", "serving": "1 scoop + water", "calories": 120, "protein": 24, "carbs": 3, "fat": 1.5},
    {"name": "Chickpeas (chana, cooked)", "serving": "1 cup", "calories": 270, "protein": 15, "carbs": 45, "fat": 4},
    {"name": "Beef curry", "serving": "1 cup", "calories": 310, "protein": 24, "carbs": 6, "fat": 20},
    {"name": "Vegetable pulao", "serving": "1 plate", "calories": 320, "protein": 6, "carbs": 55, "fat": 8},
    {"name": "Samosa", "serving": "1 piece", "calories": 150, "protein": 3, "carbs": 18, "fat": 8},
    {"name": "Boiled potato", "serving": "1 medium", "calories": 110, "protein": 2, "carbs": 26, "fat": 0.1},
    {"name": "Brown rice (cooked)", "serving": "1 cup", "calories": 215, "protein": 5, "carbs": 45, "fat": 1.8},
    {"name": "Sandwich (chicken)", "serving": "1 sandwich", "calories": 330, "protein": 22, "carbs": 32, "fat": 12},
    {"name": "French fries", "serving": "1 small serving", "calories": 320, "protein": 3, "carbs": 40, "fat": 17},
    {"name": "Green tea", "serving": "1 cup", "calories": 2, "protein": 0, "carbs": 0, "fat": 0},
]


def search_food(query: str):
    q = query.strip().lower()
    if not q:
        return []
    return [f for f in FOOD_DB if q in f["name"].lower()]
