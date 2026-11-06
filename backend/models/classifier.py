"""
Machine Learning Inference Classifier.
Loads the serialized NLP model, generates calibrated probabilities,
and extracts influential N-gram feature signals for explainability.
"""

import os
import joblib


_MODEL = None


def load_model():
    """Lazy load or return existing pipeline."""
    global _MODEL
    if _MODEL is None:
        model_path = os.path.join(os.path.dirname(__file__), "fake_news_model.pkl")
        if not os.path.exists(model_path):
            from backend.models.train_model import train_and_save_model
            _MODEL = train_and_save_model()
        else:
            _MODEL = joblib.load(model_path)
    return _MODEL


def predict_text(headline: str, body: str) -> dict:
    """
    Run ML model inference on combined text.
    Returns:
        dict: {
            "score": float (0-100),
            "genuine_probability": float,
            "fake_probability": float,
            "predicted_label": "Genuine" | "Fake / Sensational",
            "confidence": float,
            "top_signals": list,
            "red_flags": list,
            "trust_indicators": list
        }
    """
    model = load_model()
    combined = f"{headline} {body}".strip()
    if not combined:
        return {
            "score": 50.0,
            "genuine_probability": 0.5,
            "fake_probability": 0.5,
            "predicted_label": "Inconclusive",
            "confidence": 0.0,
            "top_signals": [],
            "red_flags": [],
            "trust_indicators": []
        }

    # Probability estimation: [P(Fake), P(Genuine)]
    try:
        probs = model.predict_proba([combined])[0]
        fake_prob = float(probs[0])
        genuine_prob = float(probs[1])
    except Exception:
        fake_prob = 0.5
        genuine_prob = 0.5

    score = genuine_prob * 100.0
    label = "Genuine" if genuine_prob >= 0.5 else "Fake / Sensational"
    confidence = max(fake_prob, genuine_prob)

    red_flags = []
    trust_indicators = []
    top_signals = []

    # Extract top influential feature words from the vectorizer and classifier
    try:
        vectorizer = model.named_steps['tfidf']
        clf = model.named_steps['clf']
        feature_names = vectorizer.get_feature_names_out()
        coefs = clf.coef_[0]

        # Transform single document
        tfidf_vec = vectorizer.transform([combined])
        non_zero_indices = tfidf_vec.nonzero()[1]

        # Calculate word contributions (weight * tfidf)
        contributions = []
        for idx in non_zero_indices:
            term = feature_names[idx]
            weight = coefs[idx] * tfidf_vec[0, idx]
            contributions.append((term, weight))

        # Sort by weight
        contributions.sort(key=lambda x: x[1])

        # Top words pushing towards Fake (negative weights)
        fake_signals = [t[0] for t in contributions[:3] if t[1] < -0.05]
        # Top words pushing towards Genuine (positive weights)
        genuine_signals = [t[0] for t in contributions[-3:] if t[1] > 0.05]

        if fake_signals:
            top_signals.extend([f"Fake Signal: '{s}'" for s in fake_signals])
        if genuine_signals:
            top_signals.extend([f"Genuine Signal: '{s}'" for s in reversed(genuine_signals)])

    except Exception:
        pass

    if fake_prob >= 0.65:
        red_flags.append(f"ML semantic classifier identified lexical patterns typical of fabricated content ({fake_prob * 100:.0f}% fake probability).")
    elif genuine_prob >= 0.70:
        trust_indicators.append(f"ML semantic classifier identified journalistic syntax & phrasing ({genuine_prob * 100:.0f}% confidence).")

    return {
        "score": round(score, 1),
        "genuine_probability": round(genuine_prob, 2),
        "fake_probability": round(fake_prob, 2),
        "predicted_label": label,
        "confidence": round(confidence * 100, 1),
        "top_signals": top_signals,
        "red_flags": red_flags,
        "trust_indicators": trust_indicators
    }
