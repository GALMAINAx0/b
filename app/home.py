from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QFrame, QGridLayout, QInputDialog
from .utils import normalize_url


class HomeWidget(QWidget):
    openUrl = pyqtSignal(str)

    def __init__(self, conn):
        super().__init__()
        self.conn = conn
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 28, 28, 28)
        root.setSpacing(18)

        hero = QFrame()
        hero.setObjectName('Card')
        hero_layout = QVBoxLayout(hero)
        hero_layout.setContentsMargins(24, 24, 24, 24)
        hero_layout.setSpacing(12)

        title = QLabel('Hi! Welcome back')
        title.setObjectName('HeroTitle')
        subtitle = QLabel('A faster way to browse, search, and return to what matters.')
        subtitle.setObjectName('Muted')

        search_row = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText('Search or enter web address')
        go_btn = QPushButton('Go')
        go_btn.setProperty('accent', True)
        self.search.returnPressed.connect(self.submit)
        go_btn.clicked.connect(self.submit)
        search_row.addWidget(self.search)
        search_row.addWidget(go_btn)

        hero_layout.addWidget(title)
        hero_layout.addWidget(subtitle)
        hero_layout.addLayout(search_row)
        root.addWidget(hero)

        shortcuts = QFrame()
        shortcuts.setObjectName('Card')
        shortcuts_layout = QVBoxLayout(shortcuts)
        shortcuts_layout.setContentsMargins(24, 24, 24, 24)
        shortcuts_layout.setSpacing(14)

        top = QHBoxLayout()
        section_title = QLabel('Quick access')
        section_title.setStyleSheet('font-size:18px;font-weight:600;')
        self.add_btn = QPushButton('Add shortcut')
        self.refresh_btn = QPushButton('Refresh')
        top.addWidget(section_title)
        top.addStretch()
        top.addWidget(self.add_btn)
        top.addWidget(self.refresh_btn)
        shortcuts_layout.addLayout(top)

        self.grid = QGridLayout()
        self.grid.setHorizontalSpacing(12)
        self.grid.setVerticalSpacing(12)
        shortcuts_layout.addLayout(self.grid)
        root.addWidget(shortcuts)

        self.add_btn.clicked.connect(self.add_shortcut)
        self.refresh_btn.clicked.connect(self.reload_tiles)
        self.reload_tiles()
        root.addStretch()

    def submit(self):
        text = self.search.text().strip()
        if text:
            self.openUrl.emit(normalize_url(text))

    def clear_grid(self):
        while self.grid.count():
            item = self.grid.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def tile_button(self, title, url):
        btn = QPushButton(title)
        btn.setMinimumHeight(88)
        btn.clicked.connect(lambda checked=False, u=url: self.openUrl.emit(u))
        btn.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        btn.customContextMenuRequested.connect(lambda pos, u=url: self.remove_shortcut(u))
        return btn

    def reload_tiles(self):
        self.clear_grid()
        rows = self.conn.execute('SELECT title, url FROM speed_dials ORDER BY id ASC LIMIT 12').fetchall()
        for i, (title, url) in enumerate(rows):
            r, c = divmod(i, 4)
            self.grid.addWidget(self.tile_button(title, url), r, c)

    def add_shortcut(self):
        title, ok = QInputDialog.getText(self, 'Shortcut title', 'Title:')
        if not ok or not title.strip():
            return
        url, ok = QInputDialog.getText(self, 'Shortcut URL', 'URL:')
        if not ok or not url.strip():
            return
        self.conn.execute('INSERT OR IGNORE INTO speed_dials (title, url) VALUES (?, ?)', (title.strip(), normalize_url(url.strip())))
        self.conn.commit()
        self.reload_tiles()

    def remove_shortcut(self, url):
        self.conn.execute('DELETE FROM speed_dials WHERE url = ?', (url,))
        self.conn.commit()
        self.reload_tiles()
