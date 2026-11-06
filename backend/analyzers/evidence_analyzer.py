"""
Evidentiary & Attribution Analyzer.
Evaluates the quality of citations, quotes, institutional attributions, and identifies vague weasel words.
"""

import re


WEASEL_PHRASES = [
    r"\bsome (people|experts|scientists|critics|observers) (say|claim|believe|suggest)\b",
    r"\bmany (believe|think|feel|are saying)\b",
    r"\bit is (widely|commonly) (known|believed|said|rumored)\b",
    r"\banonymous (sources?|insiders?|officials?)\b",
    r"\bconfidential (sources?|documents?)\b",
    r"\bunnamed (scientists?|doctors?|experts?|officials?|whistleblowers?)\b",
    r"\b(secret|unknown) (sources?|informants?|documents?|researchers?)\b",
    r"\bcannot be named\b",
    r"\b(don'?t|doesn'?t) want you to know\b",
    r"\bthey say that\b",
    r"\bword on the street is\b",
    r"\beveryone knows that\b",
    r"\bstudies show that\b",  # Without naming the study or journal
    r"\breports are circulating\b",
]

INSTITUTIONAL_KEYWORDS = [
    r"\b(ministry|department|agency|bureau) of\b",
    r"\b(university|college|institute|academy|hospital|clinic)\b",
    r"\b(supreme court|high court|district court|judiciary|attorney general)\b",
    r"\b(police|fbi|cia|interpol|scotland yard|defense forces)\b",
    r"\b(parliament|congress|senate|white house|kremlin|downing street)\b",
    r"\b(world health organization|who|cdc|fda|ema|unicef|united nations|un)\b",
    r"\b(central bank|federal reserve|rbi|imf|world bank)\b",
    r"\bjournal of (medicine|science|nature|economics|law)\b",
    r"\b(spokesperson|spokeswoman|spokesman|representative|director|commissioner|minister)\b"
]

ATTRIBUTION_VERBS = [
    r"\b(said|stated|explained|announced|confirmed|reported|testified|concluded|noted|argued|declared|warned|stressed)\b"
]


def extract_quotes(text: str) -> list:
    """Extract direct quotes enclosed in standard or curved quotation marks."""
    # Match double quotes, typographic quotes, single quotes with reasonable length
    quotes = re.findall(r'["“]([^"”]{10,250})["”]', text)
    return quotes


def analyze_evidence(text: str) -> dict:
    """
    Analyzes sourcing, citations, named quotes, institutional references, and weasel words.
    Returns:
        dict: {
            "score": float (0-100),
            "quote_count": int,
            "institutional_ref_count": int,
            "weasel_word_count": int,
            "data_point_count": int,
            "quotes_found": list,
            "red_flags": list,
            "trust_indicators": list,
            "details": str
        }
    """
    red_flags = []
    trust_indicators = []

    text_lower = text.lower()
    total_words = len(re.findall(r"\b\w+\b", text))

    # 1. Direct Quotes Extraction
    quotes = extract_quotes(text)
    quote_count = len(quotes)

    # 2. Institutional References
    inst_matches = []
    for pattern in INSTITUTIONAL_KEYWORDS:
        found = re.findall(pattern, text_lower)
        if found:
            inst_matches.extend(found)
    inst_ref_count = len(inst_matches)

    # 3. Weasel Words & Vague Claims
    weasel_matches = []
    for pattern in WEASEL_PHRASES:
        found = re.findall(pattern, text_lower)
        if found:
            weasel_matches.extend(found)
    weasel_count = len(weasel_matches)

    # 4. Numerical Specificity (Dates, percentages, currencies, specific figures)
    data_points = re.findall(r"(\b\d+(\.\d+)?%|\$\d+(\.\d+)?|\b\d{4}\b|\b\d+,\d+|\b(january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2})", text_lower)
    data_count = len(data_points)

    # 5. Evaluate Trust & Red Flags
    if quote_count >= 2:
        trust_indicators.append(f"Contains {quote_count} direct quotes from sources or participants.")
    elif total_words > 120 and quote_count == 0:
        red_flags.append("No direct quotes or primary statements found in an extended news text.")

    if inst_ref_count >= 2:
        trust_indicators.append(f"Cites institutional bodies, officials, or academic entities ({inst_ref_count} references).")
    elif total_words > 100 and inst_ref_count == 0:
        red_flags.append("Lacks attribution to recognized official bodies, universities, or verified agencies.")

    if weasel_count >= 2:
        red_flags.append(f"Multiple vague weasel phrases found ('some say', 'unnamed sources', 'it is believed'). Typical of unsubstantiated rumors.")

    if data_count >= 3:
        trust_indicators.append(f"Includes specific quantitative details, dates, or empirical figures ({data_count} data points).")

    # 6. Calculate Evidence Score
    # Baseline for text
    score = 50.0

    # Add quote credit
    score += min(25.0, quote_count * 12.0)
    # Add institutional credit
    score += min(20.0, inst_ref_count * 6.0)
    # Add data points
    score += min(10.0, data_count * 2.5)

    # Subtract weasel words penalty
    score -= min(40.0, weasel_count * 14.0)

    # Penalty for articles with zero quotes or institutions
    if quote_count == 0 and inst_ref_count == 0:
        score -= 20.0

    score = max(5.0, min(100.0, score))

    sample_quotes = [q.strip() for q in quotes[:3]]

    return {
        "score": round(score, 1),
        "quote_count": quote_count,
        "institutional_ref_count": inst_ref_count,
        "weasel_word_count": weasel_count,
        "data_point_count": data_count,
        "quotes_found": sample_quotes,
        "red_flags": red_flags,
        "trust_indicators": trust_indicators,
        "details": f"Attribution strength: {score:.1f}/100 with {quote_count} quotes and {inst_ref_count} institutional references."
    }
