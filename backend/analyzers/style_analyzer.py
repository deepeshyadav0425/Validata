"""
Linguistic, Stylistic & Clickbait Analyzer.
Evaluates emotional manipulation, sensationalism, punctuation anomalies, and headline-body discrepancy.
"""

import re
import math


CLICKBAIT_PATTERNS = [
    r"\byou won'?t believe\b",
    r"\bshocking\b",
    r"\bwhat happens next\b",
    r"\bwill blow your mind\b",
    r"\bdoctors (hate|stunned|speechless|don'?t want you to know)\b",
    r"\b(don'?t|doesn'?t) want you to know\b",
    r"\bsecret (cure|formula|remedy|trick|loophole|researchers?)\b",
    r"\bspread (this|the word) before (it'?s|it is) (banned|deleted|taken down)\b",
    r"\bforward (this|to everyone|to your family)\b",
    r"\bmainstream media won'?t tell you\b",
    r"\bthey are lying to you\b",
    r"\bboth sides don'?t want you to see\b",
    r"\bthis one simple trick\b",
    r"\bgone viral\b",
    r"\bcan change your life forever\b",
    r"\bunbelievable results?\b",
    r"\bexposed:\b",
    r"\bbombshell (report|proof|leak|discovery)\b",
    r"\bwake up sheeple\b",
    r"\bguaranteed to (cure|heal|fix|eliminate)\b",
]

SENSATIONAL_WORDS = {
    "shocking", "unbelievable", "mindblowing", "mind-blowing", "miracle",
    "catastrophic", "deadly", "monstrous", "terrifying", "explosive",
    "horrifying", "nightmare", "disaster", "apocalyptic", "bloodbath",
    "furious", "insane", "evil", "diabolical", "scandalous", "jaw-dropping",
    "treason", "conspiracy", "hoax", "coverup", "cover-up", "bizarre",
    "miraculous", "banned", "censored", "destroyed", "annihilated"
}

JOURNALISTIC_TONE_WORDS = {
    "stated", "reported", "confirmed", "according", "preliminary",
    "investigation", "analysis", "official", "spokesperson", "statement",
    "witnesses", "data", "indicated", "suggested", "scheduled",
    "concluded", "evidence", "findings", "published", "spokeswoman"
}


def compute_headline_body_similarity(headline: str, body: str) -> float:
    """
    Compute word overlap between headline keywords and body keywords
    to detect bait-and-switch clickbait.
    """
    if not headline or not body:
        return 0.8  # neutral default

    stop_words = {
        "the", "a", "an", "and", "or", "in", "on", "at", "to", "for", "of",
        "with", "by", "is", "are", "was", "were", "it", "this", "that", "from",
        "as", "be", "has", "have", "had", "will", "would", "can", "could"
    }

    h_words = [w.lower() for w in re.findall(r"\b[a-zA-Z]{3,}\b", headline) if w.lower() not in stop_words]
    b_words = [w.lower() for w in re.findall(r"\b[a-zA-Z]{3,}\b", body) if w.lower() not in stop_words]

    if not h_words:
        return 0.8

    h_set = set(h_words)
    b_set = set(b_words)

    overlap = len(h_set.intersection(b_set)) / len(h_set)
    return overlap


def analyze_style(headline: str, body: str) -> dict:
    """
    Analyzes sensationalism, emotional bias, punctuation, capitalization, and clickbait.
    Returns:
        dict: {
            "score": float (0-100, where 100 = neutral/journalistic, 0 = pure clickbait/sensational),
            "clickbait_probability": float,
            "sensationalism_index": float,
            "all_caps_ratio": float,
            "exclamation_count": int,
            "red_flags": list,
            "trust_indicators": list,
            "headline_alignment": float
        }
    """
    red_flags = []
    trust_indicators = []

    combined_text = f"{headline} {body}".strip()
    words = re.findall(r"\b[a-zA-Z]+\b", combined_text)
    total_words = max(len(words), 1)

    # 1. Clickbait Headline Detection
    clickbait_matches = []
    headline_lower = headline.lower()
    for pattern in CLICKBAIT_PATTERNS:
        if re.search(pattern, headline_lower) or re.search(pattern, combined_text.lower()[:300]):
            match = re.search(pattern, headline_lower) or re.search(pattern, combined_text.lower()[:300])
            clickbait_matches.append(match.group(0))

    if clickbait_matches:
        red_flags.append(f"Clickbait phrase detected: '{clickbait_matches[0]}'.")

    # 2. Sensationalism & Hyperbolic Adjectives
    sensational_found = [w.lower() for w in words if w.lower() in SENSATIONAL_WORDS]
    sensational_ratio = len(sensational_found) / total_words

    if len(sensational_found) >= 4 or sensational_ratio > 0.03:
        top_sens = list(set(sensational_found))[:3]
        red_flags.append(f"High sensationalism detected ({', '.join(top_sens)}). Emotional framing exceeds journalistic standards.")
    elif len(sensational_found) == 0:
        trust_indicators.append("Restrained, measured vocabulary with minimal emotional hyperbole.")

    # 3. Capitalization Anomalies (ALL-CAPS screaming)
    # Check words with len >= 3
    caps_words = [w for w in words if len(w) >= 3 and w.isupper() and w not in {"USA", "UK", "NASA", "WHO", "FBI", "CIA", "UN", "COVID", "AI", "EU", "GDP"}]
    caps_ratio = len(caps_words) / total_words

    if len(caps_words) >= 3 or caps_ratio > 0.05:
        red_flags.append(f"Frequent capitalized words for emphasis ({', '.join(caps_words[:3])}). Typographic indicator of sensationalism.")

    # 4. Punctuation Anomalies (Multiple !!! or ??? or !? in text or headline)
    multi_punc = len(re.findall(r"[!?]{2,}", combined_text))
    headline_excl = len(re.findall(r"!", headline))
    total_excl = len(re.findall(r"!", combined_text))

    if headline_excl > 0:
        red_flags.append("Headline contains exclamation mark(s), which is rare in standard journalistic reporting.")
    if multi_punc > 0:
        red_flags.append(f"Excessive punctuation clusters found ('??', '!!'). Characteristic of social media forwards/rumors.")
    if total_excl == 0 and headline_excl == 0:
        trust_indicators.append("Objective headline punctuation; no sensational exclamation marks.")

    # 5. Journalistic Tone Words
    journalistic_matches = [w.lower() for w in words if w.lower() in JOURNALISTIC_TONE_WORDS]
    if len(journalistic_matches) >= 3:
        trust_indicators.append("Consistent use of standard attribution and reporting language.")

    # 6. Headline vs Body Alignment
    alignment = compute_headline_body_similarity(headline, body)
    if body and len(body.split()) > 40 and alignment < 0.35:
        red_flags.append("Headline-to-body divergence: The article body mentions few keywords from the headline (possible bait-and-switch).")

    # 7. Calculate Aggregated Style Score (0 - 100)
    # Start at 85 (neutral), subtract penalties, add bonuses
    score = 85.0
    score -= len(clickbait_matches) * 22.0
    score -= min(35.0, sensational_ratio * 400.0)
    score -= min(25.0, caps_ratio * 300.0)
    score -= min(20.0, (multi_punc * 6.0) + (headline_excl * 8.0))
    if alignment < 0.35 and len(body.split()) > 40:
        score -= 15.0

    if len(journalistic_matches) >= 3:
        score += 8.0
    if len(sensational_found) == 0 and total_words > 50:
        score += 7.0

    score = max(5.0, min(100.0, score))
    sensationalism_index = min(100.0, (sensational_ratio * 1000.0) + (len(clickbait_matches) * 25.0))
    clickbait_prob = max(0.0, min(1.0, (100.0 - score) / 100.0))

    return {
        "score": round(score, 1),
        "clickbait_probability": round(clickbait_prob, 2),
        "sensationalism_index": round(sensationalism_index, 1),
        "all_caps_words_count": len(caps_words),
        "exclamation_count": total_excl,
        "headline_alignment": round(alignment * 100, 1),
        "red_flags": red_flags,
        "trust_indicators": trust_indicators,
        "details": f"Stylistic neutrality score: {score:.1f}/100 with clickbait probability {clickbait_prob * 100:.0f}%."
    }
