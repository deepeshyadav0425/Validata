"""
Validata — Authenticity Engine.
Core REST API and Application Server.
Orchestrates multi-layer analysis, scores inputs from any source, and serves the dashboard.
"""

import os
import json
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

from backend.config import SERVER_HOST, SERVER_PORT, DEBUG_MODE, WEIGHTS, VERDICT_THRESHOLDS
from backend.analyzers.source_analyzer import analyze_source
from backend.analyzers.style_analyzer import analyze_style
from backend.analyzers.evidence_analyzer import analyze_evidence
from backend.analyzers.claim_extractor import extract_claims
from backend.models.classifier import predict_text
from backend.scraper.url_scraper import scrape_article_from_url
from backend.database.db import (
    init_db, save_analysis, get_history, get_stats,
    delete_history_item, get_analysis_by_id
)

# Project paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

app = Flask(__name__, static_folder=FRONTEND_DIR)
CORS(app)

# Initialize database tables on startup
init_db()


def evaluate_content(headline: str, body: str, source_url: str = "", declared_publisher: str = "") -> dict:
    """
    Run multi-layer fake news analysis across all 5 detection engines.
    """
    headline = (headline or "").strip()
    body = (body or "").strip()
    source_url = (source_url or "").strip()
    declared_publisher = (declared_publisher or "").strip()

    # 1. Scrape URL if provided and body is sparse
    scraped_meta = {}
    if source_url and (not body or len(body.split()) < 20):
        scrape_res = scrape_article_from_url(source_url)
        if scrape_res.get("success"):
            scraped_meta = scrape_res
            if not headline or len(headline) < 5:
                headline = scrape_res.get("title", "")
            if not body:
                body = scrape_res.get("body", "")
            if not declared_publisher:
                declared_publisher = scrape_res.get("publisher", "")

    # Layer 1: Source & Publisher Reputation
    source_analysis = analyze_source(source_url, declared_publisher)

    # Layer 2: Linguistic, Stylistic & Clickbait Analysis
    style_analysis = analyze_style(headline, body)

    # Layer 3: Evidentiary, Citation & Attribution Analysis
    evidence_analysis = analyze_evidence(f"{headline}\n\n{body}")

    # Layer 4: Machine Learning NLP Text Classification
    ml_analysis = predict_text(headline, body)

    # Layer 5: Claim Extraction & Factual Verification Links
    claims = extract_claims(headline, body)

    # Synthesis & Scoring
    is_satire = source_analysis.get("is_satire", False)

    # Check satirical text cues if domain is unknown
    if not is_satire:
        satire_cues = ["the onion", "babylon bee", "satire", "parody", "borowitz report"]
        if any(cue in headline.lower() or cue in body.lower()[:200] for cue in satire_cues):
            is_satire = True

    red_flags = []
    trust_indicators = []

    red_flags.extend(source_analysis.get("red_flags", []))
    red_flags.extend(style_analysis.get("red_flags", []))
    red_flags.extend(evidence_analysis.get("red_flags", []))
    red_flags.extend(ml_analysis.get("red_flags", []))

    trust_indicators.extend(source_analysis.get("trust_indicators", []))
    trust_indicators.extend(style_analysis.get("trust_indicators", []))
    trust_indicators.extend(evidence_analysis.get("trust_indicators", []))
    trust_indicators.extend(ml_analysis.get("trust_indicators", []))

    # Calculate Weighted Credibility Score (0 to 100)
    w_src = WEIGHTS["source_reputation"]
    w_sty = WEIGHTS["style_analysis"]
    w_evi = WEIGHTS["evidence_attribution"]
    w_ml = WEIGHTS["ml_prediction"]
    w_clm = WEIGHTS["claim_coherence"]

    # Claim coherence aligns with evidence quality and stylistic credibility
    claim_score = (evidence_analysis["score"] * 0.6) + (style_analysis["score"] * 0.4)

    computed_score = (
        (source_analysis["score"] * w_src) +
        (style_analysis["score"] * w_sty) +
        (evidence_analysis["score"] * w_evi) +
        (ml_analysis["score"] * w_ml) +
        (claim_score * w_clm)
    )

    # Safety caps for high-risk flags
    if source_analysis.get("is_questionable"):
        computed_score = min(computed_score, 30.0)
    elif style_analysis.get("clickbait_probability", 0) > 0.70 and not source_analysis.get("is_trusted"):
        computed_score = min(computed_score, 42.0)
    elif style_analysis.get("clickbait_probability", 0) > 0.50 and ml_analysis.get("fake_probability", 0) > 0.60:
        computed_score = min(computed_score, 40.0)
    elif source_analysis.get("tier") == "Suspected Spoofed Domain":
        computed_score = min(computed_score, 20.0)

    # Plain-language advice tailored for everyday users & seniors
    if is_satire:
        verdict = "SATIRE"
        credibility_score = 35.0
        summary = "Satire / Parody: This content was written as a joke, humor, or parody. It is NOT real news."
        action_advice = "😄 Safe to laugh at, but do not share this as real factual news."
        verdict_badge_text = "JOKE / SATIRE (NOT REAL NEWS)"
    elif computed_score >= VERDICT_THRESHOLDS["GENUINE"]:
        verdict = "GENUINE"
        credibility_score = round(computed_score, 1)
        summary = "Highly Credible / Genuine: This news comes from a reputable newsroom with verifiable quotes and balanced reporting."
        action_advice = "✅ Safe to share: This article is supported by recognized journalists and verifiable citations."
        verdict_badge_text = "GENUINE & SAFE TO SHARE"
    elif computed_score >= VERDICT_THRESHOLDS["QUESTIONABLE"]:
        verdict = "QUESTIONABLE"
        credibility_score = round(computed_score, 1)
        summary = "Questionable / Unverified: Contains unconfirmed claims, sensational words, or lacks direct official proof."
        action_advice = "⚠️ Be careful: Do not forward this yet. Wait until major verified news channels confirm the story."
        verdict_badge_text = "UNVERIFIED (CHECK BEFORE SHARING)"
    else:
        verdict = "FAKE"
        credibility_score = round(computed_score, 1)
        summary = "Likely Fake / Fabricated: Contains classic signs of false rumors, clickbait manipulation, and fake quotes."
        action_advice = "🚫 DO NOT FORWARD: This looks like a false rumor or scam intended to cause panic or sell fake remedies."
        verdict_badge_text = "FAKE / FABRICATED (DO NOT SHARE)"

    word_count = len(f"{headline} {body}".split())

    report = {
        "title": headline or "Untitled Submission",
        "body_preview": body[:280] + "..." if len(body) > 280 else body,
        "source_url": source_url,
        "source_domain": source_analysis.get("domain", ""),
        "publisher": source_analysis.get("publisher_name", declared_publisher or "Unknown"),
        "author": scraped_meta.get("author", "Not specified"),
        "publish_date": scraped_meta.get("publish_date", "Unknown"),
        "word_count": word_count,
        "verdict": verdict,
        "verdict_badge_text": verdict_badge_text,
        "action_advice": action_advice,
        "credibility_score": credibility_score,
        "summary": summary,
        "is_satire": is_satire,
        "metrics": {
            "source_reputation": round(source_analysis["score"], 1),
            "linguistic_neutrality": round(style_analysis["score"], 1),
            "evidence_quality": round(evidence_analysis["score"], 1),
            "ml_authenticity": round(ml_analysis["score"], 1),
            "claim_coherence": round(claim_score, 1),
            "clickbait_probability": style_analysis.get("clickbait_probability", 0),
            "sensationalism_index": style_analysis.get("sensationalism_index", 0),
            "quotes_detected": evidence_analysis.get("quote_count", 0),
            "institutional_references": evidence_analysis.get("institutional_ref_count", 0),
            "weasel_words_count": evidence_analysis.get("weasel_word_count", 0)
        },
        "layer_details": {
            "source": source_analysis,
            "style": style_analysis,
            "evidence": evidence_analysis,
            "ml": ml_analysis
        },
        "red_flags": red_flags,
        "trust_indicators": trust_indicators,
        "claims": claims
    }

    # Save to history database
    db_id = save_analysis(report)
    report["id"] = db_id

    return report


# --- STATIC FILE ROUTES ---

@app.route("/")
def index():
    """Serve single-page frontend application."""
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.route("/<path:path>")
def static_files(path):
    """Serve CSS, JS, and asset files."""
    return send_from_directory(FRONTEND_DIR, path)


# --- REST API ENDPOINTS ---

@app.route("/api/analyze/text", methods=["POST"])
def api_analyze_text():
    """Analyze news text and headline."""
    data = request.get_json(silent=True) or {}
    headline = data.get("headline", "").strip()
    body = data.get("body", "").strip()
    source_url = data.get("source_url", "").strip()
    publisher = data.get("publisher", "").strip()

    if not headline and not body:
        return jsonify({"error": "Please provide a headline or article body to analyze."}), 400

    report = evaluate_content(headline, body, source_url, publisher)
    return jsonify(report)


@app.route("/api/analyze/url", methods=["POST"])
def api_analyze_url():
    """Fetch URL and analyze the extracted news article."""
    data = request.get_json(silent=True) or {}
    url = data.get("url", "").strip()

    if not url:
        return jsonify({"error": "Please provide a valid news article URL."}), 400

    # Scrape the URL
    scraped = scrape_article_from_url(url)
    if not scraped.get("success"):
        return jsonify({"error": scraped.get("error", "Failed to fetch content from URL.")}), 422

    headline = scraped.get("title", "")
    body = scraped.get("body", "")
    publisher = scraped.get("publisher", "")

    report = evaluate_content(headline, body, source_url=url, declared_publisher=publisher)
    report["scraped_meta"] = {
        "title": scraped.get("title"),
        "author": scraped.get("author"),
        "publish_date": scraped.get("publish_date"),
        "publisher": scraped.get("publisher"),
        "word_count": scraped.get("word_count")
    }
    return jsonify(report)


@app.route("/api/history", methods=["GET"])
def api_get_history():
    """Retrieve audit analysis history."""
    limit = int(request.args.get("limit", 50))
    verdict = request.args.get("verdict", None)
    history = get_history(limit=limit, verdict_filter=verdict)
    return jsonify({"history": history})


@app.route("/api/history/<int:item_id>", methods=["DELETE"])
def api_delete_history(item_id):
    """Delete an item from audit history."""
    deleted = delete_history_item(item_id)
    return jsonify({"success": deleted})


@app.route("/api/history/<int:item_id>", methods=["GET"])
def api_get_history_item(item_id):
    """Get single report by id."""
    item = get_analysis_by_id(item_id)
    if not item:
        return jsonify({"error": "Report not found"}), 404
    return jsonify(item)


@app.route("/api/stats", methods=["GET"])
def api_get_stats():
    """Retrieve aggregate statistics."""
    stats = get_stats()
    return jsonify(stats)


@app.route("/api/sample-articles", methods=["GET"])
def api_sample_articles():
    """Returns curated realistic sample news articles for testing with 1 click."""
    samples = [
        {
            "id": "reuters_vaccine",
            "title": "World Health Organization approves new pediatric malaria vaccine rollout",
            "body": "The World Health Organization confirmed the prequalification of a new pediatric malaria vaccine, marking a major milestone in global public health. According to clinical trial data published in The Lancet medical journal, the vaccine demonstrated 77 percent efficacy in clinical trials conducted across four African nations. Dr. Tedros Adhanom Ghebreyesus, WHO Director-General, stated that distribution will begin next month in partnership with UNICEF.",
            "source_url": "https://www.reuters.com/business/healthcare-pharmaceuticals/who-approves-malaria-vaccine-2024",
            "publisher": "Reuters",
            "category": "Genuine News (Wire Report)"
        },
        {
            "id": "whatsapp_cancer_cure",
            "title": "SHOCKING: Drinking boiled lemon peel and baking soda will destroy 100 percent of cancer cells in 3 days!",
            "body": "Do not let the greedy doctors fool you! Modern hospitals don't want you to know that natural kitchen remedies are ten thousand times stronger than chemotherapy! Renowned secret researchers who cannot be named proved that mixing hot lemon water with baking soda immediately suffocates every tumor. Forward this to everyone before it gets deleted forever!",
            "source_url": "",
            "publisher": "Viral WhatsApp Forward",
            "category": "Fake / Medical Hoax"
        },
        {
            "id": "onion_belly_rubs",
            "title": "The Onion: Nation's Dogs Announce Collective Strike Demanding Unlimited Belly Rubs",
            "body": "WASHINGTON—In a coordinated nationwide walkout, over 70 million domestic canines sat down on front lawns Tuesday morning, refusing to fetch tennis balls or bark at mail carriers until human households guarantee 24-hour access to couch cushions and unearned bacon treats. Spokesdog Buster told reporters through an interpreter that negotiations are currently stalled over ear scritch quotas.",
            "source_url": "https://www.theonion.com/nations-dogs-announce-strike",
            "publisher": "The Onion",
            "category": "Satire / Parody"
        },
        {
            "id": "clickbait_gossip",
            "title": "You won't believe what this beloved 90s TV star looks like today! Total nightmare!",
            "body": "Click here to see the horrifying photos that have left millions of fans in complete tears! What happened to this beloved star will shock you to your core. From luxury mansions to living in a broken camper van, see the scandalous secrets their former costars never wanted revealed to the public!",
            "source_url": "https://www.buzz-celebrity-news.xyz/horrifying-secrets-revealed",
            "publisher": "buzz-celebrity-news.xyz",
            "category": "Clickbait / Sensationalism"
        },
        {
            "id": "isro_space_success",
            "title": "Indian Space Research Organisation successfully tests semi-cryogenic engine stage",
            "body": "The Indian Space Research Organisation (ISRO) successfully conducted a hot test of its 2000 kN semi-cryogenic engine at the propulsion complex in Mahendragiri. Scientists confirmed nominal engine parameters throughout the 150-second test duration, paving the way for heavy payload orbital launch vehicle development.",
            "source_url": "https://www.thehindu.com/sci-tech/science/isro-tests-semi-cryogenic-engine",
            "publisher": "The Hindu",
            "category": "Genuine News (Science/Space)"
        }
    ]
    return jsonify({"samples": samples})


if __name__ == "__main__":
    print(f"[*] Starting Validata Authenticity Engine on http://{SERVER_HOST}:{SERVER_PORT}")
    app.run(host=SERVER_HOST, port=SERVER_PORT, debug=DEBUG_MODE)
