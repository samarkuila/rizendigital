class NoIndexPrivateAreasMiddleware:
    """Tell search engines never to index the private back-office areas.

    Sent as an HTTP header so it also covers redirects, CSV exports, JSON endpoints and the Django admin
    (none of which can carry a <meta> tag). Google only obeys noindex on URLs it is allowed to crawl, so
    these paths are deliberately NOT disallowed in robots.txt.
    """
    PREFIXES = ('/studio/', '/admin/', '/get-in-touch/')
    VALUE = 'noindex, nofollow, noarchive'

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if request.path.startswith(self.PREFIXES):
            response['X-Robots-Tag'] = self.VALUE
        return response
