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
        durations = {}
        full_track_path = None
        base_filename = None

        for filename in os.listdir(self.folder_path):
            if filename.endswith(".wav"):
                filepath = os.path.join(self.folder_path, filename)
                duration = get_duration(filepath)

                if duration is None:
                    self.finished.emit(False, f"Errore: Impossibile leggere il file {filename}.")
                    return

                if "(beginning)" in filename:
                    durations["beginning"] = round(duration, 3)
                elif "(loop)" in filename:
                    durations["loop"] = round(duration, 3)
                elif "(end)" in filename:
                    durations["end"] = round(duration, 3)
                elif filename.endswith(".wav") and "(beginning)" not in filename and "(loop)" not in filename and "(end)" not in filename:
                    full_track_path = filepath
                    base_filename = os.path.splitext(filename)[0]

        if not durations:
            self.finished.emit(False, "Nessun file con (beginning), (loop) o (end) trovato.")
            return

        if full_track_path is None or base_filename is None:
            self.finished.emit(False, "Nessun file con il nome completo del brano trovato.")
            return

        json_filename = base_filename + ".json"
        json_filepath = os.path.join(self.output_path, json_filename)
        with open(json_filepath, "w") as f:
            json.dump(durations, f, indent=4)

        self.progress.emit("Copia del brano...")
        try:
            output_full_track_path = os.path.join(self.output_path, os.path.basename(full_track_path))
            sf.write(output_full_track_path, *sf.read(full_track_path))
            self.finished.emit(True, "File JSON e copia del brano creati con successo!")
        except Exception as e:
            self.finished.emit(False, f"Errore nella copia: {str(e)}")


class App(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Elaborazione Audio")

        self.select_folder_button = QPushButton("Seleziona Cartella")
        self.select_folder_button.clicked.connect(self.select_folder)
        self.folder_label = QLabel("Nessuna cartella selezionata")
        self.output_path = "."
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
            self.selected_folder = folder_path #salvo il path della cartella
            self.process_button.setEnabled(True)

    def start_processing(self):
        if self.selected_folder: #controllo che sia stata selezionata una cartella
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