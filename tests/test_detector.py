"""
Unit & Integration Test Suite for Fake News Detector.
Tests all 5 detection engines, edge cases, and REST API endpoints.
"""

import unittest
from backend.app import app, evaluate_content
from backend.analyzers.source_analyzer import analyze_source, check_domain_spoofing
from backend.analyzers.style_analyzer import analyze_style
from backend.analyzers.evidence_analyzer import analyze_evidence
from backend.analyzers.claim_extractor import extract_claims


class TestFakeNewsDetector(unittest.TestCase):

    def setUp(self):
        self.client = app.test_client()

    def test_genuine_reuters_article(self):
        """Genuine journalistic article from Reuters should score >= 78 and marked GENUINE."""
        headline = "World Health Organization approves new pediatric malaria vaccine rollout"
        body = (
            "The World Health Organization confirmed the prequalification of a new pediatric malaria vaccine, "
            "marking a major milestone in global public health. According to clinical trial data published in "
            "The Lancet medical journal, the vaccine demonstrated 77 percent efficacy in clinical trials conducted "
            "across four African nations. Dr. Tedros Adhanom Ghebreyesus, WHO Director-General, stated that "
            "distribution will begin next month in partnership with UNICEF."
        )
        report = evaluate_content(
            headline=headline,
            body=body,
            source_url="https://www.reuters.com/business/healthcare-pharmaceuticals/who-vaccine",
            declared_publisher="Reuters"
        )
        self.assertEqual(report["verdict"], "GENUINE")
        self.assertGreaterEqual(report["credibility_score"], 78)
        self.assertTrue(any("Reuters" in t for t in report["trust_indicators"]))

    def test_fake_miracle_cure_hoax(self):
        """Sensational medical hoax should score < 45 and be marked FAKE."""
        headline = "SHOCKING: Drinking boiled lemon peel and baking soda will destroy 100 percent of cancer cells in 3 days!"
        body = (
            "Do not let the greedy doctors fool you! Modern hospitals don't want you to know that natural kitchen "
            "remedies are ten thousand times stronger than chemotherapy! Renowned secret researchers who cannot "
            "be named proved that mixing hot lemon water with baking soda immediately suffocates every tumor. "
            "Forward this to everyone before it gets deleted forever!"
        )
        report = evaluate_content(
            headline=headline,
            body=body,
            source_url="http://cure-cancer-secrets.xyz/shocking-truth",
            declared_publisher="Viral Forward"
        )
        self.assertEqual(report["verdict"], "FAKE")
        self.assertLess(report["credibility_score"], 45)
        self.assertTrue(len(report["red_flags"]) > 0)

    def test_satire_article_detection(self):
        """Known satirical publication (The Onion) should be classified as SATIRE."""
        headline = "The Onion: Nation's Dogs Announce Collective Strike Demanding Unlimited Belly Rubs"
        body = (
            "WASHINGTON—In a coordinated nationwide walkout, over 70 million domestic canines sat down on front "
            "lawns Tuesday morning, refusing to fetch tennis balls or bark at mail carriers until human households "
            "guarantee 24-hour access to couch cushions. Spokesdog Buster told reporters through an interpreter that "
            "negotiations are stalled."
        )
        report = evaluate_content(
            headline=headline,
            body=body,
            source_url="https://www.theonion.com/dogs-strike",
            declared_publisher="The Onion"
        )
        self.assertEqual(report["verdict"], "SATIRE")
        self.assertTrue(report["is_satire"])

    def test_domain_spoofing_detection(self):
        """Spoofed domain mimicking BBC or Reuters should trigger spoofing alert."""
        check = check_domain_spoofing("bbc-breakingnews-today.com")
        self.assertTrue(check["is_spoofed"])
        self.assertEqual(check["target_brand"], "bbc")

        res = analyze_source("https://bbc-breakingnews-today.com/alert")
        self.assertEqual(res["tier"], "Suspected Spoofed Domain")
        self.assertLessEqual(res["score"], 25.0)

    def test_clickbait_and_sensationalism_analyzer(self):
        """Clickbait phrases should be detected."""
        style = analyze_style(
            headline="You won't believe what happens next! Mind-blowing secret!",
            body="Doctors hate this one simple trick! Miraculous breakthrough announced!"
        )
        self.assertGreater(style["clickbait_probability"], 0.6)
        self.assertTrue(any("Clickbait" in f for f in style["red_flags"]))

    def test_attribution_analyzer(self):
        """Direct quotes and institutional attribution should boost evidence score."""
        text_with_quotes = (
            'The Ministry of Health announced new safety measures. "We are monitoring the situation closely," '
            'said Dr. John Smith from the World Health Organization.'
        )
        evi = analyze_evidence(text_with_quotes)
        self.assertGreaterEqual(evi["quote_count"], 1)
        self.assertGreaterEqual(evi["institutional_ref_count"], 2)
        self.assertGreaterEqual(evi["score"], 70)

    def test_claims_extraction(self):
        """Key testable claims should be extracted with fact-checking URLs."""
        headline = "Supreme Court strikes down controversial tech regulation statute"
        body = "The Supreme Court voted 7-2 on Friday to invalidate the proposed statute, citing lack of statutory authorization."
        claims = extract_claims(headline, body)
        self.assertGreaterEqual(len(claims), 1)
        self.assertTrue("google_factcheck_url" in claims[0])
        self.assertTrue("news_search_url" in claims[0])

    def test_api_endpoints(self):
        """Verify REST API responds correctly."""
        # 1. Test /api/sample-articles
        res = self.client.get("/api/sample-articles")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("samples", data)
        self.assertGreaterEqual(len(data["samples"]), 3)

        # 2. Test /api/stats
        res_stats = self.client.get("/api/stats")
        self.assertEqual(res_stats.status_code, 200)

        # 3. Test POST /api/analyze/text
        payload = {
            "headline": "Indian Space Research Organisation successfully tests semi-cryogenic engine stage",
            "body": "The Indian Space Research Organisation (ISRO) successfully conducted a hot test at Mahendragiri.",
            "publisher": "The Hindu",
            "source_url": "https://www.thehindu.com/sci-tech/science/isro-test"
        }
        res_post = self.client.post("/api/analyze/text", json=payload)
        self.assertEqual(res_post.status_code, 200)
        post_data = res_post.get_json()
        self.assertIn("verdict", post_data)
        self.assertIn("credibility_score", post_data)

    def test_ssrf_protection(self):
        """Verify SSRF validator blocks local loopback, private IPs, and non-http schemes."""
        from backend.scraper.url_scraper import validate_url_security

        # Loopback
        is_safe, err = validate_url_security("http://127.0.0.1:5000/api/stats")
        self.assertFalse(is_safe)
        self.assertIn("loopback", err.lower())

        # Localhost
        is_safe, err = validate_url_security("http://localhost:8080")
        self.assertFalse(is_safe)

        # Cloud Metadata IP
        is_safe, err = validate_url_security("http://169.254.169.254/latest/meta-data/")
        self.assertFalse(is_safe)

        # Dangerous non-http scheme
        is_safe, err = validate_url_security("file:///etc/passwd")
        self.assertFalse(is_safe)

    def test_security_headers(self):
        """Verify HTTP security headers are injected into responses."""
        res = self.client.get("/api/sample-articles")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.headers.get("X-Content-Type-Options"), "nosniff")
        self.assertEqual(res.headers.get("X-Frame-Options"), "SAMEORIGIN")
        self.assertIn("Content-Security-Policy", res.headers)
        self.assertEqual(res.headers.get("Referrer-Policy"), "strict-origin-when-cross-origin")


if __name__ == "__main__":
    unittest.main()
