"""Interactive demos for the Rizen AI agents (Scout has its own module: scout_demo_data.py).

Each demo module exposes run(request) -> dict (template context, or {'response': HttpResponse}).
Everything is rule-based today. ai_slot() is the single place to plug an LLM in later: a demo passes it
the facts it computed and renders whatever comes back under `ai` (None means "no AI yet").
"""
import hashlib
import importlib

from django.core.cache import cache

SLUGS = ('atlas', 'quill', 'pulse', 'ledger', 'vega', 'prism', 'echo', 'forge')


def get(slug):
    if slug not in SLUGS:
        return None
    return importlib.import_module('home.agent_demos.%s' % slug)


def ai_slot(agent, payload):
    """LLM hook. Return a dict of extra content for the template, or None. Not implemented yet."""
    return None


def client_ip(request):
    return request.META.get('REMOTE_ADDR', '') or 'unknown'


def rate_limited(request, name, limit, window=3600):
    """Count this call against a per-IP budget. True when the visitor is over it."""
    key = 'agentdemo_%s_%s' % (name, hashlib.sha256(client_ip(request).encode()).hexdigest()[:16])
    used = cache.get(key, 0)
    if used >= limit:
        return True
    cache.set(key, used + 1, window)
    return False


def clip(value, limit=200):
    return (value or '').strip()[:limit]
