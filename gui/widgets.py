from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QLineEdit, QPushButton, 
                             QListWidget, QListWidgetItem, QLabel, QComboBox, QCheckBox, 
                             QProgressBar, QTextEdit)
from PyQt6.QtGui import QIcon, QPixmap
import requests

class SearchBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QHBoxLayout(self)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search for a webtoon...")
        
        self.search_button = QPushButton("Search")
        
        self.layout.addWidget(self.search_input)
        self.layout.addWidget(self.search_button)

class ResultsDisplay(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFlow(QListWidget.Flow.LeftToRight)
        self.setWrapping(True)
        self.setSpacing(10)

    def add_manga_item(self, title, cover_url):
        item = QListWidgetItem()
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        cover_label = QLabel()
        pixmap = QPixmap()
        
        try:
            headers = {
                'Referer': 'https://www.webtoons.com/',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
            }
            response = requests.get(cover_url, stream=True, headers=headers)
            response.raise_for_status()
            pixmap.loadFromData(response.content)
            cover_label.setPixmap(pixmap.scaledToWidth(150))
        except requests.exceptions.RequestException as e:
            print(f"Failed to load cover image: {e}")
            # Optionally set a placeholder image
            pixmap.load('gui/placeholder.png') # Make sure you have a placeholder image
            cover_label.setPixmap(pixmap.scaledToWidth(150))

        title_label = QLabel(title)
        title_label.setWordWrap(True)
        
        layout.addWidget(cover_label)
        layout.addWidget(title_label)
        
        item.setSizeHint(widget.sizeHint())
        self.addItem(item)
        self.setItemWidget(item, widget)

class ChapterSelector(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QHBoxLayout(self)
        
        self.all_button = QPushButton("All")
        self.all_button.setCheckable(True)
        self.single_input = QLineEdit()
        self.single_input.setPlaceholderText("e.g., 5")
        self.range_input = QLineEdit()
        self.range_input.setPlaceholderText("e.g., 1-10")
        
        self.layout.addWidget(QLabel("Chapters:"))
        self.layout.addWidget(self.all_button)
        self.layout.addWidget(QLabel("Single:"))
        self.layout.addWidget(self.single_input)
        self.layout.addWidget(QLabel("Range:"))
        self.layout.addWidget(self.range_input)

class OptionsPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QHBoxLayout(self)
        
        self.format_selector = QComboBox()
        self.format_selector.addItems(["PDF", "CBZ"])
        
        self.cleanup_checkbox = QCheckBox("Delete images after conversion")
        
        self.layout.addWidget(QLabel("Format:"))
        self.layout.addWidget(self.format_selector)
        self.layout.addWidget(self.cleanup_checkbox)

class StatusPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        
        self.progress_bar = QProgressBar()
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        
        self.layout.addWidget(self.progress_bar)
        self.layout.addWidget(self.log_display)