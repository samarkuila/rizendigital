"""Fetch a public web page for the Atlas demo without letting visitors reach our own network (SSRF guard).

Every hop's hostname is resolved, every resolved address must be globally routable, and we connect to that
exact address (no second DNS lookup), so a hostname cannot rebind to an internal IP between check and use.
Only http/https on ports 80/443, a small redirect limit, a short timeout and a hard byte cap.
"""
import http.client
import ipaddress
import socket
import ssl
import time
from urllib.parse import urljoin, urlsplit

MAX_BYTES = 1_500_000
TIMEOUT = 8
MAX_REDIRECTS = 4
UA = 'RizenAtlasDemo/1.0 (+https://rizendigital.com/ai-agents/atlas/)'


class FetchError(Exception):
    pass


def normalise(raw):
    raw = (raw or '').strip()
    if not raw:
        raise FetchError('Enter a website address.')
    if '://' not in raw:
        raw = 'https://' + raw
    parts = urlsplit(raw)
    if parts.scheme not in ('http', 'https'):
        raise FetchError('Only http and https addresses can be checked.')
    if not parts.hostname or parts.username or parts.password:
        raise FetchError('That address is not valid.')
    try:
        port = parts.port or (443 if parts.scheme == 'https' else 80)
    except ValueError:
        raise FetchError('That address is not valid.')
    if port not in (80, 443):
        raise FetchError('Only standard web ports (80 and 443) can be checked.')
    return parts._replace(fragment='').geturl()


def _public_ip(host, port):
    try:
        infos = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    except socket.gaierror:
        raise FetchError('Could not find that website. Check the address.')
    ips = []
    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if not ip.is_global:
            raise FetchError('That address points to a private network and cannot be checked.')
        ips.append(str(ip))
    if not ips:
        raise FetchError('Could not find that website. Check the address.')
    return ips[0]


def _one(url, cap):
    parts = urlsplit(url)
    host = parts.hostname
    https = parts.scheme == 'https'
    port = parts.port or (443 if https else 80)
    ip = _public_ip(host, port)
    started = time.monotonic()
    try:
        sock = socket.create_connection((ip, port), timeout=TIMEOUT)
        if https:
            sock = ssl.create_default_context().wrap_socket(sock, server_hostname=host)
        conn = http.client.HTTPConnection(host, port, timeout=TIMEOUT)
        conn.sock = sock
        path = (parts.path or '/') + ('?' + parts.query if parts.query else '')
        conn.request('GET', path, headers={'Host': parts.netloc, 'User-Agent': UA, 'Accept': 'text/html,*/*;q=0.5',
                                           'Accept-Encoding': 'identity', 'Connection': 'close'})
        resp = conn.getresponse()
        headers = {k.lower(): v for k, v in resp.getheaders()}
        body = resp.read(cap + 1)
        elapsed = int((time.monotonic() - started) * 1000)
        conn.close()
    except ssl.SSLError:
        raise FetchError('The site\'s security certificate could not be verified.')
    except (OSError, http.client.HTTPException):
        raise FetchError('The site did not respond in time or refused the connection.')
    return resp.status, headers, body[:cap], len(body) > cap, elapsed


def fetch(url, cap=MAX_BYTES):
    """Follow redirects safely. Returns dict(url, status, headers, body, truncated, ms, chain, https)."""
    url = normalise(url)
    chain = []
    for _ in range(MAX_REDIRECTS + 1):
        status, headers, body, truncated, ms = _one(url, cap)
        chain.append({'url': url, 'status': status})
        if status in (301, 302, 303, 307, 308) and headers.get('location'):
            url = normalise(urljoin(url, headers['location']))
            continue
        return {'url': url, 'status': status, 'headers': headers, 'body': body, 'truncated': truncated,
                'ms': ms, 'chain': chain, 'https': url.startswith('https://')}
    raise FetchError('Too many redirects (more than %d).' % MAX_REDIRECTS)
