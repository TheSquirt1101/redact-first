# redact-first

**De-identify personal data before you paste it into any AI.**

A tiny, free, offline tool for anyone who handles other people's information and
uses AI chatbots to help with their work: teachers with class lists, admin staff,
anyone with names, ID numbers, phone numbers, or email addresses in their files.

It swaps real values for codes *on your own machine*, so the chatbot works on
coded text and never sees the real data. When the reply comes back, you swap the
codes for real names again, locally. Nothing is ever uploaded. There is no
account and no server.

Built in South Africa with POPIA in mind, but it is not legal advice and it does
not make you compliant with anything. See [SCOPE.md](SCOPE.md).

## Why

People are pasting class lists, patient notes, and client records straight into
ChatGPT, Claude, and Gemini. Once that leaves your machine you have lost control
of it. The fix is a habit: strip the identifying bits first, let the AI help with
the coded version, put the names back yourself afterwards. This tool makes that
habit a two-command routine.

## Install

You need Python 3 (it comes with most computers; on Windows, get it from
python.org or the Microsoft Store). There is nothing else to install - the whole
codec is one standard-library file, [`redact.py`](redact.py). Download it, or
clone this repo.

## Use it with any AI (ChatGPT, Claude, Gemini, anything)

Say you have `class.txt` with learner names in it.

1. Make a names list, `names.txt`, one name per line (see
   [`names.example.txt`](names.example.txt)).

2. Make a safe copy:

   ```
   python redact.py encode class.txt --names names.txt
   ```

   You get `class.redacted.txt` (names become `[NAME_01]`, IDs become `[ID_01]`,
   and so on) and `class.map.json` (the mapping, which stays on your machine).

3. Paste **`class.redacted.txt`** into the chatbot. Do your task. Copy the reply
   into a file, say `reply.txt`.

4. Put the real names back:

   ```
   python redact.py decode reply.txt --map class.map.json
   ```

   You get `reply.decoded.txt` with real names restored - and the AI never saw
   them.

### Just want to know what's in a file?

```
python redact.py scan class.txt --names names.txt
```

It reports what personal data it found and changes nothing. Add `--show` to list
the actual matches on your screen (they stay local).

## Use it inside Claude Code (optional, makes it automatic)

If you work in [Claude Code](https://claude.com/claude-code), the
[`claude-code/`](claude-code/) folder adds two things:

- **A skill** (`skills/deidentify-first/`) that teaches the assistant to notice
  personal data and run the encode/decode steps for you.
- **A hook** (`hooks/pii-check.js`) that scans every prompt you submit and warns
  you - before it is sent - if it looks like it contains personal data. See
  [`settings.example.json`](claude-code/settings.example.json) to wire it up.

This layer only works inside Claude Code. The `redact.py` routine above is what
protects you everywhere else.

## What it catches

Names from your list, South African ID numbers (check-digit validated), SA phone
numbers, and email addresses. It will miss things and occasionally over-match, so
always read the coded output before pasting. Full detail in [SCOPE.md](SCOPE.md).

## Privacy

Everything runs locally. No network calls, no telemetry, no account. The one file
you must protect is the `.map.json` mapping - never paste it into an AI, email it,
or commit it. The included `.gitignore` keeps it (and your real name lists) out of
git.

## Licence

MIT. Use it, change it, give it away. See [LICENSE](LICENSE).

## Contributing

Issues and pull requests welcome, especially detectors for other countries' ID
and phone formats. Please never include real personal data in an issue or a test
fixture - use obviously fake values.
