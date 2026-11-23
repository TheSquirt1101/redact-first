# What this does and does not do

Read this before relying on redact-first for anything that matters.

## What it does

- Finds likely personal data in a text file: names you supply in a list, South
  African ID numbers (validated with their check digit), phone numbers, and
  email addresses.
- Replaces those values with neutral codes so you can paste the coded version
  into any AI chatbot without sending the real data.
- Keeps the code-to-value mapping in a file on your own machine, so you can turn
  the AI's reply back into real names yourself, locally.
- Everything runs on your machine. Nothing is uploaded. There is no account, no
  server, no telemetry.

## What it does not do

- **It is not legal advice and it does not make you compliant** with POPIA, GDPR,
  or any other data-protection law. Compliance is about your whole process -
  consent, purpose, retention, who sees what - not one tool. Questions about
  what is lawful go to your organisation's information officer or a
  data-protection professional.
- **It only protects the data you choose to run through it.** If you paste a
  class list straight into a chatbot, this tool never saw it and cannot help.
  The habit is the protection; the tool only makes the habit easy.
- **It will miss things.** It catches the patterns it knows. Unusual names not on
  your list, ID numbers from other countries, account numbers, dates of birth in
  prose, and context that identifies someone without naming them will slip
  through. Always read the coded output before you paste it.
- **It can produce false positives** - an ordinary 13-digit number that happens
  to pass the check digit, or a listed name that is also a common word. Check the
  output.

## The one rule that matters most

The `.map.json` file is the thing that links codes back to real people. Keep it
on your machine. Never paste it into an AI, never email it, never commit it to a
public repo. The included `.gitignore` already keeps it out of git.
