from bot.verdict import simple_verdict

def test_simple_verdict_supported():
    claim = "Central bank cuts interest rates"
    retrieved = [
        {"text": "Today the central bank cuts interest rates by 50 basis points.", "title": "Rate cut"},
        {"text": "Analysis: central bank future policy", "title": "Policy"},
    ]
    verdict = simple_verdict(claim, retrieved, {"k": 2, "filtered": 0, "latency_s": 0.01})
    assert verdict.verdict in {"SUPPORTED", "NEEDS_MORE_EVIDENCE"}
