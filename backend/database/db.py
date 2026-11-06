"""
SQLite Database Storage for Analysis History, Audit Logs, and Global Stats.
"""

import os
import sqlite3
import json
from datetime import datetime


DB_PATH = os.path.join(os.path.dirname(__file__), "fakenews_history.db")


def get_db_connection():
    """Create and return a database connection with dict-like row factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize the SQLite schema."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            title TEXT,
            source_url TEXT,
            source_domain TEXT,
            publisher TEXT,
            verdict TEXT NOT NULL,
            credibility_score REAL NOT NULL,
            word_count INTEGER DEFAULT 0,
            metrics_json TEXT NOT NULL,
            red_flags_json TEXT,
            trust_indicators_json TEXT,
            claims_json TEXT,
            summary TEXT
        )
    """)
    conn.commit()
    conn.close()


def save_analysis(report: dict) -> int:
    """Save analysis report to database and return the inserted id."""
    conn = get_db_connection()
    cursor = conn.cursor()
    now_iso = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
        INSERT INTO analyses (
            created_at, title, source_url, source_domain, publisher,
            verdict, credibility_score, word_count, metrics_json,
            red_flags_json, trust_indicators_json, claims_json, summary
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        now_iso,
        report.get("title", "Untitled"),
        report.get("source_url", ""),
        report.get("source_domain", ""),
        report.get("publisher", ""),
        report.get("verdict", "QUESTIONABLE"),
        report.get("credibility_score", 50.0),
        report.get("word_count", 0),
        json.dumps(report.get("metrics", {})),
        json.dumps(report.get("red_flags", [])),
        json.dumps(report.get("trust_indicators", [])),
        json.dumps(report.get("claims", [])),
        report.get("summary", "")
    ))
    inserted_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return inserted_id


def get_history(limit: int = 50, verdict_filter: str = None) -> list:
    """Fetch recent analysis records."""
    conn = get_db_connection()
    cursor = conn.cursor()

    if verdict_filter and verdict_filter.upper() != "ALL":
        cursor.execute(
            "SELECT * FROM analyses WHERE verdict = ? ORDER BY id DESC LIMIT ?",
            (verdict_filter.upper(), limit)
        )
    else:
        cursor.execute(
            "SELECT * FROM analyses ORDER BY id DESC LIMIT ?",
            (limit,)
        )

    rows = cursor.fetchall()
    results = []
    for r in rows:
        results.append({
            "id": r["id"],
            "created_at": r["created_at"],
            "title": r["title"],
            "source_url": r["source_url"],
            "source_domain": r["source_domain"],
            "publisher": r["publisher"],
            "verdict": r["verdict"],
            "credibility_score": r["credibility_score"],
            "word_count": r["word_count"],
            "summary": r["summary"],
            "metrics": json.loads(r["metrics_json"]) if r["metrics_json"] else {},
            "red_flags": json.loads(r["red_flags_json"]) if r["red_flags_json"] else [],
            "trust_indicators": json.loads(r["trust_indicators_json"]) if r["trust_indicators_json"] else [],
            "claims": json.loads(r["claims_json"]) if r["claims_json"] else []
        })

    conn.close()
    return results


def get_analysis_by_id(item_id: int):
    """Retrieve full analysis details by id."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM analyses WHERE id = ?", (item_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    return {
        "id": row["id"],
        "created_at": row["created_at"],
        "title": row["title"],
        "source_url": row["source_url"],
        "source_domain": row["source_domain"],
        "publisher": row["publisher"],
        "verdict": row["verdict"],
        "credibility_score": row["credibility_score"],
        "word_count": row["word_count"],
        "summary": row["summary"],
        "metrics": json.loads(row["metrics_json"]) if row["metrics_json"] else {},
        "red_flags": json.loads(row["red_flags_json"]) if row["red_flags_json"] else [],
        "trust_indicators": json.loads(row["trust_indicators_json"]) if row["trust_indicators_json"] else [],
        "claims": json.loads(row["claims_json"]) if row["claims_json"] else []
    }


def delete_history_item(item_id: int) -> bool:
    """Delete an item from history."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM analyses WHERE id = ?", (item_id,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted


def get_stats() -> dict:
    """Calculate aggregate statistics."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM analyses")
    total = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM analyses WHERE verdict = 'GENUINE'")
    genuine = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM analyses WHERE verdict = 'FAKE'")
    fake = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM analyses WHERE verdict = 'QUESTIONABLE'")
    questionable = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM analyses WHERE verdict = 'SATIRE'")
    satire = cursor.fetchone()[0]

    cursor.execute("SELECT AVG(credibility_score) FROM analyses")
    avg_score_row = cursor.fetchone()[0]
    avg_score = round(avg_score_row, 1) if avg_score_row is not None else 0.0

    conn.close()

    return {
        "total_analyzed": total,
        "genuine_count": genuine,
        "fake_count": fake,
        "questionable_count": questionable,
        "satire_count": satire,
        "average_score": avg_score
    }
