import sys
import numpy as np
import threading
import librosa
import pyaudio
import wave
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QHBoxLayout,
    QLabel, QSlider, QAction, QMenu, QMessageBox, QTabWidget
)
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from pydub import AudioSegment
from pydub.playback import play
import struct
import os

class LabeledSlider(QWidget):
    def __init__(self, orientation, min_val, max_val, default_val, title):
        super().__init__()
        layout = QVBoxLayout()
        self.slider = QSlider(orientation)
        self.slider.setMinimum(min_val)
        self.slider.setMaximum(max_val)
        self.slider.setValue(default_val)
        self.label_min = QLabel(str(min_val))
        self.label_max = QLabel(str(max_val))
        self.slider.valueChanged.connect(self.update_labels)
        slider_layout = QHBoxLayout()
        slider_layout.addWidget(self.label_min)
        slider_layout.addWidget(self.slider)
        slider_layout.addWidget(self.label_max)
        layout.addLayout(slider_layout)
        self.setLayout(layout)

    def update_labels(self):
        self.label_min.setText(str(self.slider.minimum()))
        self.label_max.setText(str(self.slider.maximum()))

    def value(self):
        return self.slider.value()

class DeltaCodecApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.audio = pyaudio.PyAudio()
        self.stream = None
        self.frames = []
        self.decodeded_signal = []
        self.file_path = ""
        self.initUI()
        self.create_menu()

    def initUI(self):
        self.setWindowTitle('Дельта-кодек речевого сигнала для аудиосигнала с микрофона')
        self.setGeometry(100, 100, 800, 600)
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        self.main_tab = QWidget()
        self.extra_tab = QWidget()
        self.tabs.addTab(self.main_tab, 'Теория дельта кодирования')
        self.tabs.addTab(self.extra_tab, 'Программа')
        self.setup_main_tab()
        self.setup_extra_tab()

    def setup_main_tab(self):
        layout = QVBoxLayout()
        theory_label = QLabel('Теория дельта кодирования:')
        layout.addWidget(theory_label)
        theory_text = QLabel('Дельта-кодирование - это метод сжатия данных, который заключается в хранении разницы между последовательными сигналами, а не самих сигналов.\n\n'
                             'Этот метод основан на предположении, что соседние значения сигнала имеют небольшие изменения. При дельта-кодировании сохраняется разница между каждым соседним значением.\n\n'
                             'Это особенно полезно для аудио-сигналов, где изменения часто невелики и последовательные сэмплы часто похожи.')
        layout.addWidget(theory_text)
        image_layout = QHBoxLayout()
        pixmap1 = QPixmap("image1.png")
        label1 = QLabel()
        label1.setPixmap(pixmap1)
        image_layout.addWidget(label1)
        pixmap2 = QPixmap("image2.png")
        label2 = QLabel()
        label2.setPixmap(pixmap2)
        image_layout.addWidget(label2)
        layout.addLayout(image_layout)
        self.main_tab.setLayout(layout)

    def setup_extra_tab(self):
        layout = QVBoxLayout()
        self.original_label = QLabel('Оригинальный сигнал:')
        layout.addWidget(self.original_label)
        self.process_button = QPushButton('Обработать')
        self.process_button.clicked.connect(self.process_signal)
        layout.addWidget(self.process_button)
        self.play_sound = QPushButton('Проиграть')
        self.play_sound.clicked.connect(self.play_sound_thread)
        layout.addWidget(self.play_sound)
        horizontal_layout_widget = QWidget(self)
        horizontal_layout_widget.setGeometry(60, 110, 251, 81)
        horizontal_layout = QHBoxLayout(horizontal_layout_widget)
        horizontal_layout.setContentsMargins(0, 0, 0, 0)
        self.pushButton_1 = QPushButton('Начать запись')
        self.pushButton_1.clicked.connect(self.start_recording)
        horizontal_layout.addWidget(self.pushButton_1)
        self.pushButton_2 = QPushButton('Остановить запись')
        self.pushButton_2.clicked.connect(self.stop_recording)
        horizontal_layout.addWidget(self.pushButton_2)
        layout.addWidget(horizontal_layout_widget)
        self.error_slider = LabeledSlider(Qt.Horizontal, 0, 100, 0, 'Уровень ошибок')
        layout.addWidget(self.error_slider)
        self.error_label = QLabel('Уровень ошибок: 0%')
        layout.addWidget(self.error_label)
        self.result_label = QLabel('')
        layout.addWidget(self.result_label)
        self.original_figure = Figure(figsize=(8, 4))
        self.original_canvas = FigureCanvas(self.original_figure)
        layout.addWidget(self.original_canvas)
        self.original_nav_toolbar = NavigationToolbar2QT(self.original_canvas, self)
        layout.addWidget(self.original_nav_toolbar)
        self.encoded_figure = Figure(figsize=(5, 4))
        self.encoded_canvas = FigureCanvas(self.encoded_figure)
        layout.addWidget(self.encoded_canvas)
        self.encoded_nav_toolbar = NavigationToolbar2QT(self.encoded_canvas, self)
        layout.addWidget(self.encoded_nav_toolbar)
        self.decoded_figure = Figure(figsize=(8, 4))
        self.decoded_canvas = FigureCanvas(self.decoded_figure)
        layout.addWidget(self.decoded_canvas)
        self.decoded_nav_toolbar = NavigationToolbar2QT(self.decoded_canvas, self)
        layout.addWidget(self.decoded_nav_toolbar)
        self.extra_tab.setLayout(layout)

    def create_menu(self):
        menubar = self.menuBar()
        info_menu = menubar.addMenu('Информация')
        about_action = QAction('О программе', self)
        harakter_action = QAction('Системные требования', self)
        about_action.triggered.connect(self.show_about_dialog)
        harakter_action.triggered.connect(self.show_harakter_dialog)
        info_menu.addAction(about_action)
        info_menu.addAction(harakter_action)

    def show_about_dialog(self):
        QMessageBox.about(self, 'О программе', 'Дельта-кодек речевого сигнала для демонстрации принципа работы для аудио записанного с микрофона.')
    
    def show_harakter_dialog(self):
        QMessageBox.about(self, 'Системные требования', 'Для функцияонирования программы необходимо иметь....')

    def set_zoom_factor(self, zoom_factor):
        for nav_toolbar, canvas in [
            (self.original_nav_toolbar, self.original_canvas),
            (self.encoded_nav_toolbar, self.encoded_canvas),
            (self.decoded_nav_toolbar, self.decoded_canvas),
        ]:
            nav_toolbar.set_xscale(1.0 / zoom_factor)
            nav_toolbar.set_yscale(1.0 / zoom_factor)
            canvas.draw()

    def toggle_zoom(self):
        if self.zoom_button.isChecked():
            self.original_nav_toolbar.pan()
            self.encoded_nav_toolbar.pan()
            self.decoded_nav_toolbar.pan()
        else:
            self.original_nav_toolbar.zoom()
            self.encoded_nav_toolbar.zoom()
            self.decoded_nav_toolbar.zoom()
            self.sync_axes_zoom()

    def sync_axes_zoom(self):
        self.zoom_factor = self.original_nav_toolbar.get_zoom_factor()
        self.set_zoom_factor(self.zoom_factor)

    def plot_signal(self, figure, canvas, signal, color, title):
        time = np.linspace(-1, 1, len(signal))
        figure.clear()
        ax = figure.add_subplot(111)
        ax.plot(time, signal, label=title, color=color)
        ax.set_title(title)
        ax.set_xlabel('Время (сек)')
        ax.set_ylabel('Напряжение (В)')
        ax.set_xlim(-1, 1)
        ax.legend()
        ax.grid(True)
        ax.set_aspect('auto')
        ax.tick_params(axis='both', which='major', labelsize=8)
        ax.tick_params(axis='both', which='minor', labelsize=6)
        figure.tight_layout()
        canvas.draw()

    def plot_signal_code(self, figure, canvas, signal, color, title):
        ax = figure.gca()
        ax.clear()
        binary_signal = [1 if signal[i] > signal[i - 1] else 0 for i in range(1, len(signal))]
        binary_signal = [0] + binary_signal
        ax.step(range(len(binary_signal)), binary_signal, color=color, label=title)
        ax.set_title(title)
        ax.set_xlabel('Время (сек)')
        ax.set_ylabel('Напряжение (В)')
        ax.legend()
        ax.grid(True)
        ax.tick_params(axis='both', which='major', labelsize=8)
        ax.tick_params(axis='both', which='minor', labelsize=6)
        figure.tight_layout()
        canvas.draw()

    def update_error_level(self):
        self.error_level = self.error_slider.value()
        self.error_label.setText(f'Количество ошибок: {self.error_level}%')

    def add_errors(self, signal):
        num_samples = len(signal)
        num_errors = int(num_samples * self.error_level / 100)
        error_indices = np.random.choice(num_samples, num_errors, replace=False)
        signal_with_errors = np.copy(signal)
        signal_with_errors[error_indices] = np.random.uniform(-1, 1, num_errors)
        return signal_with_errors

    def process_signal(self):
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(self, 'Выберите аудиофайл', '', 'Audio files (*.mp3 *.wav)')
        if file_path:
            audio, sample_rate = librosa.load(file_path, sr=None)
            self.original_signal = audio[:48000 * 2]  # Пример ограничения длительности до 2 секунд
            self.update_error_level()
            self.encoded_signal = self.delta_encode(self.original_signal)
            self.original_signal = self.add_errors(self.original_signal) 
            decoded_signal = self.delta_decode(self.encoded_signal)
            self.decodeded_signal = decoded_signal
            error_bits_per_second = self.calculate_error_bits_per_second(self.original_signal, decoded_signal)
            mse_error = self.calculate_mse_error(self.original_signal, decoded_signal)
            self.plot_signal(self.original_figure, self.original_canvas, self.original_signal, 'r', 'Оригинальный сигнал')
            self.plot_signal_code(self.encoded_figure, self.encoded_canvas, self.encoded_signal, 'b', 'Закодированный сигнал')
            self.plot_signal(self.decoded_figure, self.decoded_canvas, decoded_signal, 'g', 'Декодированный сигнал')
            self.result_label.setText(f'Количество ошибок за секунду: {error_bits_per_second:.4f} \nСредне квадратичная ошибка: {mse_error:.4f}')

    def calculate_error_bits_per_second(self, original_signal, decoded_signal):
        error_bits = np.sum(original_signal != decoded_signal)
        duration_seconds = len(original_signal) / 48000
        bits_per_second = error_bits / duration_seconds
        return int(bits_per_second)

    def calculate_mse_error(self, original_signal, decoded_signal):
        mse_error = np.mean((original_signal - decoded_signal) ** 2)
        return mse_error

    def delta_encode(self, signal):
        delta_signal = [signal[0]]  
        for i in range(1, len(signal)):
            delta = signal[i] - signal[i - 1]
            delta_signal.append(delta)
        return delta_signal

    def delta_decode(self, delta_signal):
        decode_signal = [delta_signal[0]]  
        for i in range(1, len(delta_signal)):
            value = decode_signal[i - 1] + delta_signal[i]
            decode_signal.append(value)
        return decode_signal

    def delta_decode_binary(self, delta_signal):
        signal = [delta_signal[0]]
        for i in range(1, len(delta_signal)):
            value = signal[i - 1] + delta_signal[i]
            signal.append(value)
        return signal

    def start_recording(self):
        file_dialog = QFileDialog()
        self.file_path, _ = file_dialog.getSaveFileName(self, 'Выберите место сохранения', '', 'Audio files (*.mp3)')
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
        
    def plays_sound(self):
        try:
            if self.decodeded_signal:
                audio_bytes = b''.join(struct.pack('<h', int(sample * 32767)) for sample in self.decodeded_signal)
                sample_width = 2  # фиксированный sample_width
                frame_rate = 44100  # фиксированный frame_rate
                channels = 1  # фиксированное количество каналов
                with wave.open('temp_audio.wav', 'wb') as wf:
                    wf.setnchannels(channels)
                    wf.setsampwidth(sample_width)
                    wf.setframerate(frame_rate)
                    wf.writeframes(audio_bytes)
                decoded_audio = AudioSegment.from_wav('temp_audio.wav')
                play(decoded_audio)
                os.remove('temp_audio.wav')
            else:
                QMessageBox.warning(self, 'Ошибка', 'Декодированный сигнал не найден')
        except Exception as e:
            print(str(e))

    def play_sound_thread(self):
        threading.Thread(target=self.plays_sound).start()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = DeltaCodecApp()
    window.show()
    sys.exit(app.exec_())
