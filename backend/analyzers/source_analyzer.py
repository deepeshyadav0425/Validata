"""
Domain & Source Reputation Analyzer.
Evaluates publisher authenticity, domain history patterns, satire recognition, and spoofing indicators.
"""

import re
from urllib.parse import urlparse
from backend.config import (
    TRUSTED_DOMAINS,
    SATIRE_DOMAINS,
    QUESTIONABLE_DOMAINS,
    SUSPICIOUS_TLDS,
)


def extract_clean_domain(url_or_domain: str) -> str:
    """Extract clean domain hostname from a URL or raw domain string."""
    if not url_or_domain:
        return ""
    text = url_or_domain.strip().lower()
    if not text.startswith(("http://", "https://")):
        text = "https://" + text
    try:
        parsed = urlparse(text)
        netloc = parsed.netloc.split(":")[0]  # strip port
        if netloc.startswith("www."):
            netloc = netloc[4:]
        return netloc
    except Exception:
        return url_or_domain.lower().strip()


def check_domain_spoofing(domain: str) -> dict:
    """
    Check if a domain is imitating a reputable outlet using hyphenated suffixes
    like 'bbc-news-today.com', 'reuters-breaking.xyz', or 'cnn.com.co'.
    """
    trusted_names = [
        "reuters", "bbc", "cnn", "nytimes", "washingtonpost", "theguardian",
        "apnews", "hindu", "bloomberg", "ndtv", "aljazeera"
    ]
    for brand in trusted_names:
        # e.g., bbc-breakingnews.com or bbc.com.co or fake-reuters.com
        pattern = rf"(^|[-_.])({brand})([-_.])"
        if re.search(pattern, domain):
            # Check if it is an actual recognized legitimate domain
            if not any(domain.endswith("." + legit) or domain == legit for legit in TRUSTED_DOMAINS):
                return {
                    "is_spoofed": True,
                    "target_brand": brand,
                    "explanation": f"Domain appears to be imitating '{brand.upper()}' ({domain})."
                }
    return {"is_spoofed": False}


def analyze_source(url_or_domain: str = "", declared_publisher: str = "") -> dict:
    """
    Perform deep source reputation analysis.
    Returns:
        dict: {
            "domain": str,
            "publisher_name": str,
            "is_satire": bool,
            "is_trusted": bool,
            "is_questionable": bool,
            "score": float (0-100),
            "tier": str,
            "red_flags": list,
            "trust_indicators": list,
            "details": str
        }
    """
    red_flags = []
    trust_indicators = []
    is_satire = False
    is_trusted = False
    is_questionable = False
    tier = "Unknown / Unverified"
    score = 50.0  # neutral starting baseline for unknown sources

    domain = extract_clean_domain(url_or_domain) if url_or_domain else ""
    pub_name = (declared_publisher or "").strip().lower()

    if not domain and not pub_name:
        return {
            "domain": "Not Provided (Direct Text)",
            "publisher_name": "Direct User Submission",
            "is_satire": False,
            "is_trusted": False,
            "is_questionable": False,
            "score": 50.0,
            "tier": "Unverified Source",
            "red_flags": ["No publisher URL or domain provided for origin verification."],
            "trust_indicators": [],
            "details": "Source could not be independently cross-verified without a URL or publication name."
        }

    # 1. Check Known Satire
    for satire_dom, name in SATIRE_DOMAINS.items():
        if domain.endswith(satire_dom) or pub_name == satire_dom or pub_name == name.lower():
            is_satire = True
            tier = "Satire / Parody"
            score = 30.0
            trust_indicators.append(f"Transparent satirical publication: '{name}'.")
            return {
                "domain": domain or satire_dom,
                "publisher_name": name,
                "is_satire": True,
                "is_trusted": False,
                "is_questionable": False,
                "score": score,
                "tier": tier,
                "red_flags": ["This is a recognized satire outlet. Articles are intended for humor, not factual news."],
                "trust_indicators": trust_indicators,
                "details": f"Content is published by {name}, a recognized humor/satire website."
            }

    # 2. Check Known Questionable / Fake Outlets
    for q_dom, meta in QUESTIONABLE_DOMAINS.items():
        if domain.endswith(q_dom) or pub_name == q_dom or pub_name == meta["name"].lower():
            is_questionable = True
            tier = "Known Low Credibility / Disinformation"
            score = float(meta["score"])
            red_flags.append(f"Source matches '{meta['name']}', widely catalogued as a {meta['type']} outlet.")
            return {
                "domain": domain or q_dom,
                "publisher_name": meta["name"],
                "is_satire": False,
                "is_trusted": False,
                "is_questionable": True,
                "score": score,
                "tier": tier,
                "red_flags": red_flags,
                "trust_indicators": [],
                "details": f"High risk source with documented history of {meta['type']} content."
            }

    # 3. Check Known Trusted Media Outlets
    for t_dom, meta in TRUSTED_DOMAINS.items():
        if domain.endswith(t_dom) or pub_name == t_dom or pub_name == meta["name"].lower():
            is_trusted = True
            tier = f"Established Media (Tier {meta['tier']})"
            score = float(meta["score"])
            trust_indicators.append(f"Verified mainstream journalistic institution: {meta['name']}.")
            trust_indicators.append("Subject to institutional editorial standards and corrections policy.")
            return {
                "domain": domain or t_dom,
                "publisher_name": meta["name"],
                "is_satire": False,
                "is_trusted": True,
                "is_questionable": False,
                "score": score,
                "tier": tier,
                "red_flags": [],
                "trust_indicators": trust_indicators,
                "details": f"Published by recognized newsroom ({meta['name']}) with verified journalistic governance."
            }

    # 4. Check for Brand Impersonation / Spoofing
    spoof_check = check_domain_spoofing(domain)
    if spoof_check.get("is_spoofed"):
        score = 15.0
        red_flags.append(spoof_check["explanation"])
        red_flags.append("Domain appears designed to mislead readers by mimicking a reputable brand.")
        return {
            "domain": domain,
            "publisher_name": domain,
            "is_satire": False,
            "is_trusted": False,
            "is_questionable": True,
            "score": score,
            "tier": "Suspected Spoofed Domain",
            "red_flags": red_flags,
            "trust_indicators": [],
            "details": "Severe spoofing indicators found."
        }

    # 5. Check TLD Suspicion
    for tld in SUSPICIOUS_TLDS:
        if domain.endswith(tld):
            score -= 20.0
            red_flags.append(f"Domain uses high-risk throwaway TLD ('{tld}') frequently associated with spam and short-lived hoax sites.")
            break

    # 6. Check for Educational or Government TLDs (.edu, .gov, .org)
    if domain.endswith(".gov") or domain.endswith(".gov.in") or domain.endswith(".gov.uk"):
        score = 96.0
        trust_indicators.append("Official government domain (.gov). High institutional authority.")
        tier = "Official Government Source"
        is_trusted = True
    elif domain.endswith(".edu") or domain.endswith(".ac.in") or domain.endswith(".ac.uk"):
        score = 92.0
        trust_indicators.append("Verified academic/research institution domain (.edu).")
        tier = "Academic Institution"
        is_trusted = True

    score = max(5.0, min(100.0, score))
    return {
        "domain": domain or "Custom",
        "publisher_name": declared_publisher or domain or "Independent Source",
        "is_satire": False,
        "is_trusted": is_trusted,
        "is_questionable": is_questionable,
        "score": score,
        "tier": tier,
        "red_flags": red_flags,
        "trust_indicators": trust_indicators,
        "details": f"Analyzed domain '{domain or 'N/A'}' with baseline rating {score:.1f}/100."
    }
