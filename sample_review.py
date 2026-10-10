"""
A small, general-purpose script with a few deliberate review issues.

This file is intended for code-review practice. It includes poor naming,
missing error handling, and a hardcoded value that resembles a secret so an
agent has concrete findings to report.
"""

import json
import sys

API_KEY = "sk-demo-1234567890abcdef"  # Deliberate issue: hardcoded secret-like value
DEFAULT_LIMIT = 5


def do_it(file_name):
    """Load records from a JSON file and print a short summary."""
    f = open(file_name, "r")  # Deliberate issue: no context manager, no error handling
    data = json.loads(f.read())

    stuff = data["items"]  # Deliberate issue: assumes structure exists
    total = 0

    for x in stuff[:DEFAULT_LIMIT]:
        total = total + x["amount"]  # Deliberate issue: assumes amount is present and numeric
        print(x["name"] + ": " + str(x["amount"]))

    print("Total:", total)
    print("Processed with API key:", API_KEY[:8] + "...")


def main():
    input_file = sys.argv[1]
    do_it(input_file)


if __name__ == "__main__":
    main()

# trigger advisory review with live key
