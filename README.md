# This Project is under active development 🚧
# 🍽️ ProTeen

[![Python 3.x](https://img.shields.io/badge/Python-3.x-blue.svg)](https://www.python.org/downloads/)

A flexible Python script that reads a list of meals from a CSV file, randomly selects an item for each meal slot (Breakfast, Lunch, Dinner), and generates a schedule for a custom date range in the standard **iCalendar (`.ics`) format**. This file can be easily imported into calendar applications like **Apple Calendar, Google Calendar, and Outlook**.

**NEW:** Now includes **nutritional tracking** with automatic meal scheduling to meet your daily nutritional goals!

## 🛠️ Setup

### Prerequisites

You need **Python 3.x** installed on your system (macOS, Linux, or Windows).

## ⚙️ Input File Format (`Meals.csv`)

The script requires the input CSV file to be separated by a **comma (`,`)** and must contain the following headers:

| Header | Description | Example Value |
| :--- | :--- | :--- |
| **TITLE** | The name of the meal/dish. | `Paneer Tikka Masala` |
| **TOTAL_HOURS** | The duration of the event (as a float). | `1.5` (for 1 hour 30 mins) |
| **CATEGORY** | Must be one of: `Breakfast`, `Lunch`, `Snack` or `Dinner`. | `Dinner` |
| **INGREDIENTS** | List of ingredients separated by commas. | `Paneer, Onion, Tomato` |
| **Protein_g** | Protein content in grams per serving. | `20` |
| **KCal** | Calories (kilocalories) per serving. | `480` |
| **Fat_g** | Fat content in grams per serving. | `32` |
| **Carbs_g** | Carbohydrates in grams per serving. | `26` |
| **Iron_mg** | Iron content in milligrams per serving. | `3.5` |
| **Fiber_g** | Dietary fiber in grams per serving. | `5.0` |

## 🎯 Nutritional Tracking Features

### Intelligent Meal Selection

Enable nutritional mode with the `-nm` or `--nutritional-mode` flag to automatically select meals that help you meet your daily nutritional goals:

```bash
python3 scheduler.py --nutritional-mode --protein-goal 80
```

The intelligent scheduler uses an optimization algorithm to select meals that best fill your nutritional gaps, prioritizing protein and iron.

### Customizable Daily Goals

Set your own daily nutritional targets:

```bash
python3 scheduler.py -nm \
  --protein-goal 100 \
  --kcal-goal 2500 \
  --fat-goal 70 \
  --carbs-goal 300 \
  --iron-goal 20 \
  --fiber-goal 30
```

**Default Goals:**
- Protein: 80g/day
- Calories: 2000 kcal/day
- Fat: 60g/day
- Carbohydrates: 250g/day
- Iron: 18mg/day
- Fiber: 25g/day

### Nutrition Reports

When using nutritional mode, a `nutrition_report.txt` file is automatically generated with:
- Daily nutritional breakdown for each day
- Comparison to your goals
- Weekly averages

### Calendar Event Display

All calendar events now include nutritional information in the event description, visible when you open the event details in your calendar app:

```
Protein: 20.0g
Calories: 480 kcal
Fat: 32.0g
Carbs: 26.0g
Iron: 3.5mg
Fiber: 5.0g
```

## 📋 Usage Examples

### Basic Usage (Random Selection)
```bash
python3 scheduler.py --start-date 2026-01-15 --end-date 2026-01-21
```

### Nutritional Mode with Default Goals
```bash
python3 scheduler.py -nm --start-date 2026-01-15 --end-date 2026-01-21
```

### High Protein Diet
```bash
python3 scheduler.py -nm --protein-goal 120 --start-date 2026-01-15 --end-date 2026-01-21
```

### Custom Meal Times with Nutrition Tracking
```bash
python3 scheduler.py -nm \
  --breakfast-time 07:00-09:00 \
  --lunch-time 12:00-14:00 \
  --dinner-time 19:00-21:00 \
  --protein-goal 90
```

## 🗓️ Importing to Apple Calendar
1. Locate the generated `meal_plan.ics` file.
2. Double-click the file on macOS.
3. The Apple Calendar application will launch and prompt you to select the target calendar for importing the new schedule.
4. Confirm the import.
5. Open any event to view nutritional information in the description.

## 🤝 Contribution
Feel free to fork this repository, open issues for suggestions, or submit pull requests!

