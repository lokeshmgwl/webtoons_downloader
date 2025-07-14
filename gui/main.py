import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton
from PyQt6.QtGui import QPixmap, QPalette, QBrush
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from gui.widgets import (SearchBar, ResultsDisplay, ChapterSelector,
                         OptionsPanel, StatusPanel)
from core.scraper import search_manga, scrape_episodes, scrape_chapter_images
from core.downloader import download_chapter
from core.converter import convert_to_pdf, convert_to_cbz
from core.cleaner import clean_chapter_images

class SearchThread(QThread):
    results_ready = pyqtSignal(list)

    def __init__(self, query):
        super().__init__()
        self.query = query

    def run(self):
        results = search_manga(self.query)
        self.results_ready.emit(results)

class DownloadThread(QThread):
    progress = pyqtSignal(int, str)
    finished = pyqtSignal()

    def __init__(self, manga_title, episodes, selected_format, clean_up):
        super().__init__()
        self.manga_title = manga_title
        self.episodes = episodes
        self.selected_format = selected_format
        self.clean_up = clean_up

    def run(self):
        total_episodes = len(self.episodes)
        for i, episode in enumerate(self.episodes):
            self.progress.emit(int((i / total_episodes) * 100), f"Downloading Episode {episode['number']}")
            image_urls = scrape_chapter_images(episode['url'])
            chapter_dir = download_chapter(self.manga_title, episode['number'], image_urls)
            
            if self.selected_format == "PDF":
                self.progress.emit(int(((i + 0.5) / total_episodes) * 100), f"Converting Episode {episode['number']} to PDF")
                output_path = f"{chapter_dir}.pdf"
                convert_to_pdf(chapter_dir, output_path)
            elif self.selected_format == "CBZ":
                self.progress.emit(int(((i + 0.5) / total_episodes) * 100), f"Converting Episode {episode['number']} to CBZ")
                output_path = f"{chapter_dir}.cbz"
                convert_to_cbz(chapter_dir, output_path)

            if self.clean_up:
                self.progress.emit(int(((i + 0.9) / total_episodes) * 100), f"Cleaning up images for Episode {episode['number']}")
                clean_chapter_images(chapter_dir)
        
        self.progress.emit(100, "Download complete!")
        self.finished.emit()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Webtoons Downloader")
        self.setGeometry(100, 100, 1280, 720)
        self.set_background()
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        self.layout = QVBoxLayout(central_widget)
        self.init_ui()

    def set_background(self):
        pixmap = QPixmap('gui/GUI.jpg')
        if pixmap.isNull():
            print("Failed to load background image.")
            return
        
        palette = self.palette()
        brush = QBrush(pixmap.scaled(self.size(), Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.SmoothTransformation))
        palette.setBrush(QPalette.ColorRole.Window, brush)
        self.setPalette(palette)

    def init_ui(self):
        # This is where we will add the rest of the UI components
        title = QLabel("Webtoons Downloader")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.search_bar = SearchBar()
        self.results_display = ResultsDisplay()
        self.chapter_selector = ChapterSelector()
        self.options_panel = OptionsPanel()
        self.status_panel = StatusPanel()
        
        self.layout.addWidget(title)
        self.layout.addWidget(self.search_bar)
        self.layout.addWidget(self.results_display)
        self.layout.addWidget(self.chapter_selector)
        self.layout.addWidget(self.options_panel)
        self.layout.addWidget(self.status_panel)

        self.search_bar.search_button.clicked.connect(self.perform_search)
        self.results_display.itemClicked.connect(self.on_manga_selected)
        # We need a download button
        self.download_button = QPushButton("Download")
        self.layout.addWidget(self.download_button)
        self.download_button.clicked.connect(self.perform_download)
        self.selected_manga_url = None

    def perform_search(self):
        query = self.search_bar.search_input.text()
        if query:
            self.search_thread = SearchThread(query)
            self.search_thread.results_ready.connect(self.display_search_results)
            self.search_thread.start()

    def display_search_results(self, results):
        self.results_display.clear()
        self.manga_results = results
        for i, result in enumerate(results):
            cover_url = result.get('cover_url', '')
            self.results_display.add_manga_item(result['title'], cover_url)
            # Store index to retrieve full result later
            self.results_display.item(i).setData(Qt.ItemDataRole.UserRole, i)

    def on_manga_selected(self, item):
        selected_index = item.data(Qt.ItemDataRole.UserRole)
        self.selected_manga_url = self.manga_results[selected_index]['url']
        self.selected_manga_title = self.manga_results[selected_index]['title']

    def perform_download(self):
        if not self.selected_manga_url:
            self.status_panel.log_display.append("Please select a manga first.")
            return

        episodes = scrape_episodes(self.selected_manga_url)
        
        # Logic to select episodes based on user input
        selected_episodes = self.get_selected_episodes(episodes)
        if not selected_episodes:
            self.status_panel.log_display.append("No valid episodes selected.")
            return
        
        selected_format = self.options_panel.format_selector.currentText()
        clean_up = self.options_panel.cleanup_checkbox.isChecked()

        self.download_thread = DownloadThread(self.selected_manga_title, selected_episodes, selected_format, clean_up)
        self.download_thread.progress.connect(self.update_progress)
        self.download_thread.finished.connect(self.on_download_finished)
        self.download_thread.start()

    def update_progress(self, value, message):
        self.status_panel.progress_bar.setValue(value)
        self.status_panel.log_display.append(message)

    def on_download_finished(self):
        self.status_panel.log_display.append("All tasks complete.")

    def get_selected_episodes(self, all_episodes):
        if self.chapter_selector.all_button.isChecked():
            return all_episodes

        single = self.chapter_selector.single_input.text()
        if single:
            try:
                episode_num = int(single)
                return [ep for ep in all_episodes if ep['number'] == episode_num]
            except ValueError:
                pass

        range_text = self.chapter_selector.range_input.text()
        if range_text:
            try:
                start, end = map(int, range_text.split('-'))
                return [ep for ep in all_episodes if start <= ep['number'] <= end]
            except (ValueError, IndexError):
                pass
        
        return []

    def resizeEvent(self, event):
        self.set_background()
        super().resizeEvent(event)

def run_gui():
    app = QApplication(sys.argv)
    
    # Load and apply stylesheet
    try:
        with open('gui/style.qss', 'r') as f:
            style = f.read()
        app.setStyleSheet(style)
    except FileNotFoundError:
        print("Stylesheet not found.")

    main_win = MainWindow()
    main_win.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    run_gui()