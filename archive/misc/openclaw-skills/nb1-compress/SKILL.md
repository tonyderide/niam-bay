---
name: nb1-compress
description: "Compress a message using the NB-1 codec (Niam-Bay compression). Takes a message as input, runs the NB-1 encoder, and returns the compressed representation. Use when you need to compress text for storage or transmission."
user-invocable: true
metadata:
  { "openclaw": { "requires": { "bins": ["python"] } } }
---

# nb1-compress — NB-1 Codec Compression

You compress messages using the Niam-Bay NB-1 codec.

## Usage

When invoked with `/nb1-compress <message>`, do the following:

### Step 1 — Locate the codec

Check for the NB-1 codec:

```bash
ls C:/niam-bay/nb1/ 2>/dev/null || ls C:/niam-bay/codec/ 2>/dev/null || ls C:/niam-bay/naissance-src/nb1/ 2>/dev/null
```

### Step 2 — Run compression

If the codec script exists:

```bash
cd C:/niam-bay && python nb1/compress.py "<message>"
```

Or if it uses a different entry point, adapt accordingly.

### Step 3 — Return result

Present:

- **Original**: the input message
- **Compressed**: the NB-1 encoded output
- **Ratio**: compression ratio if available

## Fallback

If the NB-1 codec does not exist yet, report this honestly and suggest it as a project to build. The codec concept is part of the Niam-Bay vision — a way to compress meaning, not just bytes.
