import ipaddress
import socket
from urllib.parse import urlparse
from typing import Tuple, Optional
from ..config import settings


# Known metadata endpoints to explicitly block
CLOUD_METADATA_IPS = {
    ipaddress.ip_address("169.254.169.254"),
    ipaddress.ip_address("169.254.170.2"),  # AWS ECS task metadata
}


def is_safe_target_url(url: str, allow_local: Optional[bool] = None) -> Tuple[bool, Optional[str]]:
    """
    Validates that a target URL is safe for testing and does not pose an SSRF risk.
    Blocks loopback, link-local, private RFC1918 networks, and cloud metadata endpoints.
    """
    if not url or not isinstance(url, str):
        return False, "Target URL must be a non-empty string."

    url = url.strip()
    if not url:
        return False, "Target URL cannot be whitespace only."

    try:
        parsed = urlparse(url)
    except Exception as e:
        return False, f"Malformed URL: {e}"

    if parsed.scheme.lower() not in ("http", "https"):
        return False, f"Invalid scheme '{parsed.scheme}'. Only 'http' and 'https' are allowed."

    hostname = parsed.hostname
    if not hostname:
        return False, "URL must include a valid hostname."

    # Normalize hostname (lowercase, strip brackets from IPv6)
    hostname = hostname.lower().strip("[]")

    if allow_local is None:
        allow_local = settings.ALLOW_LOCAL_TEST_TARGETS

    # Try resolving hostname to IP addresses
    resolved_ips = []
    try:
        # Check if direct IP address
        direct_ip = ipaddress.ip_address(hostname)
        resolved_ips.append(direct_ip)
    except ValueError:
        # Hostname - resolve via DNS
        try:
            addr_info = socket.getaddrinfo(hostname, None)
            for item in addr_info:
                ip_str = item[4][0]
                resolved_ips.append(ipaddress.ip_address(ip_str))
        except socket.gaierror as e:
            return False, f"Unable to resolve hostname '{hostname}': {e}"
        except Exception as e:
            return False, f"DNS resolution failed for '{hostname}': {e}"

    if not resolved_ips:
        return False, f"No IP addresses resolved for hostname '{hostname}'."

    # Validate each resolved IP address
    for ip in resolved_ips:
        # Explicit cloud metadata check (always blocked even if allow_local is True)
        if ip in CLOUD_METADATA_IPS:
            return False, f"Access to cloud metadata IP {ip} is strictly forbidden."

        if not allow_local:
            if ip.is_loopback:
                return False, f"Target URL resolves to a loopback address ({ip}), which is blocked for security."
            if ip.is_private:
                return False, f"Target URL resolves to a private network address ({ip}), which is blocked for security."
            if ip.is_link_local:
                return False, f"Target URL resolves to a link-local address ({ip}), which is blocked for security."
            if ip.is_unspecified:
                return False, f"Target URL resolves to an unspecified address ({ip}), which is blocked for security."
            if ip.is_multicast:
                return False, f"Target URL resolves to a multicast address ({ip}), which is blocked for security."

    return True, None


def validate_target_url(url: str, allow_local: Optional[bool] = None) -> None:
    """
    Validates that a target URL is safe, raising ValueError if unsafe.
    """
    is_safe, error_msg = is_safe_target_url(url, allow_local=allow_local)
    if not is_safe:
        raise ValueError(error_msg or "Target URL failed security validation.")
