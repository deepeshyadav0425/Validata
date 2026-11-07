"""
Web Article Scraper.
Fetches articles from any news or blog URL, cleans markup, and extracts metadata.
"""

import re
import socket
import ipaddress
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

# Maximum allowed article download size (5 MB) to prevent memory exhaustion DoS
MAX_DOWNLOAD_BYTES = 5 * 1024 * 1024


def validate_url_security(url: str) -> tuple[bool, str | None]:
    """
    Validate URL to protect against Server-Side Request Forgery (SSRF).
    Blocks private IP ranges, loopbacks, link-local addresses, and cloud metadata services.
    """
    try:
        parsed = urlparse(url)
    except Exception as e:
        return False, f"Malformed URL: {e}"

    if parsed.scheme.lower() not in ("http", "https"):
        return False, "Only HTTP and HTTPS URLs are permitted."

    hostname = parsed.hostname
    if not hostname:
        return False, "URL is missing a valid hostname."

    hostname_lower = hostname.lower()
    if hostname_lower in ("localhost", "127.0.0.1", "::1", "0.0.0.0"):
        return False, "Access to local loopback addresses is blocked for security."

    # Prevent AWS / GCP / Azure metadata endpoint access
    if hostname_lower == "169.254.169.254" or hostname_lower.endswith(".internal"):
        return False, "Access to cloud metadata and internal endpoints is blocked."

    # Resolve hostname and check IP classification
    try:
        addr_info = socket.getaddrinfo(hostname, None)
        for _, _, _, _, sockaddr in addr_info:
            ip_str = sockaddr[0]
            ip = ipaddress.ip_address(ip_str)
            if (
                ip.is_private
                or ip.is_loopback
                or ip.is_link_local
                or ip.is_reserved
                or ip.is_multicast
            ):
                return False, f"Access to private/internal network IP ({ip_str}) is blocked for security."
    except socket.gaierror:
        # Domain cannot be resolved via DNS
        return False, f"Unable to resolve domain '{hostname}' via DNS."
    except Exception as e:
        return False, f"Network validation failed: {e}"

    return True, None


def scrape_article_from_url(url: str, timeout: int = 10) -> dict:
    """
    Fetch and extract article content and metadata from a URL with SSRF protection.
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

    # Run SSRF security validation
    is_safe, sec_err = validate_url_security(url)
    if not is_safe:
        return {"success": False, "error": f"Security Check: {sec_err}"}

    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        if domain.startswith("www."):
            domain = domain[4:]
    except Exception as e:
        return {"success": False, "error": f"Invalid URL structure: {e}"}

    try:
        # Use stream=True to guard against huge payload DoS
        resp = requests.get(
            url,
            headers=HEADERS,
            timeout=timeout,
            allow_redirects=True,
            stream=True
        )

        # Check final redirected URL for SSRF protection as well
        if resp.url and resp.url != url:
            is_redirect_safe, redir_err = validate_url_security(resp.url)
            if not is_redirect_safe:
                resp.close()
                return {"success": False, "error": f"Security Check on redirect: {redir_err}"}

        if resp.status_code >= 400:
            resp.close()
            return {
                "success": False,
                "error": f"Target server returned HTTP status {resp.status_code} ({resp.reason})"
            }

        # Read only up to MAX_DOWNLOAD_BYTES
        raw_content = b""
        for chunk in resp.iter_content(chunk_size=16384):
            raw_content += chunk
            if len(raw_content) > MAX_DOWNLOAD_BYTES:
                resp.close()
                return {
                    "success": False,
                    "error": "Article size exceeds maximum permitted download limit (5 MB)."
                }
        resp.close()

        soup = BeautifulSoup(raw_content, "html.parser")

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
