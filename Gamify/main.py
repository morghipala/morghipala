import sys
import os
import json
import tempfile
import requests
from urllib.parse import unquote
import soundfile as sf
from PIL import Image
from PyQt6.QtWidgets import (QApplication, QWidget, QPushButton,
                           QFileDialog, QVBoxLayout, QLabel,
                           QMessageBox, QHBoxLayout)
from PyQt6.QtCore import QThread, pyqtSignal, Qt, QUrl
from PyQt6.QtGui import QDropEvent, QDragEnterEvent

def get_duration(filepath):
    """Calcola la durata di un file audio."""
    try:
        audio_info = sf.info(filepath)
        duration = audio_info.duration
        return duration
    except sf.SoundFileError:
        return None

def crop_and_resize_image(image):
    """Ritaglia e ridimensiona l'immagine a 500x500 mantenendo le proporzioni."""
    width, height = image.size
    # Determina il lato più corto
    min_side = min(width, height)
    
    # Calcola le coordinate per il ritaglio
    left = (width - min_side) // 2
    top = (height - min_side) // 2
    right = left + min_side
    bottom = top + min_side
    
    # Ritaglia l'immagine in un quadrato
    image = image.crop((left, top, right, bottom))
    # Ridimensiona a 500x500
    return image.resize((500, 500), Image.Resampling.LANCZOS)

class ImageDropArea(QLabel):
    def __init__(self):
        super().__init__()
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setText("Trascina un'immagine qui\no clicca per selezionare")
        self.setStyleSheet("""
            QLabel {
                border: 2px dashed #666;
                border-radius: 5px;
                padding: 20px;
                background: transparent;
                color: #333;
            }
            QLabel:hover {
                background: rgba(0, 0, 0, 0.05);
            }
        """)
        self.setMinimumSize(300, 300)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls() or event.mimeData().hasText():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls:
                url = urls[0]
                if url.isLocalFile():
                    self.parent().process_image(url.toLocalFile())
                else:
                    self.parent().process_web_image(url.toString())
        elif event.mimeData().hasText():
            # Gestisce il caso di URL di immagini trascinate dal web
            url = event.mimeData().text()
            if any(url.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']):
                self.parent().process_web_image(url)

    def mousePressEvent(self, event):
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Seleziona Immagine",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp *.gif *.webp)"
        )
        if file_name:
            self.parent().process_image(file_name)

class FileProcessor(QThread):
    finished = pyqtSignal(bool, str)
    progress = pyqtSignal(str)
    request_image = pyqtSignal(str)
    image_processed = pyqtSignal()

    def __init__(self, folder_path, output_path):
        super().__init__()
        self.folder_path = folder_path
        self.output_path = output_path
        self.current_track = None
        self.skip_all_images = False
        self.waiting_for_image = False

    def process_image(self, image_path, skip_current, skip_all):
        if skip_all:
            self.skip_all_images = True
        elif image_path and not skip_current:
            try:
                with Image.open(image_path) as img:
                    img = img.convert('RGB')
                    img = crop_and_resize_image(img)
                    output_path = os.path.join(self.output_path, f"{self.current_track}.jpg")
                    img.save(output_path, "JPEG", quality=90)
            except Exception as e:
                self.finished.emit(False, f"Errore nel processare l'immagine: {str(e)}")
                return

        self.waiting_for_image = False
        self.image_processed.emit()

    def run(self):
        self.progress.emit("Inizio elaborazione...")

        if not os.path.exists(self.output_path):
            os.makedirs(self.output_path)

        processed_tracks = set()

        for filename in os.listdir(self.folder_path):
            if filename.endswith(".wav") and not filename.startswith('.'):
                base_name = filename.split(' (')[0]
                
                if base_name in processed_tracks:
                    continue
                    
                processed_tracks.add(base_name)
                track_files = [f for f in os.listdir(self.folder_path) if f.startswith(base_name)]

                durations = {}
                full_track_path = None

                for track_file in track_files:
                    filepath = os.path.join(self.folder_path, track_file)
                    duration = get_duration(filepath)

                    if duration is None:
                        self.finished.emit(False, f"Errore: Impossibile leggere il file {track_file}.")
                        return

                    if "(beginning)" in track_file:
                        durations["beginning"] = round(duration, 3)
                    elif "(loop)" in track_file:
                        durations["loop"] = round(duration, 3)
                    elif "(end)" in track_file:
                        durations["end"] = round(duration, 3)
                    elif track_file.endswith(".wav") and "(" not in track_file:
                        full_track_path = filepath

                if not durations or not full_track_path:
                    continue

                # Gestione immagine
                if not self.skip_all_images:
                    self.current_track = base_name
                    self.waiting_for_image = True
                    self.request_image.emit(base_name)
                    
                    while self.waiting_for_image:
                        self.msleep(100)

                # Salva JSON e file audio
                json_filename = base_name + ".json"
                json_filepath = os.path.join(self.output_path, json_filename)
                with open(json_filepath, "w") as f:
                    json.dump(durations, f, indent=4)

                try:
                    output_full_track_path = os.path.join(self.output_path, os.path.basename(full_track_path))
                    sf.write(output_full_track_path, *sf.read(full_track_path))
                except Exception as e:
                    self.finished.emit(False, f"Errore nella copia: {str(e)}")
                    return

        self.finished.emit(True, "Elaborazione completata con successo!")

class App(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Elaborazione Audio")
        self.setup_ui()
        self.thread = None
        self.selected_folder = None
        self.current_track = None
        self.initial_size = None

    def setup_ui(self):
        # Layout principale
        self.main_layout = QVBoxLayout()
        
        # Layout iniziale
        self.initial_layout = QVBoxLayout()
        self.select_folder_button = QPushButton("Seleziona Cartella")
        self.select_folder_button.clicked.connect(self.select_folder)
        self.folder_label = QLabel("Nessuna cartella selezionata")
        self.process_button = QPushButton("Processa")
        self.process_button.setEnabled(False)
        self.process_button.clicked.connect(self.start_processing)
        self.status_label = QLabel("")
        
        self.initial_layout.addWidget(self.select_folder_button)
        self.initial_layout.addWidget(self.folder_label)
        self.initial_layout.addWidget(self.process_button)
        self.initial_layout.addWidget(self.status_label)
        
        # Layout per la selezione dell'immagine
        self.image_layout = QVBoxLayout()
        self.track_name_label = QLabel()
        self.track_name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.track_name_label.setStyleSheet("font-size: 14px; font-weight: bold; margin: 10px;")
        self.drop_area = ImageDropArea()
        
        button_layout = QHBoxLayout()
        self.skip_button = QPushButton("Salta")
        self.skip_all_button = QPushButton("Salta tutti")
        button_layout.addWidget(self.skip_button)
        button_layout.addWidget(self.skip_all_button)
        
        self.image_layout.addWidget(self.track_name_label)
        self.image_layout.addWidget(self.drop_area)
        self.image_layout.addLayout(button_layout)
        
        # Aggiungi il layout iniziale al main layout
        self.main_layout.addLayout(self.initial_layout)
        self.setLayout(self.main_layout)
        
        # Output path
        self.output_path = "./output"

    def switch_to_image_selection(self, track_name):
        # Salva la dimensione iniziale della finestra
        if not self.initial_size:
            self.initial_size = self.size()
        
        self.current_track = track_name
        # Aggiorna il titolo della finestra
        self.setWindowTitle(f"Seleziona immagine per: {track_name}")
        
        # Nascondi tutti i widget del layout iniziale
        for i in range(self.initial_layout.count()):
            widget = self.initial_layout.itemAt(i).widget()
            if widget:
                widget.hide()
        
        # Mostra e configura i widget per la selezione dell'immagine
        self.track_name_label.setText(f"Brano: {track_name}")
        self.track_name_label.show()
        self.drop_area.show()
        self.skip_button.show()
        self.skip_all_button.show()
        
        # Connetti i pulsanti
        self.skip_button.clicked.connect(lambda: self.finish_image_selection(None, False))
        self.skip_all_button.clicked.connect(lambda: self.finish_image_selection(None, True))
        
        # Aggiungi il layout dell'immagine se non è già presente
        if self.image_layout.parent() is None:
            self.main_layout.addLayout(self.image_layout)

    def switch_to_initial_view(self):
        if self.initial_size:
            self.resize(self.initial_size)
        
        self.setWindowTitle("Elaborazione Audio")
        
        # Mostra tutti i widget del layout iniziale
        for i in range(self.initial_layout.count()):
            widget = self.initial_layout.itemAt(i).widget()
            if widget:
                widget.show()
        
        # Nascondi i widget per la selezione dell'immagine
        self.track_name_label.hide()
        self.drop_area.hide()
        self.skip_button.hide()
        self.skip_all_button.hide()

    def process_web_image(self, url):
        try:
            # Decodifica l'URL se necessario
            url = unquote(url)
            print(f"URL decodificato: {url}")

            # Crea una directory temporanea se non esiste
            temp_dir = tempfile.gettempdir()

            # Genera un nome file temporaneo
            temp_filename = os.path.join(temp_dir, f"temp_image_{os.path.basename(url)}")

            # Aggiungi un User-Agent nella richiesta
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }

            # Scarica l'immagine
            response = requests.get(url, headers=headers)
            response.raise_for_status()  # Solleva un'eccezione se la risposta non è valida

            # Scrivi il contenuto nel file temporaneo
            with open(temp_filename, "wb") as file:
                file.write(response.content)

            # Processa l'immagine scaricata
            self.process_image(temp_filename)

            # Rimuovi il file temporaneo
            os.remove(temp_filename)

        except Exception as e:
            QMessageBox.critical(self, "Errore", f"Errore nel download dell'immagine: {str(e)}")

    def process_image(self, image_path):
        try:
            # Verifica che l'immagine possa essere aperta
            with Image.open(image_path) as img:
                pass
            
            # Chiedi conferma
            reply = QMessageBox.question(self, 'Conferma',
                                       'Vuoi utilizzare questa immagine?',
                                       QMessageBox.StandardButton.Yes |
                                       QMessageBox.StandardButton.No,
                                       QMessageBox.StandardButton.No)
            
            if reply == QMessageBox.StandardButton.Yes:
                self.finish_image_selection(image_path, False)
            
        except Exception as e:
            QMessageBox.critical(self, "Errore", f"Errore nel processare l'immagine: {str(e)}")

    def finish_image_selection(self, image_path, skip_all):
        if self.thread:
            self.thread.process_image(image_path, skip_all, skip_all)
        self.switch_to_initial_view()

    def select_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Seleziona Cartella")
        if folder_path:
            self.folder_label.setText(folder_path)
            self.selected_folder = folder_path
            self.process_button.setEnabled(True)

    def start_processing(self):
        if self.selected_folder:
            self.status_label.setText("Elaborazione in corso...")
            self.thread = FileProcessor(self.selected_folder, self.output_path)
            self.thread.finished.connect(self.processing_finished)
            self.thread.progress.connect(self.update_status)
            self.thread.request_image.connect(self.switch_to_image_selection)
            self.process_button.setEnabled(False)
            self.thread.start()
        else:
            QMessageBox.warning(self, "Attenzione", "Seleziona prima una cartella!")

    def update_status(self, message):
        self.status_label.setText(message)

    def processing_finished(self, success, message):
        self.status_label.setText(message)
        if success:
            QMessageBox.information(self, "Successo", message)
        else:
            QMessageBox.critical(self, "Errore", message)
        self.process_button.setEnabled(True)
        self.thread = None
        self.switch_to_initial_view()

    def closeEvent(self, event):
        if self.thread and self.thread.isRunning():
            reply = QMessageBox.question(
                self, 'Conferma',
                'Elaborazione in corso. Sei sicuro di voler uscire?',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.thread.quit()
                self.thread.wait()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = App()
    window.show()
    sys.exit(app.exec())