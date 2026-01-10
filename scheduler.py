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
    "Breakfast": time(8, 0),
    "Lunch": time(13, 0),
    "Snack": time(17, 0),
    "Dinner": time(20, 0),
}

# ------------------------------------------------------------------
# Argument Parsing (UNCHANGED)
# ------------------------------------------------------------------


def parse_time_arg(value):
    try:
        return datetime.strptime(value, "%H:%M").time()
    except ValueError:
        raise argparse.ArgumentTypeError("Time must be in HH:MM format (e.g., 08:30)")


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
    )

    parser.add_argument(
        "-sd",
        "--start-date",
        type=str,
        default=(datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"),
        dest="start_date_str",
    )

    parser.add_argument(
        "-ed",
        "--end-date",
        type=str,
        default=(datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
        dest="end_date_str",
    )

    parser.add_argument(
        "-bt",
        "--breakfast-time",
        type=parse_time_arg,
        default=DEFAULT_MEAL_TIMES["Breakfast"],
        dest="breakfast_time",
    )

    parser.add_argument(
        "-lt",
        "--lunch-time",
        type=parse_time_arg,
        default=DEFAULT_MEAL_TIMES["Lunch"],
        dest="lunch_time",
    )

    parser.add_argument(
        "-st",
        "--snack-time",
        type=parse_time_arg,
        default=DEFAULT_MEAL_TIMES["Snack"],
        dest="snack_time",
    )

    parser.add_argument(
        "-dt",
        "--dinner-time",
        type=parse_time_arg,
        default=DEFAULT_MEAL_TIMES["Dinner"],
        dest="dinner_time",
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
                meal_items[category].append(
                    {
                        "title": row["TITLE"].strip(),
                        "duration_hours": float(row["TOTAL_HOURS"]),
                        "ingredients": [
                            i.strip()
                            for i in row["Ingredients"].split(",")
                            if i.strip()
                        ],
                    }
                )
            except Exception:
                continue

    if not any(meal_items.values()):
        raise ValueError("No valid meal data was found.")

    return meal_items


# ------------------------------------------------------------------
# ICS Helpers (ONLY CHANGE HERE)
# ------------------------------------------------------------------


def generate_ics_event(start_dt, end_dt, summary):
    dt_format = "%Y%m%dT%H%M%S"
    uid = f"{start_dt.strftime('%Y%m%d%H%M%S')}-{random.getrandbits(64)}@meal-scheduler.com"

    return f"""BEGIN:VEVENT
UID:{uid}
DTSTAMP:{datetime.now().strftime(dt_format)}
DTSTART:{start_dt.strftime(dt_format)}
DTEND:{end_dt.strftime(dt_format)}
SUMMARY:{summary}
LOCATION:{EVENT_ADDRESS}
END:VEVENT"""


# ------------------------------------------------------------------
# Schedule & Shopping List (UNCHANGED API)
# ------------------------------------------------------------------


def create_schedule_and_list(
    meal_data, start_date, end_date, meal_times, ics_filename, list_filename
):
    ics_content = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//MealScheduler//RandomMealGenerator//EN",
        "X-WR-CALNAME:Custom Meal Plan",
    ]

    unique_ingredients = set()
    current_date = start_date

    while current_date <= end_date:
        for category, items in meal_data.items():
            if not items:
                continue

            meal = random.choice(items)
            start_dt = datetime.combine(current_date, meal_times[category])
            end_dt = start_dt + timedelta(hours=meal["duration_hours"])

            unique_ingredients.update(meal["ingredients"])

            ics_content.append(generate_ics_event(start_dt, end_dt, meal["title"]))

        current_date += timedelta(days=1)

    ics_content.append("END:VCALENDAR")

    with open(ics_filename, "w") as f:
        f.write("\n".join(ics_content))

    with open(list_filename, "w") as f:
        for item in sorted(unique_ingredients):
            f.write(f"{item}\n")

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
    )

    print(f"\n✅ Calendar created: {ics_file}")
    print(f"✅ Shopping list created: {list_file}")
