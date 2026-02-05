# Contributing to Naija Street Slang Dataset (NSSD)
[![Contribute](https://img.shields.io/badge/Contribute-Open-brightgreen?style=flat-square)](CONTRIBUTING.md)
[![Add Slang](https://img.shields.io/badge/Add%20Slang-GitHub%20Issue-blue?style=flat-square)](../../issues/new/choose)



Thanks for contributing! This project collects Nigerian street slangs and code-mixed expressions for LLM/NLP training.

## Who can contribute
**Everyone.** You do **not** need to be a developer to contribute.

- **Non-dev contributors:** submit slang terms using GitHub Issues (recommended) or a form.
- **Dev contributors:** submit Pull Requests with JSONL entries + run validation locally.

---

## What you can contribute
- New slang terms + meanings + examples
- Better examples / translations
- Category and language tag improvements
- Fixes to schema/validation/training scripts
- Documentation improvements

---

## Quick paths to contribute

### ✅ Option 1: GitHub Issue (No coding required — recommended)
Use the repo’s **“Add a Naija slang term”** issue template:
1. Go to the **Issues** tab
2. Click **New issue**
3. Choose **Add a Naija slang term**
4. Fill the form and submit

This is the easiest way to contribute without touching code.

> If you’re not sure about spelling, category, or language tags, submit anyway — we’ll review it.

### ✅ Option 2: Online Form (No coding required — optional)
If you prefer a form, submit here:
- **Google Form:** _[add link here]_

(We’ll review and add submissions regularly.)

### ✅ Option 3: Pull Request (Developers)
If you’re comfortable with Git/GitHub:
1. Fork the repo
2. Add entries to `data/slangs.jsonl`
3. Run validation:
   ```bash
   python3 scripts/validate.py
