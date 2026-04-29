import csv
import os

FILE_NAME = "expenses.csv"


def _file_has_header():
    if not os.path.isfile(FILE_NAME):
        return False

    with open(FILE_NAME, newline="", encoding="utf-8") as file:
        first_line = file.readline().strip()

    return first_line == "Item,Amount,Category"


def save_expense(item, amount, category):
    file_exists = os.path.isfile(FILE_NAME)

    if file_exists and not _file_has_header():
        with open(FILE_NAME, newline="", encoding="utf-8") as file:
            existing_rows = list(csv.reader(file))

        with open(FILE_NAME, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(["Item", "Amount", "Category"])
            writer.writerows(existing_rows)

    if not file_exists:
        with open(FILE_NAME, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(["Item", "Amount", "Category"])

    with open(FILE_NAME, mode="a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow([item, amount, category])
