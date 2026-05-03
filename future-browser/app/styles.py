STYLE = """
QMainWindow {
    background: #081018;
}
QWidget {
    color: #e8f1fb;
    font-family: 'Segoe UI', 'Inter', sans-serif;
    font-size: 13px;
}
QFrame#SidePanel {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #09111a, stop:1 #0d1722);
    border-right: 1px solid #162637;
}
QFrame#HeaderWrap {
    background: #060b11;
    border-bottom: 1px solid #182533;
}
QFrame#TopStrip {
    background: #06080d;
    border-bottom: 1px solid #111c28;
}
QFrame#NavStrip {
    background: #0c121a;
    border-bottom: 1px solid #152130;
}
QFrame#QuickStrip {
    background: #0a1118;
    border-bottom: 1px solid #13202d;
}
QPushButton {
    background: #112032;
    color: #eef6ff;
    border: 1px solid #243d57;
    border-radius: 10px;
    padding: 7px 10px;
}
QPushButton:hover {
    background: #16304a;
    border: 1px solid #37698f;
}
QPushButton[nav='true'] {
    min-height: 34px;
    max-height: 34px;
    border-radius: 9px;
    font-size: 14px;
    padding: 0;
}
QPushButton[ghost='true'] {
    background: transparent;
    border: 1px solid transparent;
    color: #c9d7e6;
    border-radius: 8px;
    padding: 5px 7px;
}
QPushButton[ghost='true']:hover {
    background: #111b27;
    border: 1px solid #233648;
}
QPushButton[chip='true'] {
    background: #16111a;
    border: 1px solid #3f2a45;
    border-radius: 7px;
    padding: 2px 8px;
    font-size: 11px;
}
QPushButton[quick='true'] {
    background: transparent;
    border: none;
    color: #d9e5f0;
    border-radius: 8px;
    padding: 4px 8px;
    text-align: left;
}
QPushButton[quick='true']:hover {
    background: #101a26;
    border: 1px solid #1f3144;
}
QLineEdit {
    background: #14121a;
    color: #eef6ff;
    border: 1px solid #26263c;
    border-radius: 10px;
    padding: 8px 12px;
    selection-background-color: #4dd3ff;
}
QLineEdit:focus {
    border: 1px solid #4dd3ff;
    background: #181722;
}
QTabBar {
    background: transparent;
}
QTabBar::tab {
    background: #161018;
    color: #c9d0db;
    border: 1px solid #2a1f2d;
    padding: 6px 22px 6px 12px;
    min-width: 110px;
    max-width: 170px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    margin-right: 4px;
}
QTabBar::tab:selected {
    background: #17384c;
    color: #ffffff;
    border: 1px solid #53cfff;
}
QTabBar::close-button {
    subcontrol-position: right;
    width: 10px;
    height: 10px;
    margin-right: 5px;
}
QTabBar::close-button:hover {
    background: #71263a;
    border-radius: 6px;
}
QFrame#Card {
    background: #0f1a26;
    border: 1px solid #22384d;
    border-radius: 22px;
}
QLabel#HeroTitle {
    font-size: 30px;
    font-weight: 700;
    color: #ffffff;
}
QLabel#Muted {
    color: #9ab0c5;
}
QLabel#BrandMark {
    font-size: 15px;
    font-weight: 700;
    color: #6de3ff;
    padding: 0 4px;
}
QListWidget {
    background: #0f1a26;
    border: 1px solid #22384d;
    border-radius: 16px;
    padding: 8px;
}
QListWidget::item {
    padding: 10px;
    border-radius: 10px;
}
QListWidget::item:selected {
    background: #16304a;
}
"""
