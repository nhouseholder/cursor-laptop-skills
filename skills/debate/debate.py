#!/usr/bin/env python3
"""
Debate API — calls Gemini 3.1 Pro as the Challenger in a formalized debate.

Usage:
  python3 debate.py --topic "AI will replace radiologists" --round 1 --proposer "Opening statement..."
  python3 debate.py --topic "..." --round 2 --history '{"r1":{"proposer":"...","challenger":"..."}}' --proposer "Rebuttal..."
  python3 debate.py --topic "..." --verdict --history '{...}'
"""

import argparse
import json
import os
import sys
from pathlib import Path

MASTER_ENV = Path.home() / ".claude" / "credentials" / "master.env"

# Gemini 3.1 Pro — latest stable pro-tier model
MODEL = "gemini-3.1-pro-preview"
API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"


def load_env_var(key):
    val = os.environ.get(key)
    if val:
        return val
    if MASTER_ENV.is_file():
        for line in MASTER_ENV.read_text().splitlines():
            if line.startswith(f"{key}="):
                v = line.split("=", 1)[1].strip().strip('"').strip("'")
                if v:
                    return v
    return None


def call_gemini(prompt, api_key, model=MODEL, temperature=0.7, max_tokens=2048):
    """Call Gemini 3.1 Pro with a prompt and return the text response."""
    import subprocess

    url = f"{API_BASE}/{model}:generateContent?key={api_key}"
    payload = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": max_tokens,
        }
    })

    result = subprocess.run(
        ["curl", "-s", "--max-time", "60", "-X", "POST", url,
         "-H", "Content-Type: application/json", "-d", payload],
        capture_output=True, text=True
    )

    if result.returncode != 0:
        return f"[ERROR] curl exit code {result.returncode}"

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        return f"[ERROR] JSON parse failed: {result.stdout[:300]}"

    if "error" in data:
        err = data["error"]
        return f"[ERROR] {err.get('code', '?')}: {err.get('message', str(err))}"

    try:
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError) as e:
        return f"[ERROR] Unexpected response: {e} — {result.stdout[:300]}"


def build_round_prompt(topic, role, round_num, proposer_text, history_json):
    """Build the full prompt for Gemini as Challenger."""
    if round_num == 1 and not history_json:
        # Round 1 — no prior history
        return f"""\
You are the CHALLENGER in a formal debate.

## TOPIC
{topic}

## RULES
- You take the OPPOSING position to the Proposer.
- You are intellectually formidable — argue with evidence, logic, and precision.
- Do not concede without counter-argument. If the Proposer makes a strong point, acknowledge it but explain why it's insufficient.
- Keep your response to 300-500 words. Be concise and punchy.
- End with a single sentence "CHALLENGE" that distills your strongest counter-position into one line.

## PROPOSER'S OPENING STATEMENT
{proposer_text}

## YOUR RESPONSE AS CHALLENGER
"""

    # Rounds 2-3 — full history
    try:
        hist = json.loads(history_json) if isinstance(history_json, str) else history_json
    except json.JSONDecodeError:
        hist = {}

    history_lines = []
    for r in sorted(hist.keys()):
        entry = hist[r]
        history_lines.append(f"=== ROUND {r[-1]} ===")
        history_lines.append(f"PROPOSER: {entry.get('proposer', '')}")
        history_lines.append(f"CHALLENGER: {entry.get('challenger', '')}")
        history_lines.append("")

    history_text = "\n".join(history_lines)

    return f"""\
You are the CHALLENGER in a formal debate.

## TOPIC
{topic}

## RULES
- You take the OPPOSING position to the Proposer.
- You are intellectually formidable — argue with evidence, logic, and precision.
- Do not concede without counter-argument. If the Proposer makes a strong point, acknowledge it but explain why it's insufficient.
- You CAN change your argument or introduce NEW evidence each round — you are not locked into prior reasoning unless the Proposer's point demands a response.
- Keep your response to 300-500 words. Be concise and punchy.
- End with a single sentence "CHALLENGE" that distills your strongest counter-position into one line.

## DEBATE HISTORY
{history_text}

## PROPOSER'S REBUTTAL (Round {round_num})
{proposer_text}

## YOUR RESPONSE AS CHALLENGER (Round {round_num})
"""


def build_verdict_prompt(topic, history_json):
    """Build the final verdict prompt."""
    try:
        hist = json.loads(history_json) if isinstance(history_json, str) else history_json
    except json.JSONDecodeError:
        hist = {}

    history_lines = []
    for r in sorted(hist.keys()):
        entry = hist[r]
        history_lines.append(f"=== ROUND {r[-1]} ===")
        history_lines.append(f"PROPOSER: {entry.get('proposer', '')}")
        history_lines.append(f"CHALLENGER: {entry.get('challenger', '')}")
        history_lines.append("")

    history_text = "\n".join(history_lines)

    return f"""\
You are the FINAL JUDGE of a formal debate. Review the full transcript and render a verdict.

## TOPIC
{topic}

## DEBATE HISTORY
{history_text}

## JUDGING CRITERIA
Score 1-10 in each:
- **Argument strength** (evidence, reasoning, internal consistency)
- **Rebuttal quality** (did they address the other side's points?)
- **Persuasiveness** (clarity, framing, rhetorical force)

## VERDICT FORMAT
Return ONLY a JSON block — no surrounding text:

```json
{{
  "winner": "Proposer | Challenger | Draw",
  "proposer_score": {{ "argument": N, "rebuttal": N, "persuasiveness": N, "total": N }},
  "challenger_score": {{ "argument": N, "rebuttal": N, "persuasiveness": N, "total": N }},
  "summary": "2-3 sentence analysis of who won and why",
  "strongest_moment": "Quote the single most effective point from either side",
  "weakest_argument": "Which argument was least convincing and why"
}}
```
"""


def main():
    parser = argparse.ArgumentParser(description="Debate with Gemini 3.1 Pro")
    parser.add_argument("--topic", required=True, help="Debate topic")
    parser.add_argument("--round", type=int, choices=[1, 2, 3], help="Current round")
    parser.add_argument("--proposer", help="Claude's position/rebuttal text")
    parser.add_argument("--history", help="JSON string of debate history")
    parser.add_argument("--verdict", action="store_true", help="Get final verdict")
    parser.add_argument("--temperature", type=float, default=0.7, help="LLM temperature")
    parser.add_argument("--mode", choices=["challenger", "judge"], default="challenger", help="Gemini role")
    args = parser.parse_args()

    api_key = load_env_var("GEMINI_API_KEY_PAID") or load_env_var("GEMINI_API_KEY")
    if not api_key:
        print("[FATAL] No GEMINI_API_KEY_PAID or GEMINI_API_KEY found in env or master.env", file=sys.stderr)
        sys.exit(1)

    if args.verdict:
        prompt = build_verdict_prompt(args.topic, args.history or "{}")
        response = call_gemini(prompt, api_key, temperature=0.3, max_tokens=1024)
    elif args.round and args.proposer:
        prompt = build_round_prompt(args.topic, args.mode, args.round, args.proposer, args.history or "{}")
        response = call_gemini(prompt, api_key, temperature=args.temperature, max_tokens=2048)
    else:
        print("[FATAL] Provide --round N + --proposer, or --verdict", file=sys.stderr)
        sys.exit(1)

    print(response)


if __name__ == "__main__":
    main()