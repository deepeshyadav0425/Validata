"""
Web Article Scraper.
Fetches articles from any news or blog URL, cleans markup, and extracts metadata.
"""

import re
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


def scrape_article_from_url(url: str, timeout: int = 10) -> dict:
    """
    Fetch and extract article content and metadata from a URL.
    Returns:
        dict: {
            "success": bool,
            "url": str,
            "domain": str,
            "title": str,
            "body": str,
            "author": str,
            "publish_date": str,
            "publisher": str,
            "word_count": int,
            "error": str or None
        }
    """
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        if domain.startswith("www."):
            domain = domain[4:]
    except Exception as e:
        return {"success": False, "error": f"Invalid URL structure: {e}"}

    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout, allow_redirects=True)
        if resp.status_code >= 400:
            return {
                "success": False,
                "error": f"Target server returned HTTP status {resp.status_code} ({resp.reason})"
            }

        soup = BeautifulSoup(resp.content, "html.parser")

        # Strip undesirable tags
        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "noscript", "form", "svg"]):
            tag.decompose()

        # 1. Extract Title
        title = ""
        og_title = soup.find("meta", property="og:title")
        if og_title and og_title.get("content"):
            title = og_title["content"].strip()
        elif soup.find("h1"):
            title = soup.find("h1").get_text().strip()
        elif soup.title:
            title = soup.title.get_text().strip()

        # 2. Extract Publisher / Site Name
        publisher = ""
        og_site = soup.find("meta", property="og:site_name")
        if og_site and og_site.get("content"):
            publisher = og_site["content"].strip()
        else:
            publisher = domain

        # 3. Extract Author
        author = ""
        meta_author = soup.find("meta", attrs={"name": "author"}) or soup.find("meta", property="article:author")
        if meta_author and meta_author.get("content"):
            author = meta_author["content"].strip()
        else:
            author_tag = soup.find(class_=re.compile(r"author|byline", re.IGNORECASE))
            if author_tag:
                author = author_tag.get_text().strip()

        # 4. Extract Published Date
        pub_date = ""
        meta_time = (
            soup.find("meta", property="article:published_time")
            or soup.find("meta", attrs={"name": "pubdate"})
            or soup.find("meta", attrs={"name": "date"})
        )
        if meta_time and meta_time.get("content"):
            pub_date = meta_time["content"].strip()
        else:
            time_tag = soup.find("time")
            if time_tag:
                pub_date = time_tag.get_text().strip() or time_tag.get("datetime", "")

        # 5. Extract Article Body Text
        body = ""
        article_elem = soup.find("article") or soup.find(class_=re.compile(r"article-content|story-body|post-content|entry-content", re.IGNORECASE))
        if article_elem:
            paras = article_elem.find_all("p")
            body_parts = [p.get_text().strip() for p in paras if len(p.get_text().strip()) > 20]
            body = "\n\n".join(body_parts)

        # Fallback to general paragraph collection
        if not body or len(body.split()) < 30:
            paras = soup.find_all("p")
            body_parts = [p.get_text().strip() for p in paras if len(p.get_text().strip()) > 30]
            body = "\n\n".join(body_parts)

        # Clean excess whitespaces
        body = re.sub(r"\n\s*\n", "\n\n", body).strip()
        words = body.split()
        word_count = len(words)

        if not title and not body:
            return {
                "success": False,
                "error": "Could not extract article content. The webpage might require JavaScript rendering or login."
            }

        return {
            "success": True,
            "url": url,
            "domain": domain,
            "title": title or "Untitled Article",
            "body": body,
            "author": author or "Not Listed",
            "publish_date": pub_date or "Unknown",
            "publisher": publisher or domain,
            "word_count": word_count,
            "error": None
        }

    except requests.exceptions.Timeout:
        return {"success": False, "error": "Request timed out while connecting to the news website."}
    except requests.exceptions.RequestException as e:
        return {"success": False, "error": f"Failed to connect to URL: {e}"}
    except Exception as e:
        return {"success": False, "error": f"Error parsing webpage: {e}"}
