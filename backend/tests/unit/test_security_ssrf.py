import pytest
from app.agents.tools.fetch_page import validate_url_safety
from app.core.exceptions import SecurityError


def test_ssrf_blocks_localhost():
    with pytest.raises(SecurityError, match="blocked"):
        validate_url_safety("http://localhost:8080/admin")


def test_ssrf_blocks_loopback_ip():
    with pytest.raises(SecurityError, match="Blocked private/internal IP"):
        validate_url_safety("http://127.0.0.1:5000/metrics")


def test_ssrf_blocks_aws_metadata():
    with pytest.raises(SecurityError, match="Blocked private/internal IP"):
        validate_url_safety("http://169.254.169.254/latest/meta-data/")


def test_ssrf_blocks_private_rfc1918():
    with pytest.raises(SecurityError, match="Blocked private/internal IP"):
        validate_url_safety("http://192.168.1.1/router")


def test_ssrf_allows_public_url():
    assert validate_url_safety("https://techcrunch.com/funding") is True
