# Phase 75 — Token Counting + Cost Estimation Module

**Version:** 1.1 | **Tier:** Micro | **Date:** 2026-03-28

## Goal
Build a token counting and cost estimation utility using `client.messages.count_tokens()`. Pre-compute costs before sending requests. Demonstrates the count_tokens API for budget planning.

CLI: `python main.py --input data/compounds.csv --n 3`

Outputs: token_counts.json, cost_report.txt

## Logic
1. Load compounds and build prompts of varying complexity (simple, medium, detailed)
2. Use `client.messages.count_tokens()` to count input tokens without making a generation call
3. Estimate output tokens based on task type
4. Calculate cost per request and total cost across models (Haiku, Sonnet, Opus)
5. Report cost breakdown and batch budget estimates

## Key Concepts
- `client.messages.count_tokens()` API — count tokens without generation
- Pre-request cost estimation for budget control
- Token-to-cost mapping for different models
- Prompt complexity analysis (simple 51 tok, medium 95 tok, detailed 151 tok)

## Verification Checklist
- [x] count_tokens called successfully (no generation)
- [x] Cost estimates for multiple prompt sizes
- [x] Haiku vs Sonnet vs Opus cost comparison
- [x] $0.00 API cost (count_tokens is free)
- [x] --help works

## Results
| Task | Input Tokens | Haiku Cost | Sonnet Cost | Opus Cost |
|------|-------------|------------|-------------|-----------|
| simple_extract | 51 | $0.000241 | $0.000903 | $0.004515 |
| detailed_review | 95 | $0.001276 | $0.004785 | $0.023925 |
| full_analysis | 151 | $0.003321 | $0.012453 | $0.062265 |

Batch estimate (45 compounds, simple_extract):
- Haiku: $0.011 | Sonnet: $0.041 | Opus: $0.203

Key findings:
- count_tokens API works on `client.messages.count_tokens()` (not beta)
- Returns `MessageTokensCount(input_tokens=N)` — simple, clean
- Opus is 18.7x more expensive than Haiku for simple extraction
- Output tokens dominate cost (even at 50 tokens, output > input cost for all models)
- Zero generation cost — count_tokens is genuinely free

## Risks
- Output token estimation is approximate (actual may vary 2-3x)
- count_tokens counts system + user messages but not tool definitions
