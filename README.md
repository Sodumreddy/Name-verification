Name Verification Application
=============================

This is a small, self-contained application for a technical screen. It has two independent capabilities:

- A **Target Name Generator** that produces a single name from a free-form prompt and stores it as the latest target name.
- A **Name Verifier** that decides whether a candidate name matches the latest target name using deterministic fuzzy matching.

The verifier treats the generator as a black box and only uses the latest generated name string (no prompt, no generator logic, no shared LLM state).

## Running locally

From this project root:

```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
```

### 1. Generate a target name

```bash
python -m name_verification.cli generate "Please generate a random Arabic sounding name with an Al and ibn both involved. The name shouldn't be longer than 5 words."
```

This prints the generated name and stores it as the latest target name.

### 2. Verify a candidate name

```bash
python -m name_verification.cli verify "Tlyer Bilha"
```

This prints:

- latest target name
- candidate name
- match (boolean)
- confidence (0–1)
- short explanation

If you verify before generating, you get a clear error: the verifier sees that no latest name exists and does not attempt to generate one.

## Running tests

The provided test suite encodes the 30 (target, candidate, expected match) examples from the prompt.

```bash
pytest -q
```



