"""
Claim Extraction & Verification Engine.
Extracts factual claims, identifies testable assertions, and generates targeted fact-checking search links.
"""

import re
import urllib.parse


def split_into_sentences(text: str) -> list:
    """Split text into sentences cleanly."""
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    return [s.strip() for s in sentences if len(s.strip()) > 15]


def extract_claims(headline: str, body: str) -> list:
    """
    Extract key factual assertions and generate fact-checking search links.
    Returns:
        list of dicts: [
            {
                "claim_text": str,
                "type": "Headline Claim" | "Factual Assertion" | "Quote / Statement",
                "google_factcheck_url": str,
                "news_search_url": str,
                "verification_tip": str
            }
        ]
    """
    claims = []

    # 1. Headline is always primary claim
    if headline and len(headline.strip()) > 10:
        encoded_h = urllib.parse.quote_plus(headline.strip())
        claims.append({
            "claim_text": headline.strip(),
            "type": "Primary Headline Claim",
            "google_factcheck_url": f"https://toolbox.google.com/factcheck/explorer/search/listresults?query={encoded_h}",
            "news_search_url": f"https://www.google.com/search?q={encoded_h}&tbm=nws",
            "verification_tip": "Check if major international news wire services (Reuters, AP, BBC) report this same headline."
        })

    # 2. Extract notable sentences from body
    sentences = split_into_sentences(body)
    claim_indicators = [
        r"\b(announced|claimed|discovered|invented|proved|revealed|warned|died|killed|signed|passed|voted|arrested|banned)\b",
        r"\b(\d+ percent|\$\d+|\bmillion\b|\bbillion\b)\b",
        r"\b(confirmed that|found that|stated that|shows that)\b"
    ]

    selected_sentences = []
    for s in sentences:
        for ind in claim_indicators:
            if re.search(ind, s, re.IGNORECASE):
                if s not in selected_sentences and len(s) < 220:
                    selected_sentences.append(s)
                break
        if len(selected_sentences) >= 4:
            break

    for s in selected_sentences:
        encoded_s = urllib.parse.quote_plus(s[:100])
        claims.append({
            "claim_text": s,
            "type": "Key Factual Assertion",
            "google_factcheck_url": f"https://toolbox.google.com/factcheck/explorer/search/listresults?query={encoded_s}",
            "news_search_url": f"https://www.google.com/search?q={encoded_s}&tbm=nws",
            "verification_tip": "Cross-reference with primary government records, regulatory filings, or scientific publications."
        })

    return claims
