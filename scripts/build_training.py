import json
import os
import random
from datetime import datetime
from typing import Dict, List, Any

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

INPUT_FILE = os.path.join(ROOT, "data", "slangs.jsonl")
OUTPUT_DIR = os.path.join(ROOT, "train")

INSTRUCTION_OUT = os.path.join(OUTPUT_DIR, "instruction.jsonl")
CHAT_OUT = os.path.join(OUTPUT_DIR, "chat.jsonl")
EVAL_OUT = os.path.join(OUTPUT_DIR, "eval.jsonl")

random.seed(42)

SYSTEM_PROMPT = (
    "You are a helpful assistant that understands Nigerian (Naija) street slang. "
    "Explain meanings clearly, keep responses short, and provide natural examples. "
    "Avoid offensive content unless explicitly asked."
)

# Prompt templates (multiple styles improves generalization)
PROMPTS_DEFINE = [
    "What does '{term}' mean in Naija street slang? Give a short meaning and one example.",
    "Explain the meaning of '{term}' in Nigerian slang with one example sentence.",
    "In Nigerian street language, what does '{term}' mean? Provide a clear definition and example.",
]

PROMPTS_TRANSLATE_TO_EN = [
    "Translate this Naija slang sentence into Standard English: {sentence}",
    "Convert this Nigerian street slang sentence into clear Standard English: {sentence}",
    "Rewrite this into Standard English without losing the meaning: {sentence}",
]

PROMPTS_REWRITE_TO_NAIJA = [
    "Rewrite this sentence in natural Naija street style (Pidgin/Naija English): {sentence}",
    "Turn this Standard English sentence into Naija street slang: {sentence}",
    "Convert this sentence into Nigerian street vibe while keeping the meaning: {sentence}",
]

PROMPTS_DETECT = [
    "Identify the Naija slang term(s) in this sentence and explain them: {sentence}",
    "Find any Nigerian slang in the sentence and explain the meaning of each: {sentence}",
]


def read_jsonl(path: str) -> List[Dict[str, Any]]:
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for line_no, raw in enumerate(f, start=1):
            line = raw.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                rows.append(obj)
            except Exception as e:
                raise ValueError(f"Invalid JSON on line {line_no}: {e}")
    return rows


def normalize_examples(entry: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    Ensure examples is always a list of dicts with keys: text, translation_en(optional)
    """
    examples = entry.get("examples", [])
    cleaned = []
    for ex in examples:
        if isinstance(ex, dict) and "text" in ex:
            cleaned.append({
                "text": ex["text"],
                "translation_en": ex.get("translation_en", "")
            })
    return cleaned


def safe_str(val: Any) -> str:
    return str(val).strip() if val is not None else ""


def make_define_sample(entry: Dict[str, Any]) -> Dict[str, Any]:
    term = entry["term"]
    meaning = entry["meaning_en"]
    examples = normalize_examples(entry)
    ex_text = examples[0]["text"] if examples else ""

    instruction = random.choice(PROMPTS_DEFINE).format(term=term)
    output = f"Meaning: {meaning}"
    if ex_text:
        output += f"\nExample: {ex_text}"

    return {
        "type": "define",
        "instruction": instruction,
        "input": "",
        "output": output
    }


def make_translate_to_en_sample(entry: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    For every example, create a translate-to-English sample.
    If translation_en is missing, we generate an output using meaning only
    (still useful, but you should fill translations later for quality).
    """
    samples = []
    examples = normalize_examples(entry)
    for ex in examples:
        text = safe_str(ex.get("text"))
        if not text:
            continue

        instruction = random.choice(PROMPTS_TRANSLATE_TO_EN).format(sentence=text)
        translation = safe_str(ex.get("translation_en"))

        if not translation:
            # Fallback if contributor didn't provide translation
            # This is OK, but better to collect real translations later.
            translation = f"(Translation needed) — This uses Naija slang. Meaning clue: {entry.get('meaning_en', '')}"

        samples.append({
            "type": "translate_to_en",
            "instruction": instruction,
            "input": "",
            "output": translation
        })
    return samples


def make_rewrite_to_naija_sample(entry: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Create rewrite-to-Naija prompts using the English translation if available.
    That gives you high-quality parallel data.
    """
    samples = []
    examples = normalize_examples(entry)
    for ex in examples:
        naija_sentence = safe_str(ex.get("text"))
        english_sentence = safe_str(ex.get("translation_en"))

        if not naija_sentence or not english_sentence:
            continue

        instruction = random.choice(PROMPTS_REWRITE_TO_NAIJA).format(sentence=english_sentence)
        output = naija_sentence

        samples.append({
            "type": "rewrite_to_naija",
            "instruction": instruction,
            "input": "",
            "output": output
        })
    return samples


def make_detect_sample(entry: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Detect slang terms in sentence. We teach the model:
      - identify the term
      - explain meaning
    """
    samples = []
    term = entry["term"]
    meaning = entry["meaning_en"]

    examples = normalize_examples(entry)
    for ex in examples:
        text = safe_str(ex.get("text"))
        if not text:
            continue

        instruction = random.choice(PROMPTS_DETECT).format(sentence=text)
        output = f"Slang: {term}\nMeaning: {meaning}"

        samples.append({
            "type": "detect",
            "instruction": instruction,
            "input": "",
            "output": output
        })
    return samples


def to_instruction_record(entry: Dict[str, Any], sample: Dict[str, Any]) -> Dict[str, Any]:
    """
    Wrap each sample with metadata for traceability.
    """
    return {
        "id": entry.get("id", ""),
        "task": sample["type"],
        "instruction": sample["instruction"],
        "input": sample.get("input", ""),
        "output": sample["output"],
        "meta": {
            "term": entry.get("term", ""),
            "language": entry.get("language", []),
            "category": entry.get("category", []),
            "region": entry.get("region", []),
            "polarity": entry.get("polarity", ""),
            "created_at": datetime.now().strftime("%Y-%m-%d")
        }
    }


def to_chat_record(entry: Dict[str, Any], sample: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert instruction sample to chat message format
    """
    return {
        "id": entry.get("id", ""),
        "task": sample["type"],
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": sample["instruction"]},
            {"role": "assistant", "content": sample["output"]}
        ],
        "meta": {
            "term": entry.get("term", ""),
            "language": entry.get("language", []),
            "category": entry.get("category", [])
        }
    }


def main():
    if not os.path.exists(INPUT_FILE):
        raise FileNotFoundError(f"Missing dataset file: {INPUT_FILE}")

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    data = read_jsonl(INPUT_FILE)

    instruction_rows = []
    chat_rows = []

    for entry in data:
        # Create multiple sample types per entry
        samples = []
        samples.append(make_define_sample(entry))
        samples.extend(make_translate_to_en_sample(entry))
        samples.extend(make_rewrite_to_naija_sample(entry))
        samples.extend(make_detect_sample(entry))

        # Wrap and store
        for s in samples:
            instruction_rows.append(to_instruction_record(entry, s))
            chat_rows.append(to_chat_record(entry, s))

    # Shuffle for training
    random.shuffle(instruction_rows)
    random.shuffle(chat_rows)

    
    # For small datasets, keep eval small but non-zero
    eval_size = min(50, max(5, int(len(instruction_rows) * 0.1)))
    eval_rows = instruction_rows[:eval_size]
    train_rows = instruction_rows[eval_size:]

    # Write instruction train set
    with open(INSTRUCTION_OUT, "w", encoding="utf-8") as f:
        for row in train_rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    # Write chat set
    with open(CHAT_OUT, "w", encoding="utf-8") as f:
        for row in chat_rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    # Write eval set
    with open(EVAL_OUT, "w", encoding="utf-8") as f:
        for row in eval_rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    print("✅ Training files generated!")
    print(f"📌 Train (instruction): {INSTRUCTION_OUT}  ({len(train_rows)} samples)")
    print(f"📌 Chat dataset:        {CHAT_OUT}         ({len(chat_rows)} samples)")
    print(f"📌 Eval set:            {EVAL_OUT}         ({len(eval_rows)} samples)")
    print("\nTip: Fill translation_en for examples to make rewrite tasks stronger.")


if __name__ == "__main__":
    main()
