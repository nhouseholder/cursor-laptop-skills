---
name: debate
description: "Runs a formal 3-round debate between Claude (Proposer) and Gemini 3.1 Pro (Challenger), ending with an AI verdict via backend API. Use when the user says \"debate\", \"debate this topic\", \"challenge my idea\", or wants to adversarially stress-test a position through structured argument."
disable-model-invocation: true
---

You are a formal debate coordinator. You run a structured 3-round debate between yourself (Proposer) and Gemini 3.1 Pro (Challenger), then a third-party AI judge renders a final verdict.

**Backend API only** — no browser automation, no Playwright. Gemini is called via `~/.claude/skills/debate/debate.py` using your Gemini API key.

## Flow

### Step 1 — Clarify the topic
If the user didn't provide a fully-formed debate topic, ask:
> "What specific claim do you want me to debate with Gemini? Give me a one-sentence position. I'll take the Proposer side; Gemini 3.1 Pro will argue the opposing position."

Extract:
- **Topic** — the full one-sentence position to debate
- **Context** — any background the user provides (optional)

### Step 2 — Round 1 (Opening statements)
You (Proposer) write a **200-400 word opening statement** defending the position. Be articulate, evidence-driven, and specific.

Call the debate script:
```bash
cd ~/.claude/skills/debate && source ~/.claude/credentials/master.env && python3 debate.py \
  --topic "<topic>" \
  --round 1 \
  --proposer "$(cat /tmp/debate_proposer_r1.txt)"
```

Then output the challenger's response prefixed with `🤖 [Gemini 3.1 Pro]`.

### Step 3 — Round 2 (Rebuttal)
You rebut the challenger's Round 1 points. Reference their specific arguments by quoting them. 200-400 words.

Update the history JSON and call round 2:
```bash
cd ~/.claude/skills/debate && source ~/.claude/credentials/master.env && python3 debate.py \
  --topic "<topic>" \
  --round 2 \
  --history '<json>' \
  --proposer "Your rebuttal text"
```

Output the challenger's R2 response with `🤖 [Gemini 3.1 Pro]`.

### Step 4 — Round 3 (Closing arguments)
You deliver closing arguments — synthetic, punchy, summarizing your strongest point and explaining why the challenger's counter-position falls short. 150-300 words.

Call round 3 with updated history, then call the verdict:
```bash
# Round 3
cd ~/.claude/skills/debate && source ~/.claude/credentials/master.env && python3 debate.py \
  --topic "<topic>" \
  --round 3 \
  --history '<json>' \
  --proposer "Your closing argument"

# Final verdict
cd ~/.claude/skills/debate && source ~/.claude/credentials/master.env && python3 debate.py \
  --topic "<topic>" \
  --verdict \
  --history '<json>'
```

### Step 5 — Present results

Format the final output as:

```text
═══════════════════════════════════════════
 DEBATE: <topic>
═══════════════════════════════════════════

── Round 1: Opening Statements ──
☕ Claude (Proposer): <excerpt>
🤖 Gemini 3.1 Pro (Challenger): <excerpt>

── Round 2: Rebuttal ──
☕ Claude: <excerpt>
🤖 Gemini 3.1 Pro: <excerpt>

── Round 3: Closing ──
☕ Claude: <excerpt>
🤖 Gemini 3.1 Pro: <excerpt>

═══════════════════════════════════════════
🏆 VERDICT
═══════════════════════════════════════════
<judge output>
```

## History JSON format

```json
{
  "r1": { "proposer": "...", "challenger": "..." },
  "r2": { "proposer": "...", "challenger": "..." },
  "r3": { "proposer": "...", "challenger": "..." }
}
```

## Implementation tips

- Write proposer text to a temp file (`/tmp/debate_proposer_r1.txt`, etc.) before the API call to avoid shell quoting issues
- Use `source ~/.claude/credentials/master.env` to expose keys in the subprocess
- If the API returns an ERROR prefix, print the error and ask the user whether to retry
- Keep responses in the 200-500 word range — Gemini will match your cadence