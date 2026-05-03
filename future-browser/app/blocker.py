from PyQt6.QtWebEngineCore import QWebEngineUrlRequestInterceptor

BLOCKED_HOST_KEYWORDS = [
    'doubleclick', 'googlesyndication', 'adservice', 'adsystem', 'adnxs',
    'taboola', 'outbrain', 'tracking', 'analytics', 'pixel.'
]


class RequestBlocker(QWebEngineUrlRequestInterceptor):
    def interceptRequest(self, info):
        host = info.requestUrl().host().lower()
        if any(keyword in host for keyword in BLOCKED_HOST_KEYWORDS):
            info.block(True)
