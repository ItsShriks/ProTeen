#!/usr/bin/env python3

import argparse
import csv
import os
import random
from datetime import datetime, time, timedelta

# ------------------------------------------------------------------
# Constants
# ------------------------------------------------------------------

OUTPUT_ICS_FILENAME = "meal_plan.ics"
OUTPUT_SHOPPING_LIST_FILENAME = "shopping_list.txt"

EVENT_ADDRESS = "Home"

DEFAULT_MEAL_TIMES = {
    "Breakfast": (time(6, 0), time(10, 0)),
    "Lunch": (time(11, 0), time(14, 0)),
    "Snack": (time(17, 0), time(19, 0)),
    "Dinner": (time(20, 0), time(22, 0)),
}

# Default daily nutritional goals
DEFAULT_NUTRITION_GOALS = {
    "protein_g": 80.0,
    "kcal": 2000.0,
    "fat_g": 60.0,
    "carbs_g": 250.0,
    "iron_mg": 18.0,
    "fiber_g": 25.0,
}

# ------------------------------------------------------------------
# Argument Parsing (UNCHANGED)
# ------------------------------------------------------------------


def parse_time_arg(value):
    """
    Parse time argument supporting both formats:
    - Single time: "08:00" -> returns (time(8,0), time(8,0))
    - Time range: "08:00-09:00" -> returns (time(8,0), time(9,0))
    """
    if "-" in value:
        # Time range format
        try:
            parts = value.split("-")
            if len(parts) != 2:
                raise argparse.ArgumentTypeError(
                    "Time range must be in HH:MM-HH:MM format (e.g., 08:00-09:00)"
                )
            start_time = datetime.strptime(parts[0].strip(), "%H:%M").time()
            end_time = datetime.strptime(parts[1].strip(), "%H:%M").time()

            # Validate that start < end
            if start_time >= end_time:
                raise argparse.ArgumentTypeError(
                    "Start time must be before end time in range"
                )

            return (start_time, end_time)
        except ValueError:
            raise argparse.ArgumentTypeError(
                "Time range must be in HH:MM-HH:MM format (e.g., 08:00-09:00)"
            )
    else:
        # Single time format (backward compatible)
        try:
            single_time = datetime.strptime(value, "%H:%M").time()
            return (single_time, single_time)
        except ValueError:
            raise argparse.ArgumentTypeError(
                "Time must be in HH:MM format (e.g., 08:30) or HH:MM-HH:MM range format"
            )



def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Generate a meal schedule calendar and shopping list from CSV"
    )

    parser.add_argument(
        "-i",
        "--input",
        type=str,
        default="Meals.csv",
        dest="csv_filename",
        help="Path to the input CSV file containing meal data (default: %(default)s)",
    )

    parser.add_argument(
        "-sd",
        "--start-date",
        type=str,
        default=(datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"),
        dest="start_date_str",
        help="Start date for the meal plan in YYYY-MM-DD format (default: %(default)s)",
    )

    parser.add_argument(
        "-ed",
        "--end-date",
        type=str,
        default=(datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
        dest="end_date_str",
        help="End date for the meal plan in YYYY-MM-DD format (default: %(default)s)",
    )

    parser.add_argument(
        "-bt",
        "--breakfast-time",
        type=parse_time_arg,
        default=DEFAULT_MEAL_TIMES["Breakfast"],
        dest="breakfast_time",
        help="Time for breakfast: HH:MM for fixed time or HH:MM-HH:MM for random range (default: %(default)s)",
    )

    parser.add_argument(
        "-lt",
        "--lunch-time",
        type=parse_time_arg,
        default=DEFAULT_MEAL_TIMES["Lunch"],
        dest="lunch_time",
        help="Time for lunch: HH:MM for fixed time or HH:MM-HH:MM for random range (default: %(default)s)",
    )

    parser.add_argument(
        "-st",
        "--snack-time",
        type=parse_time_arg,
        default=DEFAULT_MEAL_TIMES["Snack"],
        dest="snack_time",
        help="Time for snack: HH:MM for fixed time or HH:MM-HH:MM for random range (default: %(default)s)",
    )

    parser.add_argument(
        "-dt",
        "--dinner-time",
        type=parse_time_arg,
        default=DEFAULT_MEAL_TIMES["Dinner"],
        dest="dinner_time",
        help="Time for dinner: HH:MM for fixed time or HH:MM-HH:MM for random range (default: %(default)s)",
    )

    # Nutritional mode and goals
    parser.add_argument(
        "-nm",
        "--nutritional-mode",
        action="store_true",
        dest="nutritional_mode",
        help="Enable intelligent meal selection to meet daily nutritional goals",
    )

    parser.add_argument(
        "--protein-goal",
        type=float,
        default=DEFAULT_NUTRITION_GOALS["protein_g"],
        dest="protein_goal",
        help="Daily protein goal in grams (default: %(default)s)",
    )

    parser.add_argument(
        "--kcal-goal",
        type=float,
        default=DEFAULT_NUTRITION_GOALS["kcal"],
        dest="kcal_goal",
        help="Daily calorie goal in kcal (default: %(default)s)",
    )

    parser.add_argument(
        "--fat-goal",
        type=float,
        default=DEFAULT_NUTRITION_GOALS["fat_g"],
        dest="fat_goal",
        help="Daily fat goal in grams (default: %(default)s)",
    )

    parser.add_argument(
        "--carbs-goal",
        type=float,
        default=DEFAULT_NUTRITION_GOALS["carbs_g"],
        dest="carbs_goal",
        help="Daily carbohydrates goal in grams (default: %(default)s)",
    )

    parser.add_argument(
        "--iron-goal",
        type=float,
        default=DEFAULT_NUTRITION_GOALS["iron_mg"],
        dest="iron_goal",
        help="Daily iron goal in milligrams (default: %(default)s)",
    )

    parser.add_argument(
        "--fiber-goal",
        type=float,
        default=DEFAULT_NUTRITION_GOALS["fiber_g"],
        dest="fiber_goal",
        help="Daily fiber goal in grams (default: %(default)s)",
    )

    args = parser.parse_args()

    args.start_date = datetime.strptime(args.start_date_str, "%Y-%m-%d").date()
    args.end_date = datetime.strptime(args.end_date_str, "%Y-%m-%d").date()

    if args.start_date > args.end_date:
        parser.error("Start Date cannot be after End Date.")

    args.meal_times = {
        "Breakfast": args.breakfast_time,
        "Lunch": args.lunch_time,
        "Snack": args.snack_time,
        "Dinner": args.dinner_time,
    }

    args.nutrition_goals = {
        "protein_g": args.protein_goal,
        "kcal": args.kcal_goal,
        "fat_g": args.fat_goal,
        "carbs_g": args.carbs_goal,
        "iron_mg": args.iron_goal,
        "fiber_g": args.fiber_goal,
    }

    return args


# ------------------------------------------------------------------
# Data Parsing (UNCHANGED)
# ------------------------------------------------------------------


def parse_data(filename):
    meal_items = {"Breakfast": [], "Lunch": [], "Snack": [], "Dinner": []}

    if not os.path.exists(filename):
        raise FileNotFoundError(f"File '{filename}' not found.")

    print(f"Reading data from {filename}...")

    with open(filename, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            required_headers = ["TITLE", "TOTAL_HOURS", "CATEGORY", "Ingredients"]

            if not all(h in row for h in required_headers):
                continue

            category = row["CATEGORY"].strip()

            try:
                meal_dict = {
                    "title": row["TITLE"].strip(),
                    "duration_hours": float(row["TOTAL_HOURS"]),
                    "ingredients": [
                        i.strip()
                        for i in row["Ingredients"].split(",")
                        if i.strip()
                    ],
                }
                
                # Parse nutritional information if available
                nutrition_fields = ["Protein_g", "KCal", "Fat_g", "Carbs_g", "Iron_mg", "Fiber_g"]
                if all(field in row for field in nutrition_fields):
                    meal_dict["nutrition"] = {
                        "protein_g": float(row["Protein_g"]) if row["Protein_g"] else 0.0,
                        "kcal": float(row["KCal"]) if row["KCal"] else 0.0,
                        "fat_g": float(row["Fat_g"]) if row["Fat_g"] else 0.0,
                        "carbs_g": float(row["Carbs_g"]) if row["Carbs_g"] else 0.0,
                        "iron_mg": float(row["Iron_mg"]) if row["Iron_mg"] else 0.0,
                        "fiber_g": float(row["Fiber_g"]) if row["Fiber_g"] else 0.0,
                    }
                else:
                    meal_dict["nutrition"] = None
                
                meal_items[category].append(meal_dict)
            except Exception:
                continue

    if not any(meal_items.values()):
        raise ValueError("No valid meal data was found.")

    return meal_items



# ------------------------------------------------------------------
# Scheduling Helpers
# ------------------------------------------------------------------


def check_overlap(start1, end1, start2, end2):
    """
    Check if two time ranges overlap.
    Returns True if there is any overlap, False otherwise.
    """
    return start1 < end2 and start2 < end1


def get_random_time_in_range(date, time_range):
    """
    Generate a random datetime within the given time range for a specific date.
    time_range is a tuple (start_time, end_time).
    If start_time == end_time, returns that exact time (backward compatible).
    """
    start_time, end_time = time_range

    if start_time == end_time:
        # Fixed time (backward compatible)
        return datetime.combine(date, start_time)

    # Convert times to minutes since midnight
    start_minutes = start_time.hour * 60 + start_time.minute
    end_minutes = end_time.hour * 60 + end_time.minute

    # Generate random time in minutes
    random_minutes = random.randint(start_minutes, end_minutes - 1)

    # Convert back to time
    random_hour = random_minutes // 60
    random_minute = random_minutes % 60

    return datetime.combine(date, time(random_hour, random_minute))


def select_meal_for_nutrition(available_meals, current_nutrition, nutrition_goals):
    """
    Intelligently select a meal to help meet daily nutritional goals.
    Uses a scoring system to find the meal that best fills nutritional gaps.
    
    Args:
        available_meals: List of meal dictionaries for a specific category
        current_nutrition: Dict of current daily nutritional totals
        nutrition_goals: Dict of daily nutritional goals
    
    Returns:
        Selected meal dictionary
    """
    if not available_meals:
        return None
    
    # If no nutrition data available, fall back to random selection
    if not available_meals[0].get("nutrition"):
        return random.choice(available_meals)
    
    best_meal = None
    best_score = float('-inf')
    
    for meal in available_meals:
        if not meal.get("nutrition"):
            continue
        
        score = 0.0
        meal_nutrition = meal["nutrition"]
        
        # Calculate how much this meal helps meet each nutritional goal
        # Higher score for nutrients we're furthest from meeting
        for nutrient in nutrition_goals:
            goal = nutrition_goals[nutrient]
            current = current_nutrition.get(nutrient, 0.0)
            meal_value = meal_nutrition.get(nutrient, 0.0)
            
            if goal > 0:
                # Calculate gap: how far we are from the goal
                gap = max(0, goal - current)
                
                # Score based on how much this meal fills the gap
                # Prioritize nutrients we're furthest from meeting
                if gap > 0:
                    fill_percentage = min(meal_value / gap, 1.0)
                    # Weight protein and iron more heavily
                    weight = 2.0 if nutrient in ["protein_g", "iron_mg"] else 1.0
                    score += fill_percentage * weight * (gap / goal)
        
        if score > best_score:
            best_score = score
            best_meal = meal
    
    # If no meal has nutrition data, fall back to random
    return best_meal if best_meal else random.choice(available_meals)



# ------------------------------------------------------------------
# ICS Helpers (ONLY CHANGE HERE)
# ------------------------------------------------------------------


def generate_ics_event(start_dt, end_dt, summary, nutrition=None):
    dt_format = "%Y%m%dT%H%M%S"
    uid = f"{start_dt.strftime('%Y%m%d%H%M%S')}-{random.getrandbits(64)}@meal-scheduler.com"
    
    # Build description with nutritional information if available
    description = ""
    if nutrition:
        nutrition_lines = [
            f"Protein: {nutrition.get('protein_g', 0):.1f}g",
            f"Calories: {nutrition.get('kcal', 0):.0f} kcal",
            f"Fat: {nutrition.get('fat_g', 0):.1f}g",
            f"Carbs: {nutrition.get('carbs_g', 0):.1f}g",
            f"Iron: {nutrition.get('iron_mg', 0):.1f}mg",
            f"Fiber: {nutrition.get('fiber_g', 0):.1f}g",
        ]
        description = "\\n".join(nutrition_lines)
    
    event = f"""BEGIN:VEVENT
UID:{uid}
DTSTAMP:{datetime.now().strftime(dt_format)}
DTSTART:{start_dt.strftime(dt_format)}
DTEND:{end_dt.strftime(dt_format)}
SUMMARY:{summary}
LOCATION:{EVENT_ADDRESS}"""
    
    if description:
        event += f"\nDESCRIPTION:{description}"
    
    event += "\nEND:VEVENT"
    
    return event


# ------------------------------------------------------------------
# Schedule & Shopping List (UNCHANGED API)
# ------------------------------------------------------------------


def create_schedule_and_list(
    meal_data, start_date, end_date, meal_times, ics_filename, list_filename,
    nutritional_mode=False, nutrition_goals=None
):
    ics_content = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//MealScheduler//RandomMealGenerator//EN",
        "X-WR-CALNAME:Custom Meal Plan",
    ]

    unique_ingredients = set()
    current_date = start_date
    
    # Track nutritional totals for reporting
    daily_nutrition_totals = {}

    MAX_RETRIES = 10

    while current_date <= end_date:
        # Track scheduled events for this day to detect overlaps
        daily_events = []
        
        # Track daily nutritional totals
        daily_nutrition = {
            "protein_g": 0.0,
            "kcal": 0.0,
            "fat_g": 0.0,
            "carbs_g": 0.0,
            "iron_mg": 0.0,
            "fiber_g": 0.0,
        }

        # Sort meal categories by their start time to schedule in order
        sorted_categories = sorted(
            meal_data.keys(),
            key=lambda cat: meal_times[cat][0] if cat in meal_times else time(0, 0)
        )

        for category in sorted_categories:
            items = meal_data[category]
            if not items:
                continue

            # Select meal based on mode
            if nutritional_mode and nutrition_goals:
                meal = select_meal_for_nutrition(items, daily_nutrition, nutrition_goals)
            else:
                meal = random.choice(items)
            
            if not meal:
                continue
            
            meal_duration = timedelta(hours=meal["duration_hours"])

            # Try to find a non-overlapping time slot
            scheduled = False
            for attempt in range(MAX_RETRIES):
                # Generate random start time within the allowed range
                start_dt = get_random_time_in_range(current_date, meal_times[category])
                end_dt = start_dt + meal_duration

                # Check for overlaps with already scheduled events
                has_overlap = False
                for existing_start, existing_end in daily_events:
                    if check_overlap(start_dt, end_dt, existing_start, existing_end):
                        has_overlap = True
                        break

                if not has_overlap:
                    # No overlap, schedule this event
                    daily_events.append((start_dt, end_dt))
                    unique_ingredients.update(meal["ingredients"])
                    
                    # Update daily nutrition totals
                    if meal.get("nutrition"):
                        for nutrient, value in meal["nutrition"].items():
                            daily_nutrition[nutrient] += value
                    
                    ics_content.append(
                        generate_ics_event(start_dt, end_dt, meal["title"], meal.get("nutrition"))
                    )
                    scheduled = True
                    break

            if not scheduled:
                # Fallback: schedule at the next available slot after the range end
                range_end_time = meal_times[category][1]
                fallback_start = datetime.combine(current_date, range_end_time)

                # Find the latest end time among existing events
                if daily_events:
                    latest_end = max(end for _, end in daily_events)
                    if latest_end > fallback_start:
                        fallback_start = latest_end

                end_dt = fallback_start + meal_duration
                daily_events.append((fallback_start, end_dt))
                unique_ingredients.update(meal["ingredients"])
                
                # Update daily nutrition totals
                if meal.get("nutrition"):
                    for nutrient, value in meal["nutrition"].items():
                        daily_nutrition[nutrient] += value
                
                ics_content.append(
                    generate_ics_event(fallback_start, end_dt, meal["title"], meal.get("nutrition"))
                )

                print(f"⚠️  Warning: Could not find non-overlapping slot for {category} on {current_date}, scheduled at {fallback_start.time()}")
        
        # Store daily nutrition totals
        daily_nutrition_totals[current_date] = daily_nutrition
        current_date += timedelta(days=1)

    ics_content.append("END:VCALENDAR")

    with open(ics_filename, "w") as f:
        f.write("\n".join(ics_content))

    with open(list_filename, "w") as f:
        for item in sorted(unique_ingredients):
            f.write(f"{item}\n")
    
    # Generate nutrition report if we have nutritional data
    if daily_nutrition_totals and nutrition_goals:
        report_filename = "nutrition_report.txt"
        with open(report_filename, "w") as f:
            f.write("=" * 60 + "\n")
            f.write("NUTRITIONAL REPORT\n")
            f.write("=" * 60 + "\n\n")
            
            # Daily breakdown
            f.write("DAILY BREAKDOWN:\n")
            f.write("-" * 60 + "\n")
            
            for date in sorted(daily_nutrition_totals.keys()):
                nutrition = daily_nutrition_totals[date]
                f.write(f"\n{date.strftime('%A, %B %d, %Y')}:\n")
                f.write(f"  Protein:  {nutrition['protein_g']:6.1f}g  (Goal: {nutrition_goals['protein_g']:.0f}g)\n")
                f.write(f"  Calories: {nutrition['kcal']:6.0f}    (Goal: {nutrition_goals['kcal']:.0f})\n")
                f.write(f"  Fat:      {nutrition['fat_g']:6.1f}g  (Goal: {nutrition_goals['fat_g']:.0f}g)\n")
                f.write(f"  Carbs:    {nutrition['carbs_g']:6.1f}g  (Goal: {nutrition_goals['carbs_g']:.0f}g)\n")
                f.write(f"  Iron:     {nutrition['iron_mg']:6.1f}mg (Goal: {nutrition_goals['iron_mg']:.0f}mg)\n")
                f.write(f"  Fiber:    {nutrition['fiber_g']:6.1f}g  (Goal: {nutrition_goals['fiber_g']:.0f}g)\n")
            
            # Weekly averages
            if len(daily_nutrition_totals) > 0:
                f.write("\n" + "=" * 60 + "\n")
                f.write("WEEKLY AVERAGES:\n")
                f.write("-" * 60 + "\n")
                
                num_days = len(daily_nutrition_totals)
                totals = {
                    "protein_g": 0.0,
                    "kcal": 0.0,
                    "fat_g": 0.0,
                    "carbs_g": 0.0,
                    "iron_mg": 0.0,
                    "fiber_g": 0.0,
                }
                
                for nutrition in daily_nutrition_totals.values():
                    for nutrient in totals:
                        totals[nutrient] += nutrition[nutrient]
                
                f.write(f"\nAverage over {num_days} days:\n")
                f.write(f"  Protein:  {totals['protein_g']/num_days:6.1f}g  (Goal: {nutrition_goals['protein_g']:.0f}g)\n")
                f.write(f"  Calories: {totals['kcal']/num_days:6.0f}    (Goal: {nutrition_goals['kcal']:.0f})\n")
                f.write(f"  Fat:      {totals['fat_g']/num_days:6.1f}g  (Goal: {nutrition_goals['fat_g']:.0f}g)\n")
                f.write(f"  Carbs:    {totals['carbs_g']/num_days:6.1f}g  (Goal: {nutrition_goals['carbs_g']:.0f}g)\n")
                f.write(f"  Iron:     {totals['iron_mg']/num_days:6.1f}mg (Goal: {nutrition_goals['iron_mg']:.0f}mg)\n")
                f.write(f"  Fiber:    {totals['fiber_g']/num_days:6.1f}g  (Goal: {nutrition_goals['fiber_g']:.0f}g)\n")
                f.write("\n" + "=" * 60 + "\n")
        
        print(f"✅ Nutrition report created: {report_filename}")

    return ics_filename, list_filename


# ------------------------------------------------------------------
# Main Execution (UNCHANGED)
# ------------------------------------------------------------------


if __name__ == "__main__":
    args = parse_arguments()

    parsed_items = parse_data(args.csv_filename)

    ics_file, list_file = create_schedule_and_list(
        parsed_items,
        args.start_date,
        args.end_date,
        args.meal_times,
        OUTPUT_ICS_FILENAME,
        OUTPUT_SHOPPING_LIST_FILENAME,
        args.nutritional_mode,
        args.nutrition_goals,
    )

    print(f"\n✅ Calendar created: {ics_file}")
    print(f"✅ Shopping list created: {list_file}")
    
    if args.nutritional_mode:
        print(f"\n🎯 Nutritional mode enabled with goals:")
        print(f"   Protein: {args.nutrition_goals['protein_g']:.0f}g/day")
        print(f"   Calories: {args.nutrition_goals['kcal']:.0f} kcal/day")
        print(f"   Fat: {args.nutrition_goals['fat_g']:.0f}g/day")
        print(f"   Carbs: {args.nutrition_goals['carbs_g']:.0f}g/day")
        print(f"   Iron: {args.nutrition_goals['iron_mg']:.0f}mg/day")
        print(f"   Fiber: {args.nutrition_goals['fiber_g']:.0f}g/day")

