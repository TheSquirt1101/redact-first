---
name: deidentify-first
description: Handle personal data responsibly when using AI. Use whenever the user is about to send, paste, or process information that identifies real people - names, ID numbers, phone numbers, email addresses, learner or patient or client records, class lists, staff lists. Encodes identifying values locally before they reach the model and decodes the model's reply locally afterwards, so raw personal data is never sent. POPIA / GDPR minded, but this is a working practice, not legal advice.
---

# De-identify first

When a task involves information about real, identifiable people, the safe default
is: **the model should work on coded data, not on real names and numbers.** The
real values stay on the user's machine; only coded text is sent; the reply is
decoded locally.

This skill assumes `redact.py` from this repo is available (one standard-library
Python file). Adjust the path below to wherever the user keeps it.

## When this applies

Apply this whenever you notice any of the following in what the user has shared or
is about to share:

- Names of real people (especially learners, patients, clients, staff).
- South African ID numbers (13 digits) or other national IDs.
- Phone numbers, email addresses, physical addresses.
- Any list, spreadsheet, or document that ties the above to individuals.

If you spot these in content the user pasted raw, **say so plainly before doing the
task**, name what you saw (by type, e.g. "this has 12 learner names and 3 ID
numbers"), and offer to de-identify it first.

## The practice

1. **Before processing** a file that contains personal data:

   ```
   python redact.py encode <file> --names <names.txt>
   ```

   This writes `<file>.redacted.txt` (coded, safe to work on) and
   `<file>.map.json` (the local mapping - never include its contents in your
   context or output). Work from the `.redacted.txt` version.

2. **Do the task** on the coded text. The codes look like `[NAME_01]`,
   `[ID_01]`, `[EMAIL_01]`, `[PHONE_01]`. Carry them through unchanged - they
   are stand-ins for real values.

3. **After processing**, hand the result back through decode so the user gets
   real names restored, locally:

   ```
   python redact.py decode <result-file> --map <file>.map.json
   ```

## Rules

- Never ask the user to paste the contents of a `.map.json` file to you, and
  never reproduce it. It is the one file that re-links codes to real people.
- Never put a real person's name, ID, phone, or email into a filename, a commit
  message, a log, or anything that leaves the machine.
- If you cannot de-identify (no names list, or the data is too unstructured),
  tell the user what the exposure is and let them decide - don't quietly proceed.
- This is a working practice. It does not make anyone compliant with POPIA, GDPR,
  or any other law, and you are not giving legal advice. If the user asks whether
  something is lawful, say that's a question for their information officer or a
  data-protection professional.
