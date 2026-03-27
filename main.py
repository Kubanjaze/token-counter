import sys
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

import argparse, os, json, warnings
warnings.filterwarnings("ignore")
import pandas as pd
from dotenv import load_dotenv
import anthropic

load_dotenv()
os.environ.setdefault("ANTHROPIC_API_KEY", os.getenv("ANTHROPIC_API_KEY", ""))

# Pricing per million tokens (USD)
PRICING = {
    "claude-haiku-4-5-20251001": {"input": 0.80, "output": 4.0},
    "claude-sonnet-4-20250514": {"input": 3.0, "output": 15.0},
    "claude-opus-4-20250514": {"input": 15.0, "output": 75.0},
}

# Estimated output tokens by task type
OUTPUT_ESTIMATES = {
    "simple_extract": 50,
    "detailed_review": 300,
    "full_analysis": 800,
}


def build_prompts(df: pd.DataFrame) -> list[dict]:
    """Build prompts of varying complexity from compound data."""
    prompts = []

    # Simple: single compound extraction
    row = df.iloc[0]
    prompts.append({
        "label": "simple_extract",
        "system": "Extract compound properties as JSON.",
        "messages": [{"role": "user", "content": f"Compound: {row['compound_name']}, SMILES: {row['smiles']}. Extract name and scaffold family."}],
        "est_output": OUTPUT_ESTIMATES["simple_extract"],
    })

    # Medium: peer review of a hypothesis
    compounds_str = "\n".join(f"  {r['compound_name']}: pIC50={r['pic50']:.2f}" for _, r in df.iterrows())
    prompts.append({
        "label": "detailed_review",
        "system": "You are a peer reviewer for SAR hypotheses. Provide verdict, evidence, and suggestions.",
        "messages": [{"role": "user", "content": f"HYPOTHESIS: EWG groups increase potency.\n\nDATA:\n{compounds_str}\n\nReview critically."}],
        "est_output": OUTPUT_ESTIMATES["detailed_review"],
    })

    # Detailed: full SAR analysis with all compounds
    all_data = df.to_csv(index=False)
    prompts.append({
        "label": "full_analysis",
        "system": "You are a medicinal chemistry expert. Analyze the full compound library and identify SAR trends, activity cliffs, and optimization opportunities.",
        "messages": [{"role": "user", "content": f"Analyze this compound library:\n\n{all_data}\n\nProvide a comprehensive SAR analysis."}],
        "est_output": OUTPUT_ESTIMATES["full_analysis"],
    })

    return prompts


def main():
    parser = argparse.ArgumentParser(
        description="Phase 75 — Token counting + cost estimation module",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--input", required=True, help="Compounds CSV")
    parser.add_argument("--n", type=int, default=3, help="Number of compounds to include")
    parser.add_argument("--output-dir", default="output", help="Output directory")
    args = parser.parse_args()
    os.makedirs(args.output_dir, exist_ok=True)

    df = pd.read_csv(args.input).head(args.n)
    client = anthropic.Anthropic()
    prompts = build_prompts(df)

    print(f"\nPhase 75 — Token Counting + Cost Estimation")
    print(f"Compounds: {len(df)} | Prompts: {len(prompts)} | Models: {len(PRICING)}\n")

    results = []

    for p in prompts:
        # Count tokens via API (no generation, free)
        count_result = client.messages.count_tokens(
            model="claude-haiku-4-5-20251001",
            system=p["system"],
            messages=p["messages"],
        )
        input_tokens = count_result.input_tokens
        est_output = p["est_output"]

        print(f"Prompt: {p['label']}")
        print(f"  Input tokens: {input_tokens}")
        print(f"  Est. output tokens: {est_output}")

        model_costs = {}
        for model_id, pricing in PRICING.items():
            in_cost = input_tokens / 1e6 * pricing["input"]
            out_cost = est_output / 1e6 * pricing["output"]
            total = in_cost + out_cost
            model_name = model_id.split("-")[1]
            model_costs[model_name] = {
                "input_cost": round(in_cost, 6),
                "output_cost": round(out_cost, 6),
                "total_cost": round(total, 6),
            }
            print(f"  {model_name:>8s}: ${total:.6f} (in=${in_cost:.6f} + out=${out_cost:.6f})")

        results.append({
            "label": p["label"],
            "input_tokens": input_tokens,
            "est_output_tokens": est_output,
            "costs": model_costs,
        })
        print()

    # Budget planning: estimate cost for full library (45 compounds)
    print("=" * 50)
    print("BUDGET PLANNING — Full library (45 compounds)\n")

    report = f"Phase 75 — Token Counting + Cost Estimation\n{'='*50}\n\n"

    for r in results:
        report += f"Task: {r['label']}\n"
        report += f"  Input tokens: {r['input_tokens']} | Est. output: {r['est_output_tokens']}\n"
        for model, costs in r["costs"].items():
            report += f"  {model}: ${costs['total_cost']:.6f}/call\n"
        report += "\n"

    # Scale to 45-compound batch
    report += "Batch cost estimate (45 compounds, simple_extract):\n"
    simple = next(r for r in results if r["label"] == "simple_extract")
    for model, costs in simple["costs"].items():
        batch_cost = costs["total_cost"] * 45
        report += f"  {model}: ${batch_cost:.4f} (45 x ${costs['total_cost']:.6f})\n"
    report += "\n"

    report += f"API calls made: 0 (count_tokens only)\nActual cost: $0.00\n"
    print(report)

    with open(os.path.join(args.output_dir, "token_counts.json"), "w") as f:
        json.dump(results, f, indent=2)
    with open(os.path.join(args.output_dir, "cost_report.txt"), "w") as f:
        f.write(report)
    print("Done.")


if __name__ == "__main__":
    main()
