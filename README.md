# 🍽️ ProTeen

[![Python 3.x](https://img.shields.io/badge/Python-3.x-blue.svg)](https://www.python.org/downloads/)

A flexible Python script that reads a list of meals from a CSV file, randomly selects an item for each meal slot (Breakfast, Lunch, Dinner), and generates a schedule for a custom date range in the standard **iCalendar (`.ics`) format**. This file can be easily imported into calendar applications like **Apple Calendar, Google Calendar, and Outlook**.

## 🛠️ Setup

### Prerequisites

You need **Python 3.x** installed on your system (macOS, Linux, or Windows).

## ⚙️ Input File Format (`Meals.csv`)

The script requires the input CSV file to be separated by a **semicolon (`;`)** and must contain the following three headers:

| Header | Description | Example Value |
| :--- | :--- | :--- |
| **TITLE** | The name of the meal/dish. | `Paneer Tikka Masala` |
| **TOTAL_HOURS** | The duration of the event (as a float). | `1.5` (for 1 hour 30 mins) |
| **CATEGORY** | Must be one of: `Breakfast`, `Lunch`, or `Dinner`. | `Dinner` |

## 🗓️ Importing to Apple Calendar
1. Locate the generated custom_meal_schedule.ics file.
2. Double-click the file on your macOS machine.
3. The Apple Calendar application will launch and prompt you to select the target calendar for importing the new schedule.
4. Confirm the import.

## 🤝 Contribution
Feel free to fork this repository, open issues for suggestions, or submit pull requests!
