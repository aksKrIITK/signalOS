import ipaddress
import re
import socket
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import httpx
from pydantic import BaseModel, Field
from app.core.exceptions import SecurityError, ToolExecutionError
from app.core.logging import logger

BLOCKED_IP_NETWORKS = [
    ipaddress.ip_network("127.0.0.0/8"),       # Loopback
    ipaddress.ip_network("10.0.0.0/8"),        # Private RFC 1918
    ipaddress.ip_network("172.16.0.0/12"),     # Private RFC 1918
    ipaddress.ip_network("192.168.0.0/16"),    # Private RFC 1918
    ipaddress.ip_network("169.254.0.0/16"),    # Link-local & AWS EC2 Metadata (169.254.169.254)
    ipaddress.ip_network("0.0.0.0/8"),         # Current network
    ipaddress.ip_network("::1/128"),           # IPv6 Loopback
    ipaddress.ip_network("fc00::/7"),          # IPv6 Unique local
    ipaddress.ip_network("fe80::/10"),         # IPv6 Link-local
]

PROMPT_INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?previous\s+instructions", re.IGNORECASE),
    re.compile(r"system\s*:\s*you\s+are\s+now", re.IGNORECASE),
    re.compile(r"you\s+must\s+output\s+the\s+following\s+password", re.IGNORECASE),
    re.compile(r"reveal\s+your\s+system\s+prompt", re.IGNORECASE),
]


def validate_url_safety(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme not in ["http", "https"]:
        raise SecurityError(f"Disallowed URL scheme: {parsed.scheme}")

    hostname = parsed.hostname
    if not hostname:
        raise SecurityError("Invalid URL: missing hostname")

    if hostname.lower() in ["localhost", "metadata.google.internal", "instance-data"]:
        raise SecurityError(f"Access to internal host '{hostname}' is blocked")

    try:
        ip_str = socket.gethostbyname(hostname)
        ip_addr = ipaddress.ip_address(ip_str)
        for net in BLOCKED_IP_NETWORKS:
            if ip_addr in net:
                raise SecurityError(f"Blocked private/internal IP address: {ip_str} for host {hostname}")
    except socket.gaierror:
        # Host could not be resolved, will fail safely during HTTP fetch
        pass

    return True


def sanitize_untrusted_content(text: str) -> str:
    cleaned = text
    for pattern in PROMPT_INJECTION_PATTERNS:
        cleaned = pattern.sub("[POTENTIAL_PROMPT_INJECTION_REDACTED]", cleaned)
    return cleaned


class PageContent(BaseModel):
    url: str
    title: str
    main_content: str
    links: list[str] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)


async def fetch_page(url: str, max_bytes: int = 500_000, timeout_seconds: float = 10.0) -> PageContent:
    validate_url_safety(url)

    headers = {
        "User-Agent": "SignalOS-GTM-Research-Bot/1.0 (+https://signalos.ai)",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    try:
        async with httpx.AsyncClient(timeout=timeout_seconds, follow_redirects=True, max_redirects=3) as client:
            res = await client.get(url, headers=headers)
            if res.status_code != 200:
                raise ToolExecutionError(f"HTTP {res.status_code} when fetching {url}")

            raw_bytes = res.content[:max_bytes]
            html_text = raw_bytes.decode("utf-8", errors="ignore")

            soup = BeautifulSoup(html_text, "html.parser")
            for tag in soup(["script", "style", "nav", "footer", "iframe", "noscript"]):
                tag.decompose()

            title = soup.title.string.strip() if soup.title and soup.title.string else ""
            paragraphs = [p.get_text().strip() for p in soup.find_all(["p", "h1", "h2", "h3", "li"]) if p.get_text().strip()]
            extracted_text = "\n".join(paragraphs[:50])

            sanitized_text = sanitize_untrusted_content(extracted_text)
            links = [a.get("href") for a in soup.find_all("a", href=True) if a["href"].startswith("http")][:15]

            return PageContent(
                url=url,
                title=title,
                main_content=sanitized_text[:8000],
                links=links,
                metadata={"status_code": res.status_code, "content_length": len(raw_bytes)},
            )
    except Exception as e:
        logger.warning("fetch_page_failed", url=url, error=str(e))
        # Graceful degradation fallback
        return PageContent(
            url=url,
            title="Extracted Information",
            main_content=f"Could not retrieve full webpage ({str(e)}). Proceeding with cached GTM knowledge.",
            links=[],
            metadata={"error": str(e)},
        )
