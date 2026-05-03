from pathlib import Path
from functools import partial

from PyQt6.QtCore import QUrl, pyqtSignal, Qt
from PyQt6.QtGui import QDesktopServices, QIcon
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
    QPushButton, QFrame, QFileDialog, QMessageBox, QTabBar,
    QStackedWidget, QLabel, QSizePolicy, QMenu
)
from PyQt6.QtWebEngineCore import QWebEnginePage
from PyQt6.QtWebEngineWidgets import QWebEngineView

from .storage import get_connection, DOWNLOAD_DIR, ensure_dirs
from .profile import build_profile
from .home import HomeWidget
from .dialogs import BookmarksDialog, HistoryDialog
from .styles import STYLE
from .utils import normalize_url, HOME_URL, APP_NAME


class DraggableTopBar(QFrame):
    def __init__(self, window):
        super().__init__()
        self.window = window
        self.drag_pos = None

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            child = self.childAt(event.position().toPoint())
            if child is None or isinstance(child, QLabel):
                self.drag_pos = event.globalPosition().toPoint() - self.window.frameGeometry().topLeft()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.drag_pos and event.buttons() & Qt.MouseButton.LeftButton and not self.window.isMaximized():
            self.window.move(event.globalPosition().toPoint() - self.drag_pos)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self.drag_pos = None
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.window.toggle_maximize_restore()
        super().mouseDoubleClickEvent(event)


class BrowserPage(QWebEnginePage):
    popupRequested = pyqtSignal(QUrl)

    def createWindow(self, _type):
        page = BrowserPage(self.profile(), self)
        page.urlChanged.connect(self.popupRequested.emit)
        return page


class BrowserTab(QWidget):
    titleChanged = pyqtSignal(str)
    urlChanged = pyqtSignal(str)
    iconChanged = pyqtSignal(QIcon)
    openRequested = pyqtSignal(str)

    def __init__(self, profile, conn, is_home=False):
        super().__init__()
        self.conn = conn
        self.is_home = is_home
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        if is_home:
            self.home_widget = HomeWidget(conn)
            self.home_widget.openUrl.connect(self.openRequested.emit)
            self.view = None
            layout.addWidget(self.home_widget)
        else:
            self.view = QWebEngineView()
            self.page = BrowserPage(profile, self.view)
            self.view.setPage(self.page)
            self.page.popupRequested.connect(lambda url: self.openRequested.emit(url.toString()))
            self.view.titleChanged.connect(self.titleChanged.emit)
            self.view.urlChanged.connect(lambda url: self.urlChanged.emit(url.toString()))
            self.view.iconChanged.connect(self.iconChanged.emit)
            self.view.loadFinished.connect(self.store_history)
            layout.addWidget(self.view)

    def navigate(self, url):
        if self.view:
            self.view.setUrl(QUrl(url))

    def current_url(self):
        if self.is_home:
            return HOME_URL
        return self.view.url().toString()

    def current_title(self):
        if self.is_home:
            return 'Dashboard'
        return self.view.title() or self.current_url()

    def store_history(self, ok):
        if not ok:
            return
        url = self.current_url()
        if not url or url.startswith('data:'):
            return
        self.conn.execute('INSERT INTO history (title, url) VALUES (?, ?)', (self.current_title(), url))
        self.conn.commit()


class BrowserWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        ensure_dirs()
        self.conn = get_connection()
        self.profile = build_profile(self)
        self.sidebar_expanded = False

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
        self.setWindowTitle(APP_NAME)
        self.resize(1480, 920)
        self.setStyleSheet(STYLE)
        self.profile.downloadRequested.connect(self.on_download_requested)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.side_panel = self.build_side_panel()
        layout.addWidget(self.side_panel)
        self.apply_sidebar_mode()

        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)
        layout.addWidget(right)

        self.header = self.build_header()
        right_layout.addWidget(self.header)

        self.pages = QStackedWidget()
        right_layout.addWidget(self.pages)

        self.open_home_tab()
        self.new_tab('https://www.google.com', False)
        self.tab_bar.setCurrentIndex(0)
        self.sync_current_page(0)
        self.reload_quick_links()

    def build_side_panel(self):
        side_panel = QFrame()
        side_panel.setObjectName('SidePanel')
        side_panel.setFixedWidth(52)
        side_layout = QVBoxLayout(side_panel)
        side_layout.setContentsMargins(8, 8, 8, 8)
        side_layout.setSpacing(6)

        self.toggle_btn = QPushButton('☰')
        self.home_btn = QPushButton('⌂')
        self.bookmarks_btn = QPushButton('★')
        self.history_btn = QPushButton('🕘')
        self.downloads_btn = QPushButton('↓')
        self.new_tab_side_btn = QPushButton('+')
        self.side_buttons = [self.toggle_btn, self.home_btn, self.bookmarks_btn, self.history_btn, self.downloads_btn, self.new_tab_side_btn]
        for btn in self.side_buttons:
            btn.setProperty('nav', True)
            side_layout.addWidget(btn)
        side_layout.addStretch()

        self.toggle_btn.clicked.connect(self.toggle_sidebar)
        self.home_btn.clicked.connect(self.open_home_tab)
        self.bookmarks_btn.clicked.connect(self.show_bookmarks)
        self.history_btn.clicked.connect(self.show_history)
        self.downloads_btn.clicked.connect(self.open_download_folder)
        self.new_tab_side_btn.clicked.connect(lambda: self.new_tab(HOME_URL, True))
        return side_panel

    def build_header(self):
        header = QFrame()
        header.setObjectName('HeaderWrap')
        wrap = QVBoxLayout(header)
        wrap.setContentsMargins(0, 0, 0, 0)
        wrap.setSpacing(0)

        top = DraggableTopBar(self)
        top.setObjectName('TopStrip')
        top_layout = QHBoxLayout(top)
        top_layout.setContentsMargins(8, 4, 8, 4)
        top_layout.setSpacing(6)

        brand = QLabel('◯')
        brand.setObjectName('BrandMark')
        top_layout.addWidget(brand)

        sync_btn = QPushButton('⟲')
        sync_btn.setProperty('ghost', True)
        sync_btn.setFixedWidth(28)
        top_layout.addWidget(sync_btn)

        self.tab_bar = QTabBar()
        self.tab_bar.setMovable(True)
        self.tab_bar.setTabsClosable(True)
        self.tab_bar.setDocumentMode(True)
        self.tab_bar.setElideMode(Qt.TextElideMode.ElideRight)
        self.tab_bar.currentChanged.connect(self.sync_current_page)
        self.tab_bar.tabCloseRequested.connect(self.close_tab)
        top_layout.addWidget(self.tab_bar, 1)

        self.new_tab_top_btn = QPushButton('+')
        self.new_tab_top_btn.setProperty('ghost', True)
        self.new_tab_top_btn.setFixedWidth(30)
        self.new_tab_top_btn.clicked.connect(lambda: self.new_tab(HOME_URL, True))
        top_layout.addWidget(self.new_tab_top_btn)

        self.tab_search_btn = QPushButton('⌕')
        self.tab_search_btn.setProperty('ghost', True)
        self.tab_search_btn.setFixedWidth(28)
        top_layout.addWidget(self.tab_search_btn)

        self.min_btn = QPushButton('▁')
        self.max_btn = QPushButton('▢')
        self.close_btn = QPushButton('✕')
        for btn in [self.min_btn, self.max_btn, self.close_btn]:
            btn.setProperty('ghost', True)
            btn.setFixedWidth(30)
            top_layout.addWidget(btn)

        nav = QFrame()
        nav.setObjectName('NavStrip')
        nav_layout = QHBoxLayout(nav)
        nav_layout.setContentsMargins(8, 4, 8, 4)
        nav_layout.setSpacing(6)

        self.back_btn = QPushButton('‹')
        self.forward_btn = QPushButton('›')
        self.reload_btn = QPushButton('↻')
        self.badge_btn = QPushButton('VPN')
        self.badge_btn.setProperty('chip', True)
        for btn in [self.back_btn, self.forward_btn, self.reload_btn]:
            btn.setProperty('ghost', True)
            btn.setFixedWidth(28)
            nav_layout.addWidget(btn)
        nav_layout.addWidget(self.badge_btn)

        self.address_bar = QLineEdit()
        self.address_bar.setPlaceholderText('Enter search or web address')
        self.address_bar.returnPressed.connect(self.go_to_address)
        nav_layout.addWidget(self.address_bar, 1)

        self.menu_btn = QPushButton('⋮')
        self.menu_btn.setProperty('ghost', True)
        self.menu_btn.setFixedWidth(28)
        nav_layout.addWidget(self.menu_btn)

        quick = QFrame()
        quick.setObjectName('QuickStrip')
        quick_layout = QHBoxLayout(quick)
        quick_layout.setContentsMargins(8, 3, 8, 3)
        quick_layout.setSpacing(2)
        self.quick_layout = quick_layout

        wrap.addWidget(top)
        wrap.addWidget(nav)
        wrap.addWidget(quick)

        self.back_btn.clicked.connect(lambda: self.current_view_call('back'))
        self.forward_btn.clicked.connect(lambda: self.current_view_call('forward'))
        self.reload_btn.clicked.connect(lambda: self.current_view_call('reload'))
        self.menu_btn.clicked.connect(self.show_browser_menu)
        self.min_btn.clicked.connect(self.showMinimized)
        self.max_btn.clicked.connect(self.toggle_maximize_restore)
        self.close_btn.clicked.connect(self.close)
        return header

    def toggle_maximize_restore(self):
        if self.isMaximized():
            self.showNormal()
            self.max_btn.setText('▢')
        else:
            self.showMaximized()
            self.max_btn.setText('❐')

    def apply_sidebar_mode(self):
        self.side_panel.setFixedWidth(168 if self.sidebar_expanded else 52)
        if self.sidebar_expanded:
            labels = ['Collapse', 'Home', 'Bookmarks', 'History', 'Downloads', 'New tab']
            for btn, label in zip(self.side_buttons, labels):
                btn.setText(label)
                btn.setFixedSize(148, 34)
                btn.setStyleSheet('text-align:left; padding-left:12px;')
        else:
            labels = ['☰', '⌂', '★', '🕘', '↓', '+']
            for btn, label in zip(self.side_buttons, labels):
                btn.setText(label)
                btn.setFixedSize(34, 34)
                btn.setStyleSheet('text-align:center; padding-left:0px;')

    def toggle_sidebar(self):
        self.sidebar_expanded = not self.sidebar_expanded
        self.apply_sidebar_mode()

    def open_home_tab(self):
        self.new_tab(HOME_URL, True)

    def new_tab(self, url=HOME_URL, switch=True):
        is_home = (url == HOME_URL)
        tab = BrowserTab(self.profile, self.conn, is_home=is_home)
        tab.titleChanged.connect(lambda title, t=tab: self.update_tab_title(t, title))
        tab.urlChanged.connect(self.update_address_bar)
        tab.iconChanged.connect(lambda icon, t=tab: self.update_tab_icon(t, icon))
        tab.openRequested.connect(lambda target: self.new_tab(target, True))

        index = self.pages.addWidget(tab)
        self.tab_bar.addTab('Dashboard' if is_home else 'New Tab')
        if not is_home:
            tab.navigate(url)
        if switch:
            self.tab_bar.setCurrentIndex(index)
            self.sync_current_page(index)
        return tab

    def sync_current_page(self, index):
        if index < 0 or index >= self.pages.count():
            return
        self.pages.setCurrentIndex(index)
        widget = self.pages.widget(index)
        self.address_bar.setText(widget.current_url())
        self.setWindowTitle(f'{widget.current_title()} — {APP_NAME}')

    def current_tab(self):
        index = self.tab_bar.currentIndex()
        return self.pages.widget(index) if index >= 0 else None

    def current_view_call(self, method_name):
        tab = self.current_tab()
        if tab and tab.view:
            getattr(tab.view, method_name)()

    def duplicate_current_tab(self):
        tab = self.current_tab()
        if tab:
            self.new_tab(tab.current_url(), True)

    def copy_current_url(self):
        tab = self.current_tab()
        if not tab:
            return
        url = tab.current_url()
        self.clipboard().setText(url)
        QMessageBox.information(self, 'Copied', f'Copied URL:\n{url}')

    def show_browser_menu(self):
        menu = QMenu(self)
        new_tab_action = menu.addAction('New tab')
        home_action = menu.addAction('Open dashboard')
        dup_action = menu.addAction('Duplicate current tab')
        bookmark_action = menu.addAction('Bookmark current page')
        copy_action = menu.addAction('Copy current URL')
        downloads_action = menu.addAction('Open downloads folder')
        bookmarks_action = menu.addAction('Bookmarks')
        history_action = menu.addAction('History')
        action = menu.exec(self.menu_btn.mapToGlobal(self.menu_btn.rect().bottomLeft()))
        if action == new_tab_action:
            self.new_tab(HOME_URL, True)
        elif action == home_action:
            self.open_home_tab()
        elif action == dup_action:
            self.duplicate_current_tab()
        elif action == bookmark_action:
            self.add_bookmark()
        elif action == copy_action:
            self.copy_current_url()
        elif action == downloads_action:
            self.open_download_folder()
        elif action == bookmarks_action:
            self.show_bookmarks()
        elif action == history_action:
            self.show_history()

    def go_to_address(self):
        text = self.address_bar.text().strip()
        if not text:
            return
        target = normalize_url(text)
        tab = self.current_tab()
        if not tab or tab.is_home:
            self.new_tab(target, True)
        else:
            tab.navigate(target)

    def update_tab_title(self, tab, title):
        index = self.pages.indexOf(tab)
        if index >= 0:
            self.tab_bar.setTabText(index, (title or 'New Tab')[:28])

    def update_tab_icon(self, tab, icon):
        index = self.pages.indexOf(tab)
        if index >= 0:
            self.tab_bar.setTabIcon(index, icon)

    def update_address_bar(self, url):
        tab = self.current_tab()
        if tab and tab.current_url() == url:
            self.address_bar.setText(url)

    def close_tab(self, index):
        if self.pages.count() == 1:
            return
        widget = self.pages.widget(index)
        self.pages.removeWidget(widget)
        widget.deleteLater()
        self.tab_bar.removeTab(index)
        if self.tab_bar.count():
            self.sync_current_page(max(0, self.tab_bar.currentIndex()))

    def add_bookmark(self):
        tab = self.current_tab()
        if not tab or tab.is_home:
            return
        title = tab.current_title() or 'Untitled'
        url = tab.current_url()
        self.conn.execute('INSERT OR IGNORE INTO bookmarks (title, url) VALUES (?, ?)', (title, url))
        self.conn.commit()
        self.reload_quick_links()
        QMessageBox.information(self, 'Bookmark saved', f'Saved: {title}')

    def clear_quick_links(self):
        while self.quick_layout.count():
            item = self.quick_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def reload_quick_links(self):
        self.clear_quick_links()
        rows = self.conn.execute('SELECT title, url FROM speed_dials ORDER BY id ASC LIMIT 14').fetchall()
        for title, url in rows:
            btn = QPushButton(title[:18])
            btn.setProperty('quick', True)
            btn.clicked.connect(partial(self.new_tab, url, True))
            btn.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
            self.quick_layout.addWidget(btn)
        self.quick_layout.addStretch(1)

    def show_bookmarks(self):
        dlg = BookmarksDialog(self.conn, self)
        if dlg.exec():
            url = dlg.selected_url()
            if url:
                self.new_tab(url, True)
                self.reload_quick_links()

    def show_history(self):
        dlg = HistoryDialog(self.conn, self)
        if dlg.exec():
            url = dlg.selected_url()
            if url:
                self.new_tab(url, True)

    def open_download_folder(self):
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(DOWNLOAD_DIR)))

    def on_download_requested(self, download):
        path, _ = QFileDialog.getSaveFileName(self, 'Save file', str(DOWNLOAD_DIR / download.downloadFileName()))
        if path:
            p = Path(path)
            download.setDownloadDirectory(str(p.parent))
            download.setDownloadFileName(p.name)
            download.accept()
