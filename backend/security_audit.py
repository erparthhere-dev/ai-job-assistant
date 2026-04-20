import os
import re
import sys

print("=" * 55)
print("  AI Job Assistant — Secrets Security Audit")
print("=" * 55)

issues = []
warnings = []
passed = []

env_path = os.path.join(os.path.dirname(__file__), ".env")

# Check 1: .env file exists
if not os.path.exists(env_path):
    issues.append(".env file not found")
else:
    passed.append(".env file exists")
    with open(env_path) as f:
        lines = f.readlines()

    for i, line in enumerate(lines, 1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        # Check 2: No hardcoded keys in .env committed to git
        if re.search(r"sk-[a-zA-Z0-9]{20,}", line):
            warnings.append(f"Line {i}: OpenAI key detected — ensure .env is in .gitignore")

        # Check 3: Empty required keys
        if "=" in line:
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip()
            if key in ["OPENAI_API_KEY", "RAPIDAPI_KEY"] and not value:
                issues.append(f"Line {i}: Required key '{key}' is empty")
            elif value:
                passed.append(f"Key '{key}' is set")

# Check 4: .gitignore has .env
gitignore_path = os.path.join(os.path.dirname(__file__), "..", ".gitignore")
if os.path.exists(gitignore_path):
    with open(gitignore_path) as f:
        gitignore = f.read()
    if ".env" in gitignore:
        passed.append(".env is listed in .gitignore")
    else:
        issues.append(".env is NOT in .gitignore — secrets could be committed to git!")
else:
    warnings.append(".gitignore not found")

# Check 5: No .env committed to git
env_in_git = os.popen("git ls-files backend/.env .env 2>/dev/null").read().strip()
if env_in_git:
    issues.append(f".env is tracked by git: {env_in_git} — remove immediately!")
else:
    passed.append(".env is not tracked by git")

# ── Report ────────────────────────────────────────────────────
print(f"\n✅ PASSED ({len(passed)})")
for p in passed:
    print(f"   ✓ {p}")

if warnings:
    print(f"\n⚠️  WARNINGS ({len(warnings)})")
    for w in warnings:
        print(f"   ! {w}")

if issues:
    print(f"\n❌ ISSUES ({len(issues)})")
    for iss in issues:
        print(f"   ✗ {iss}")
else:
    print(f"\n🎉 No critical issues found!")

print("\n" + "=" * 55)

# ── LLM Output Filter Test ────────────────────────────────────
print("\n🔍 Testing LLM Output Filter...")
from services.security import filter_llm_output

test_cases = [
    ("Hello, contact me at john@example.com for details.", "email PII"),
    ("My SSN is 123-45-6789 please keep it safe.", "SSN PII"),
    ("Call me at 555-123-4567 anytime.", "phone PII"),
    ("This is a clean professional cover letter.", "clean text"),
]

for text, label in test_cases:
    cleaned, warnings = filter_llm_output(text, source="test")
    status = "⚠️  FILTERED" if warnings else "✅ CLEAN"
    print(f"   {status} [{label}]: {cleaned[:60]}")

print("\n" + "=" * 55)
sys.exit(1 if issues else 0)