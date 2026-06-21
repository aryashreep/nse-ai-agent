---
name: nse-ai-agent
description: Use this skill to analyze NSE-listed Indian stocks, screen for momentum opportunities, compare stocks, and generate research reports. Trigger when the user asks about Indian stocks, NSE analysis, momentum screening, sector rotation, or stock comparison. The skill invokes the nse-agent CLI and interprets its structured JSON output.
---

# NSE Agentic Research Skill

## When to invoke this skill

- User asks to analyze a specific NSE stock (e.g. "analyze ITC" or "what's the momentum on HDFC?")
- User asks to screen for momentum stocks
- User asks to compare two or more NSE stocks
- User asks about sector rotation in Indian markets

## How to run

Install once:
```bash
npx skills add aryashreep/nse-ai-agent
```

Run CLI commands:
```bash
npx nse-agent analyze <TICKER> --format json
npx nse-agent screen momentum --format json
npx nse-agent compare <TICKER1> <TICKER2> --format json
```

## Interpreting output

The CLI returns structured JSON. Parse the `momentum.momentum_score`, `technical.trend`, `risk.flags`, and `valuation` fields to answer the user's question.
Do not present raw numbers — interpret them in plain language.
Always include the `disclaimer` field at the end of your response to the user.
