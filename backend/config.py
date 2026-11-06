"""
Configuration settings, scoring weights, and media domain reputation lists.
"""

# Server Configuration
SERVER_HOST = "0.0.0.0"
SERVER_PORT = 5000
DEBUG_MODE = False

# Scoring Weights (Total = 1.0)
WEIGHTS = {
    "source_reputation": 0.25,
    "style_analysis": 0.20,
    "evidence_attribution": 0.20,
    "ml_prediction": 0.25,
    "claim_coherence": 0.10,
}

# Verdict Thresholds (Overall Credibility Score 0 - 100)
VERDICT_THRESHOLDS = {
    "GENUINE": 78,       # >= 78 is Genuine / Highly Credible
    "QUESTIONABLE": 45,  # 45 - 77 is Questionable / Unverified
    "FAKE": 0,           # < 45 is Likely Fake / Fabricated
}

# Known Trusted Global & Regional News Sources (High Credibility Baseline)
TRUSTED_DOMAINS = {
    # Major Global Wire Services & Broadcasters
    "reuters.com": {"name": "Reuters", "tier": "A+", "score": 98},
    "apnews.com": {"name": "Associated Press", "tier": "A+", "score": 98},
    "afp.com": {"name": "Agence France-Presse", "tier": "A+", "score": 96},
    "bbc.com": {"name": "BBC News", "tier": "A", "score": 95},
    "bbc.co.uk": {"name": "BBC UK", "tier": "A", "score": 95},
    "npr.org": {"name": "NPR", "tier": "A", "score": 94},
    "pbs.org": {"name": "PBS", "tier": "A", "score": 94},
    "dw.com": {"name": "Deutsche Welle", "tier": "A", "score": 93},
    "france24.com": {"name": "France 24", "tier": "A", "score": 92},

    # Recognized Quality Journalism Outlets
    "nytimes.com": {"name": "The New York Times", "tier": "A", "score": 92},
    "wsj.com": {"name": "The Wall Street Journal", "tier": "A", "score": 92},
    "theguardian.com": {"name": "The Guardian", "tier": "A", "score": 91},
    "washingtonpost.com": {"name": "The Washington Post", "tier": "A", "score": 91},
    "ft.com": {"name": "Financial Times", "tier": "A+", "score": 95},
    "bloomberg.com": {"name": "Bloomberg", "tier": "A+", "score": 95},
    "economist.com": {"name": "The Economist", "tier": "A+", "score": 94},
    "time.com": {"name": "TIME", "tier": "B+", "score": 87},
    "theatlantic.com": {"name": "The Atlantic", "tier": "A", "score": 90},
    "politico.com": {"name": "Politico", "tier": "B+", "score": 88},
    "propublica.org": {"name": "ProPublica", "tier": "A+", "score": 97},
    "axios.com": {"name": "Axios", "tier": "B+", "score": 88},
    "cnn.com": {"name": "CNN", "tier": "B", "score": 82},
    "nbcnews.com": {"name": "NBC News", "tier": "B+", "score": 86},
    "cbsnews.com": {"name": "CBS News", "tier": "B+", "score": 86},
    "abcnews.go.com": {"name": "ABC News", "tier": "B+", "score": 86},

    # Indian Major Publications
    "thehindu.com": {"name": "The Hindu", "tier": "A", "score": 93},
    "indianexpress.com": {"name": "The Indian Express", "tier": "A", "score": 91},
    "timesofindia.indiatimes.com": {"name": "Times of India", "tier": "B", "score": 82},
    "hindustantimes.com": {"name": "Hindustan Times", "tier": "B", "score": 83},
    "ndtv.com": {"name": "NDTV", "tier": "B+", "score": 84},
    "livemint.com": {"name": "Livemint", "tier": "A", "score": 90},
    "theprint.in": {"name": "ThePrint", "tier": "B+", "score": 85},
    "scroll.in": {"name": "Scroll.in", "tier": "B+", "score": 85},

    # Science & Academic Publications
    "nature.com": {"name": "Nature", "tier": "A+", "score": 99},
    "sciencemag.org": {"name": "Science", "tier": "A+", "score": 99},
    "scientificamerican.com": {"name": "Scientific American", "tier": "A", "score": 95},
    "nationalgeographic.com": {"name": "National Geographic", "tier": "A", "score": 93},
    "who.int": {"name": "World Health Organization", "tier": "A+", "score": 99},
    "cdc.gov": {"name": "CDC", "tier": "A+", "score": 98},
    "nih.gov": {"name": "National Institutes of Health", "tier": "A+", "score": 98},
    "nasa.gov": {"name": "NASA", "tier": "A+", "score": 99},
}

# Known Satire / Parody Publications
SATIRE_DOMAINS = {
    "theonion.com": "The Onion",
    "babylonbee.com": "The Babylon Bee",
    "fakingnews.com": "Faking News",
    "clickhole.com": "ClickHole",
    "thebeaverton.com": "The Beaverton",
    "private-eye.co.uk": "Private Eye",
    "waterfordwhispersnews.com": "Waterford Whispers",
    "duffelblog.com": "Duffel Blog",
    "thepoke.co.uk": "The Poke",
    "dailycurrant.com": "Daily Currant",
    "borowitzreport.com": "The Borowitz Report",
}

# Known Questionable, Clickbait, Disinformation, or Propaganda Outlets
QUESTIONABLE_DOMAINS = {
    "infowars.com": {"name": "InfoWars", "type": "conspiracy", "score": 10},
    "naturalnews.com": {"name": "NaturalNews", "type": "pseudomedical", "score": 12},
    "beforeitsnews.com": {"name": "Before It's News", "type": "conspiracy/fake", "score": 8},
    "worldnewsdailyreport.com": {"name": "World News Daily Report", "type": "hoax", "score": 5},
    "empirenews.net": {"name": "Empire News", "type": "fabricated", "score": 6},
    "neonnettle.com": {"name": "Neon Nettle", "type": "clickbait/fake", "score": 14},
    "yournewswire.com": {"name": "YourNewsWire / NewsPunch", "type": "disinformation", "score": 8},
    "newspunch.com": {"name": "NewsPunch", "type": "disinformation", "score": 8},
    "breitbart.com": {"name": "Breitbart", "type": "extreme bias/sensational", "score": 38},
    "thegatewaypundit.com": {"name": "The Gateway Pundit", "type": "conspiracy/unverified", "score": 20},
}

# Suspicious Top-Level Domains commonly used by throwaway fake news sites
SUSPICIOUS_TLDS = {
    ".xyz", ".top", ".buzz", ".club", ".icu", ".cam", ".monster", ".work",
    ".gq", ".ml", ".cf", ".tk", ".ga"
}
