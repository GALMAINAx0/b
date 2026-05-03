from urllib.parse import quote_plus

HOME_URL = 'app://home'
APP_NAME = 'Future Browser'


def normalize_url(text: str) -> str:
    text = text.strip()
    lower = text.lower()
    if lower.startswith(('http://', 'https://', 'file://')):
        return text
    if ' ' in text or '.' not in text:
        return f'https://www.google.com/search?q={quote_plus(text)}'
    return 'https://' + text
