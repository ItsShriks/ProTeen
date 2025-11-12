import argparse
import csv
import os
import random
from datetime import datetime, time, timedelta
from io import StringIO

# --- Configuration (Defaults) ---
DEFAULT_MEAL_TIMES = {
    "Breakfast": time(8, 0),
    "Lunch": time(12, 30),
    "Dinner": time(20, 0),
}
OUTPUT_ICS_FILENAME = "custom_meal_schedule.ics"
OUTPUT_SHOPPING_LIST_FILENAME = "shopping_list.txt"  # New output file

# --- Argument Parser ---


def parse_time_arg(time_str):
    """Validates and converts a time string (HH:MM) to a datetime.time object."""
    try:
        # Use strptime to parse time string
        return datetime.strptime(time_str, "%H:%M").time()
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"Invalid time format: '{time_str}'. Must be HH:MM (e.g., 07:30 or 19:00)."
        )


def parse_arguments():
    """Parses command line arguments for input file, date range, and meal times."""
    parser = argparse.ArgumentParser(
        description="Generates a random meal schedule in iCalendar (.ics) format and a unique ingredient shopping list.",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    # --- File and Date Arguments ---
    parser.add_argument(
        "-i",
        "--input",
        type=str,
        default="Meals.csv",
        help="Path to the input CSV file containing meal data. (Delimiter: ;)\nExample: -i path/to/my/data.csv",
        dest="csv_filename",
    )

    parser.add_argument(
        "-sd",
        "--start-date",
        type=str,
        default=(datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"),
        help="The start date (inclusive) for the schedule. Format: YYYY-MM-DD.\nDefaults to tomorrow's date.",
        dest="start_date_str",
    )

    parser.add_argument(
        "-ed",
        "--end-date",
        type=str,
        default=(datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
        help="The end date (inclusive) for the schedule. Format: YYYY-MM-DD.\nDefaults to 7 days from tomorrow.",
        dest="end_date_str",
    )

    # --- Time Customization Arguments ---
    parser.add_argument(
        "-bt",
        "--breakfast-time",
        type=parse_time_arg,
        default=DEFAULT_MEAL_TIMES["Breakfast"],
        help=f"Custom time for Breakfast. Format: HH:MM. (Default: {DEFAULT_MEAL_TIMES['Breakfast'].strftime('%H:%M')})",
        dest="breakfast_time",
    )

    parser.add_argument(
        "-lt",
        "--lunch-time",
        type=parse_time_arg,
        default=DEFAULT_MEAL_TIMES["Lunch"],
        help=f"Custom time for Lunch. Format: HH:MM. (Default: {DEFAULT_MEAL_TIMES['Lunch'].strftime('%H:%M')})",
        dest="lunch_time",
    )

    parser.add_argument(
        "-dt",
        "--dinner-time",
        type=parse_time_arg,
        default=DEFAULT_MEAL_TIMES["Dinner"],
        help=f"Custom time for Dinner. Format: HH:MM. (Default: {DEFAULT_MEAL_TIMES['Dinner'].strftime('%H:%M')})",
        dest="dinner_time",
    )

    args = parser.parse_args()

    # Date validation and conversion
    try:
        args.start_date = datetime.strptime(args.start_date_str, "%Y-%m-%d").date()
        args.end_date = datetime.strptime(args.end_date_str, "%Y-%m-%d").date()
    except ValueError:
        parser.error("Date format is invalid. Please use YYYY-MM-DD.")

    if args.start_date > args.end_date:
        parser.error("Start Date cannot be after End Date.")

    # Consolidate meal times for easier processing
    args.meal_times = {
        "Breakfast": args.breakfast_time,
        "Lunch": args.lunch_time,
        "Dinner": args.dinner_time,
    }

    return args


# --- Core Functions ---


def parse_data(filename):
    """Reads and parses meal data from the specified CSV file, including ingredients."""
    meal_items = {"Breakfast": [], "Lunch": [], "Dinner": []}

    if not os.path.exists(filename):
        raise FileNotFoundError(
            f"Error: The file '{filename}' was not found in the current directory."
        )

    print(f"Reading data from {filename}...")

    with open(filename, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=";")

        for row in reader:
            # Check for all required headers including the new 'Ingredients'
            required_headers = ["TITLE", "TOTAL_HOURS", "CATEGORY", "Ingredients"]
            if all(header in row for header in required_headers):
                category = row["CATEGORY"].strip()
                try:
                    duration = float(row["TOTAL_HOURS"])
                    title = row["TITLE"].strip()
                    # CRITICAL: Split ingredients by comma and strip whitespace
                    ingredients = [
                        item.strip()
                        for item in row["Ingredients"].split(",")
                        if item.strip()
                    ]

                    if category in meal_items:
                        meal_items[category].append(
                            {
                                "title": title,
                                "duration_hours": duration,
                                "ingredients": ingredients,
                            }
                        )
                except ValueError:
                    print(f"Warning: Skipping row due to invalid TOTAL_HOURS: {row}")
            else:
                # Only print warning if one of the core fields is missing.
                if "TITLE" in row:
                    print(
                        f"Warning: Skipping row due to missing 'Ingredients' column: {row.get('TITLE', 'Unknown Title')}"
                    )
                else:
                    print(f"Warning: Skipping row due to missing core headers.")

    if not any(meal_items.values()):
        raise ValueError(
            "Error: Successfully read the file, but no valid meal data was found."
        )

    return meal_items


def generate_ics_event(start_dt, end_dt, summary):
    """Generates an iCalendar VEVENT block. summary is the food title only."""
    dt_format = "%Y%m%dT%H%M%S"
    uid_base = start_dt.strftime("%Y%m%d%H%M%S")
    # Generate a unique UID
    uid = f"{uid_base}-{random.getrandbits(64)}@meal-scheduler.com"

    return f"""BEGIN:VEVENT
UID:{uid}
DTSTAMP:{datetime.now().strftime(dt_format)}
DTSTART:{start_dt.strftime(dt_format)}
DTEND:{end_dt.strftime(dt_format)}
SUMMARY:{summary}
END:VEVENT"""


def create_schedule_and_list(
    meal_data, start_date, end_date, meal_times, ics_filename, list_filename
):
    """Creates the iCalendar file and the shopping list file."""

    ics_content = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//MealScheduler//RandomMealGenerator//EN",
        "X-WR-CALNAME:Custom Meal Plan",
    ]

    # Set to store all unique ingredients scheduled for the week
    unique_ingredients = set()

    current_date = start_date
    delta = timedelta(days=1)

    print(
        f"\n--- Meal Schedule: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')} ---"
    )

    while current_date <= end_date:
        day_name = current_date.strftime("%A, %B %d")
        print(f"\n**{day_name}**")

        for category, items in meal_data.items():
            if not items:
                print(f"Warning: No items found for {category}. Skipping.")
                continue

            # Randomly select a meal for this day
            meal_info = random.choice(items)

            meal_time = meal_times[category]
            duration_hours = meal_info["duration_hours"]
            title = meal_info["title"]

            # Add all unique ingredients to the set
            if "ingredients" in meal_info and meal_info["ingredients"]:
                unique_ingredients.update(meal_info["ingredients"])

            # Create ICS event
            start_dt = datetime.combine(current_date, meal_time)
            end_dt = start_dt + timedelta(hours=duration_hours)
            summary = title
            ics_content.append(generate_ics_event(start_dt, end_dt, summary))

            # Print to console for verification
            start_str = start_dt.strftime("%H:%M")
            end_str = end_dt.strftime("%H:%M")
            print(f"  - **{category}** ({start_str} - {end_str}): {title}")

        current_date += delta  # Move to the next day

    # Finalize ICS file
    ics_content.append("END:VCALENDAR")
    with open(ics_filename, "w") as f:
        f.write("\n".join(ics_content))

    # Create Shopping List file (TXT format)
    shopping_list_content = "--- Weekly Shopping List ---\n\n"
    # Sort the ingredients alphabetically
    sorted_ingredients = sorted(list(unique_ingredients))

    for ingredient in sorted_ingredients:
        shopping_list_content += f"{ingredient}\n"

    with open(list_filename, "w") as f:
        f.write(shopping_list_content)

    return ics_filename, list_filename


# --- Execution ---
if __name__ == "__main__":
    try:
        # 1. Parse arguments
        args = parse_arguments()

        # 2. Parse meal data
        parsed_items = parse_data(args.csv_filename)

        # 3. Create the iCalendar and Shopping List files
        ics_file, list_file = create_schedule_and_list(
            parsed_items,
            args.start_date,
            args.end_date,
            args.meal_times,
            OUTPUT_ICS_FILENAME,
            OUTPUT_SHOPPING_LIST_FILENAME,
        )

        print(f"\n✅ Successfully created calendar file: **{ics_file}**")
        print(
            f"✅ Successfully created shopping list file: **{list_file}** (Contains unique ingredients only)"
        )

    except (FileNotFoundError, ValueError, argparse.ArgumentTypeError) as e:
        print(f"\n❌ Script failed: {e}")
        print(
            "\nPlease ensure your CSV includes the 'Ingredients' column and run with `-h` for usage details."
        )
    except Exception as e:
        print(f"\n❌ An unexpected error occurred: {e}")
