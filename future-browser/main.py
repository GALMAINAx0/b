import sys
from PyQt6.QtWidgets import QApplication
from app.browser import BrowserWindow


def main():
    app = QApplication(sys.argv)
    window = BrowserWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
