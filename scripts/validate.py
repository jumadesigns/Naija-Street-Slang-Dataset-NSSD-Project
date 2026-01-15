import json
import os
import sys
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATA_FILE = os.path.join(ROOT, "data", "slangs.jsonl")
CATEGORIES_FILE = os.path.join(ROOT, "data", "categories.json")
LANGUAGES_FILE = os.path.join(ROOT, "data", "languages.json")


REQUIRED_FIELDS = [
    "id",
    "term",
    "meaning_en",
    "examples",
    "language",
    "category",
    "safety",
    "source",
    "created_at"
]


def load_json_file(path: str):
    if not os.path.exists(path):
        print(f"❌ Missing file: {path}")
        sys.exit(1)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_allowed_categories():
    data = load_json_file(CATEGORIES_FILE)
    return set(data.get("categories", []))


def load_allowed_languages():
    data = load_json_file(LANGUAGES_FILE)
    langs = data.get("languages", {})
    return set(langs.keys())


def validate_date_format(date_str: str):
    """
    Ensures created_at is in YYYY-MM-DD format.
    """
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def validate_entry(entry: dict, line_number: int, allowed_categories: set, allowed_languages: set):
    errors = []

    # required fields
    for field in REQUIRED_FIELDS:
        if field not in entry:
            errors.append(f"Missing required field: '{field}'")

    # basic type checks
    if "examples" in entry and not isinstance(entry["examples"], list):
        errors.append("'examples' must be a list")
    if "language" in entry and not isinstance(entry["language"], list):
        errors.append("'language' must be a list")
    if "category" in entry and not isinstance(entry["category"], list):
        errors.append("'category' must be a list")

    # examples should not be empty
    if "examples" in entry and isinstance(entry["examples"], list) and len(entry["examples"]) == 0:
        errors.append("'examples' must contain at least 1 example object")

    # validate categories
    if "category" in entry and isinstance(entry["category"], list):
        invalid_categories = [c for c in entry["category"] if c not in allowed_categories]
        if invalid_categories:
            errors.append(f"Invalid categories: {invalid_categories}")

    # validate languages
    if "language" in entry and isinstance(entry["language"], list):
        invalid_languages = [l for l in entry["language"] if l not in allowed_languages]
        if invalid_languages:
            errors.append(f"Invalid language tags: {invalid_languages}")

    # validate safety structure
    if "safety" in entry and isinstance(entry["safety"], dict):
        required_safety_fields = ["contains_slur", "contains_profanity", "adult_sexual", "harassment"]
        for f in required_safety_fields:
            if f not in entry["safety"]:
                errors.append(f"Missing safety field: safety.{f}")
    else:
        errors.append("'safety' must be an object")

    # validate created_at format
    if "created_at" in entry:
        if not isinstance(entry["created_at"], str) or not validate_date_format(entry["created_at"]):
            errors.append("created_at must be a string in YYYY-MM-DD format")

    if errors:
        print(f"\n❌ Validation errors on line {line_number}:")
        for e in errors:
            print(f"   - {e}")
        return False

    return True


def main():
    if not os.path.exists(DATA_FILE):
        print(f"❌ Missing dataset file: {DATA_FILE}")
        print("Create it at: data/slangs.jsonl")
        sys.exit(1)

    allowed_categories = load_allowed_categories()
    allowed_languages = load_allowed_languages()

    seen_ids = set()
    total = 0
    ok_count = 0

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        for line_number, raw_line in enumerate(f, start=1):
            line = raw_line.strip()

            # allow blank lines
            if not line:
                continue

            total += 1

            try:
                entry = json.loads(line)
            except json.JSONDecodeError as e:
                print(f"\n❌ JSON error on line {line_number}: {e}")
                print(f"   Line content: {line}")
                continue

            # unique id check
            entry_id = entry.get("id")
            if entry_id in seen_ids:
                print(f"\n❌ Duplicate id found on line {line_number}: {entry_id}")
                continue
            seen_ids.add(entry_id)

            # validate fields
            if validate_entry(entry, line_number, allowed_categories, allowed_languages):
                ok_count += 1

    print("\n============================")
    print(f"✅ Validation finished")
    print(f"Total entries checked: {total}")
    print(f"Valid entries: {ok_count}")
    print(f"Invalid entries: {total - ok_count}")
    print("============================\n")

    if ok_count != total:
        sys.exit(1)


if __name__ == "__main__":
    main()
