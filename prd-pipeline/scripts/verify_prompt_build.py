#!/usr/bin/env python3
"""
Verify that the generated PRD prompt correctly includes:
- Step 3 config: product context, business goals, constraints, audience, tone, roadmap
- Dovetail data (user research summary)
- Productboard data (product feedback summary)

Run from prd-pipeline: python scripts/verify_prompt_build.py
"""
from __future__ import annotations

import sys
from pathlib import Path

# prd-pipeline as project root for imports
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.prompt_builder import build_prompt_from_summaries
from services.prompt_builder.models import PromptBuilderConfig


def main() -> int:
    # Step 3–like config (what user would enter)
    product_context = "Our B2B SaaS helps teams manage compliance workflows and audit trails."
    business_goals = "Increase enterprise adoption by 30%; reduce support tickets for compliance questions."
    constraints = "Must ship by Q2; no new infra; support existing SSO only."

    config = PromptBuilderConfig(
        prd_template_id="default",
        product_context=product_context,
        business_goals=business_goals,
        constraints=constraints,
        audience_type="executives",
        output_tone="concise",
        include_roadmap=True,
    )

    # Simulated summaries from Dovetail + Productboard (as run_pipeline would produce)
    dovetail_summary = (
        "- Project: Compliance Research 2024\n"
        "- Insight: Users want one-click export. Users want one-click export for audits.\n"
        "- Insight: Confusion about retention settings. Confusion about data retention settings."
    )
    productboard_summary = (
        "- Feature: Audit log export. Allow export of audit logs in CSV and PDF.\n"
        "- Note: Enterprise ask: SSO. Enterprise customers requesting SSO integration."
    )

    result = build_prompt_from_summaries(
        dovetail_summary=dovetail_summary,
        productboard_summary=productboard_summary,
        config=config,
    )

    prompt = result.prompt
    errors: list[str] = []

    # Step 3 config must appear in prompt
    if product_context not in prompt:
        errors.append("Product context from step 3 is missing from prompt")
    if business_goals not in prompt:
        errors.append("Business goals from step 3 are missing from prompt")
    if constraints not in prompt:
        errors.append("Constraints from step 3 are missing from prompt")

    # Audience and tone (strategy formats them)
    if "Executives" not in prompt:
        errors.append("Audience (executives) not found in prompt")
    if "Concise" not in prompt:
        errors.append("Output tone (concise) not found in prompt")

    # Roadmap section requested
    if "Roadmap" not in prompt and "roadmap" not in prompt.lower():
        errors.append("Roadmap section instruction not found in prompt")

    # Dovetail data
    if "User research (Dovetail)" not in prompt:
        errors.append("Dovetail section heading missing")
    if "Compliance Research 2024" not in prompt:
        errors.append("Dovetail project/content missing from prompt")
    if "one-click export" not in prompt and "retention" not in prompt.lower():
        errors.append("Dovetail insight content not present in prompt")

    # Productboard data
    if "Product feedback (Productboard)" not in prompt:
        errors.append("Productboard section heading missing")
    if "Audit log export" not in prompt:
        errors.append("Productboard feature content missing from prompt")
    if "SSO" not in prompt:
        errors.append("Productboard note content missing from prompt")

    if errors:
        print("FAIL: Prompt verification failed:")
        for e in errors:
            print("  -", e)
        print("\n--- Generated prompt (first 2000 chars) ---\n")
        print(prompt[:2000])
        return 1

    print("OK: Prompt is correctly built with:")
    print("  - Step 3 config: product context, business goals, constraints, audience, tone, roadmap")
    print("  - Dovetail user research section with project/insights content")
    print("  - Productboard product feedback section with features/notes content")
    print(f"  - Word count: {result.word_count}, sections: {result.sections}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
