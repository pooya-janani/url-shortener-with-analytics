import geoip2.database
from geoip2.errors import AddressNotFoundError


GEOIP_DB_PATH = "/app/geoip/GeoLite2-City.mmdb"

_reader = None


def get_reader():
    """
    Lazily initialize GeoIP database reader.
    """

    global _reader

    if _reader is None:
        _reader = geoip2.database.Reader(GEOIP_DB_PATH)

    return _reader


def get_location(ip: str | None) -> dict[str, str | None]:
    """
    Lookup country and city from an IP address.
    """

    if not ip:
        return {
            "country": None,
            "city": None
        }

    try:
        reader = get_reader()

        response = reader.city(ip)

        return {
            "country": response.country.name,
            "city": response.city.name
        }

    except AddressNotFoundError:
        return {
            "country": None,
            "city": None
        }