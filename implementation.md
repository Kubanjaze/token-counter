# Phase 75 — Token Counting + Cost Estimation Module

**Version:** 1.0 | **Tier:** Micro | **Date:** 2026-03-28

## Goal
Build a token counting and cost estimation utility using `client.messages.count_tokens()`. Pre-compute costs before sending requests. Demonstrates the count_tokens API for budget planning.

CLI: `python main.py --input data/compounds.csv --n 3`

Outputs: token_counts.json, cost_report.txt

## Logic
1. Load compounds and build prompts of varying complexity (simple, medium, detailed)
2. Use `client.messages.count_tokens()` to count input tokens without making a generation call
3. Estimate output tokens based on task type
4. Calculate cost per request and total cost across models (Haiku, Sonnet)
5. Report cost breakdown

## Key Concepts
- `client.messages.count_tokens()` API — count tokens without generation
- Pre-request cost estimation for budget control
- Token-to-cost mapping for different models
- Prompt complexity analysis

## Verification Checklist
- [ ] count_tokens called successfully (no generation)
- [ ] Cost estimates for multiple prompt sizes
- [ ] Haiku vs Sonnet cost comparison
- [ ] $0.00 API cost (count_tokens is free)
- [ ] --help works

## Risks
- count_tokens endpoint may have different billing (currently free)
- Output token estimation is approximate
