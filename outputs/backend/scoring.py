"""
Mock LLM + evaluation engine.

This is the piece that gets swapped out for a real model call in production.
The contract it must preserve: a response is generated ALONGSIDE a list of
claim spans, each traced to a source sentence (or flagged as unattributed).
That contract is what makes faithfulness scoring explainable downstream —
see design-document.md, section 3.
"""
import random

FABRICATIONS = [
    "this also applies retroactively to contracts signed before 2023",
    "a dedicated account manager will personally approve every request within the hour",
    "this policy was updated last week to remove all approval requirements",
    "there is an unlimited grace period for all tiers",
]


def mock_generate(prompt: str, source_name: str, source_content: str) -> dict:
    sentences = [s.strip() for s in source_content.split(". ") if s.strip()]
    used = [s for s in sentences if random.random() > 0.4][:3]
    if not used and sentences:
        used = sentences[:1]

    hallucinate = random.random() > 0.55
    spans = [{"text": s + ("." if not s.endswith(".") else ""), "status": "verified"} for s in used]

    if hallucinate:
        fab = random.choice(FABRICATIONS)
        fab = fab[0].upper() + fab[1:] + "."
        spans.append({"text": fab, "status": random.choice(["unverified", "contradicted"])})
    else:
        spans.append({"text": "No further exceptions apply beyond what's documented.", "status": "verified"})

    random.shuffle(spans)

    html_parts = [f'<mark class="{s["status"]}">{s["text"]}</mark>' for s in spans]
    html = f'Based on <b>{source_name}</b>: ' + " ".join(html_parts)

    verified_count = sum(1 for s in spans if s["status"] == "verified")
    faith = max(20, round(100 * verified_count / len(spans)))
    rel = round(random.uniform(75, 97))
    comp = round(random.uniform(60, 95))

    flagged_span = next((s for s in spans if s["status"] != "verified"), None)
    if flagged_span:
        explain = (
            f'{verified_count}/{len(spans)} claims were traced to indexed chunks in "{source_name}". '
            f'The remaining claim ("{flagged_span["text"]}") could not be matched to any source chunk '
            f'above the similarity threshold and is flagged as {flagged_span["status"]}.'
        )
    else:
        explain = (
            f'{verified_count}/{len(spans)} claims were traced directly to indexed chunks in '
            f'"{source_name}". No unsupported claims detected.'
        )

    return {
        "html": html,
        "faith": faith,
        "rel": rel,
        "comp": comp,
        "latency": round(random.uniform(380, 1200)),
        "tokens": round(random.uniform(60, 220)),
        "explain": explain,
        "spans": spans,
    }