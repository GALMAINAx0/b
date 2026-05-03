from PyQt6.QtWebEngineCore import QWebEngineProfile
from .storage import DATA_DIR, CACHE_DIR, DOWNLOAD_DIR
from .blocker import RequestBlocker


def build_profile(parent=None):
    profile = QWebEngineProfile('main', parent)
    profile.setPersistentStoragePath(str(DATA_DIR))
    profile.setCachePath(str(CACHE_DIR))
    profile.setDownloadPath(str(DOWNLOAD_DIR))
    profile.setPersistentCookiesPolicy(
        QWebEngineProfile.PersistentCookiesPolicy.ForcePersistentCookies
    )
    profile.setHttpCacheType(QWebEngineProfile.HttpCacheType.DiskHttpCache)
    blocker = RequestBlocker(profile)
    profile.setUrlRequestInterceptor(blocker)
    profile._blocker = blocker
    return profile
