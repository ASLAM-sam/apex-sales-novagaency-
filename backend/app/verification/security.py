import ipaddress
import socket
from typing import Optional, Tuple
from urllib.parse import urlparse


BLOCKED_HOSTNAMES = {
    "localhost",
    "localhost.localdomain",
    "loopback",
}


def is_private_or_restricted_ip(ip_str: str) -> bool:
    """Check if an IP address string is private, loopback, link-local, or reserved."""
    try:
        ip = ipaddress.ip_address(ip_str)
        return (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_multicast
            or ip.is_reserved
            or ip.is_unspecified
        )
    except ValueError:
        return False


def validate_and_sanitize_url(url: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Validate URL to prevent Server-Side Request Forgery (SSRF).
    Returns (is_safe, error_message, sanitized_url).
    """
    if not url or not isinstance(url, str):
        return False, "URL is empty or not a string.", None

    url_trimmed = url.strip()
    if not (url_trimmed.startswith("http://") or url_trimmed.startswith("https://")):
        url_trimmed = "https://" + url_trimmed

    try:
        parsed = urlparse(url_trimmed)
    except Exception as e:
        return False, f"Malformed URL: {str(e)}", None

    scheme = (parsed.scheme or "").lower()
    if scheme not in ("http", "https"):
        return False, f"Unsupported scheme '{scheme}'. Only http and https are allowed.", None

    hostname = (parsed.hostname or "").lower()
    if not hostname:
        return False, "URL missing valid hostname.", None

    if hostname in BLOCKED_HOSTNAMES or hostname.endswith(".local"):
        return False, f"Blocked target hostname '{hostname}'.", None

    # Check direct IP strings
    if is_private_or_restricted_ip(hostname):
        return False, f"Access to restricted IP address '{hostname}' is blocked.", None

    # Resolve domain via DNS and check resolved IP addresses
    try:
        port = parsed.port or (443 if scheme == "https" else 80)
        addr_info = socket.getaddrinfo(hostname, port, socket.AF_UNSPEC, socket.SOCK_STREAM)
        resolved_ips = {item[4][0] for item in addr_info if item and item[4]}

        for resolved_ip in resolved_ips:
            if is_private_or_restricted_ip(resolved_ip):
                return False, f"Domain '{hostname}' resolves to restricted IP '{resolved_ip}'.", None
    except socket.gaierror:
        return False, f"Domain resolution failed for '{hostname}'.", None
    except Exception as e:
        return False, f"DNS validation error for '{hostname}': {str(e)}", None

    sanitized_url = parsed.geturl()
    return True, None, sanitized_url
