# app/services/analytics.py

import ipaddress


def anonymize_ip(ip: str | None) -> str | None:
    """
    Anonymize IP address before storing analytics data.

    IPv4:
        192.168.1.45 -> 192.168.1.xxx

    IPv6:
        2001:db8:85a3::8a2e:370:7334
        -> 2001:db8:85a3::xxxx

    Returns None for invalid/missing IPs.
    """

    if not ip:
        return None

    try:
        ip_obj = ipaddress.ip_address(ip)

    except ValueError:
        return None

    # IPv4 anonymization
    if isinstance(ip_obj, ipaddress.IPv4Address):
        octets = ip.split(".")
        octets[-1] = "xxx"
        return ".".join(octets)

    # IPv6 anonymization
    elif isinstance(ip_obj, ipaddress.IPv6Address):
        parts = ip.split(":")

        # Keep the network part, hide the host part
        return ":".join(parts[:4]) + ":xxxx"
