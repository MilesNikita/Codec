import sys
import os
import wave
import pyaudio
import threading
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QFileDialog

class AudioRecorderApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.audio = pyaudio.PyAudio()
        self.stream = None
        self.frames = []

        self.file_path = ""

        self.init_ui()

    def init_ui(self):

        start_button = QPushButton('Начать запись', self)
        start_button.clicked.connect(self.start_recording)
        start_button.setGeometry(50, 50, 150, 30)


        stop_button = QPushButton('Остановить запись', self)
        stop_button.clicked.connect(self.stop_recording)
        stop_button.setGeometry(50, 100, 150, 30)

        self.setGeometry(300, 300, 300, 200)
        self.setWindowTitle('Запись аудио')
        self.show()

    def start_recording(self):

        file_dialog = QFileDialog()
        self.file_path, _ = file_dialog.getSaveFileName(self, 'Выберите место сохранения', '', 'Audio files (*.wav)')

        if self.file_path:

            self.stream = self.audio.open(format=pyaudio.paInt16,
                                          channels=1,
                                          rate=44100,
                                          input=True,
                                          frames_per_buffer=1024)

            print("Запись начата...")

            threading.Thread(target=self.record_audio).start()

    def record_audio(self):
        while self.stream.is_active():
            data = self.stream.read(1024)
            self.frames.append(data)

    def stop_recording(self):
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()

            wf = wave.open(self.file_path, 'wb')
            wf.setnchannels(1)
            wf.setsampwidth(self.audio.get_sample_size(pyaudio.paInt16))
            wf.setframerate(44100)
            wf.writeframes(b''.join(self.frames))
            wf.close()

            print(f"Аудиофайл сохранен по пути: {self.file_path}")


    def closeEvent(self, event):
        if self.stream and self.stream.is_active():
            self.stop_recording()
        event.accept()

def main():
    app = QApplication(sys.argv)
    ex = AudioRecorderApp()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
