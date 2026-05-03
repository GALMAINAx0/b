from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QListWidget, QListWidgetItem, QPushButton, QHBoxLayout


class BookmarksDialog(QDialog):
    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn = conn
        self.setWindowTitle('Bookmarks')
        self.resize(760, 500)
        layout = QVBoxLayout(self)
        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget)
        buttons = QHBoxLayout()
        self.open_btn = QPushButton('Open')
        self.delete_btn = QPushButton('Delete')
        buttons.addWidget(self.open_btn)
        buttons.addWidget(self.delete_btn)
        layout.addLayout(buttons)
        self.open_btn.clicked.connect(self.accept)
        self.delete_btn.clicked.connect(self.delete_selected)
        self.populate()

    def populate(self):
        self.list_widget.clear()
        rows = self.conn.execute('SELECT title, url FROM bookmarks ORDER BY created_at DESC').fetchall()
        for title, url in rows:
            item = QListWidgetItem(f'{title} — {url}')
            item.setData(Qt.ItemDataRole.UserRole, url)
            self.list_widget.addItem(item)

    def selected_url(self):
        item = self.list_widget.currentItem()
        return item.data(Qt.ItemDataRole.UserRole) if item else None

    def delete_selected(self):
        url = self.selected_url()
        if not url:
            return
        self.conn.execute('DELETE FROM bookmarks WHERE url = ?', (url,))
        self.conn.commit()
        self.populate()


class HistoryDialog(QDialog):
    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn = conn
        self.setWindowTitle('History')
        self.resize(860, 540)
        layout = QVBoxLayout(self)
        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget)
        self.clear_btn = QPushButton('Clear history')
        layout.addWidget(self.clear_btn)
        self.clear_btn.clicked.connect(self.clear_history)
        self.populate()

    def populate(self):
        self.list_widget.clear()
        rows = self.conn.execute('SELECT title, url, visited_at FROM history ORDER BY id DESC LIMIT 300').fetchall()
        for title, url, visited_at in rows:
            item = QListWidgetItem(f'[{visited_at}] {title or url} — {url}')
            item.setData(Qt.ItemDataRole.UserRole, url)
            self.list_widget.addItem(item)

    def selected_url(self):
        item = self.list_widget.currentItem()
        return item.data(Qt.ItemDataRole.UserRole) if item else None

    def clear_history(self):
        self.conn.execute('DELETE FROM history')
        self.conn.commit()
        self.populate()
