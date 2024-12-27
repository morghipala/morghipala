import sys
import os
import json
import soundfile as sf
from PyQt6.QtWidgets import (QApplication, QWidget, QPushButton,
                             QFileDialog, QVBoxLayout, QLabel,
                             QMessageBox)
from PyQt6.QtCore import QThread, pyqtSignal

def get_duration(filepath):
    """Calcola la durata di un file audio."""
    try:
        audio_info = sf.info(filepath)
        duration = audio_info.duration
        return duration
    except sf.SoundFileError:
        return None

class FileProcessor(QThread):
    finished = pyqtSignal(bool, str)
    progress = pyqtSignal(str)

    def __init__(self, folder_path, output_path):
        super().__init__()
        self.folder_path = folder_path
        self.output_path = output_path

    def run(self):
        self.progress.emit("Inizio elaborazione...")

        # Crea la directory di output se non esiste
        if not os.path.exists(self.output_path):
            os.makedirs(self.output_path)

        for filename in os.listdir(self.folder_path):
            if filename.endswith(".wav") and not filename.startswith('.'):
                base_name = filename.split(' (')[0]  # Nome del brano base
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

                if not durations:
                    self.progress.emit(f"Nessun segmento trovato per {base_name}, ignorato.")
                    continue

                if not full_track_path:
                    self.progress.emit(f"Nessun file principale trovato per {base_name}, ignorato.")
                    continue

                # Salva il file JSON
                json_filename = base_name + ".json"
                json_filepath = os.path.join(self.output_path, json_filename)
                with open(json_filepath, "w") as f:
                    json.dump(durations, f, indent=4)

                # Copia il file completo
                self.progress.emit(f"Copia del brano {base_name}...")
                try:
                    output_full_track_path = os.path.join(self.output_path, os.path.basename(full_track_path))
                    sf.write(output_full_track_path, *sf.read(full_track_path))
                except Exception as e:
                    self.finished.emit(False, f"Errore nella copia: {str(e)}")

        self.finished.emit(True, "Elaborazione completata con successo!")


class App(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Elaborazione Audio")

        self.select_folder_button = QPushButton("Seleziona Cartella")
        self.select_folder_button.clicked.connect(self.select_folder)
        self.folder_label = QLabel("Nessuna cartella selezionata")
        self.output_path = "./output"
        self.process_button = QPushButton("Processa")
        self.process_button.setEnabled(False)
        self.process_button.clicked.connect(self.start_processing)
        self.status_label = QLabel("")

        layout = QVBoxLayout()
        layout.addWidget(self.select_folder_button)
        layout.addWidget(self.folder_label)
        layout.addWidget(self.process_button)
        layout.addWidget(self.status_label)
        self.setLayout(layout)
        self.thread = None
        self.selected_folder = None

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
            self.thread.start()
            self.process_button.setEnabled(False)
        else:
            QMessageBox.warning(None, "Attenzione", "Seleziona prima una cartella!")

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


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = App()
    window.show()
    sys.exit(app.exec())
