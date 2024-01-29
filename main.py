import sys
import numpy as np
import pyaudio
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QHBoxLayout,
    QLabel, QComboBox, QSlider, QAction, QMenu, QMessageBox, QTabWidget
)
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from pydub import AudioSegment

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
        self.load_button = QPushButton('Загрузить звук')
        self.load_button.clicked.connect(self.load_sound)
        layout.addWidget(self.load_button)
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
    
    def load_sound(self):
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(self, 'Выберите аудиофайл', '', 'Audio files (*.mp3 *.wav *.ogg)')

        if file_path:
            try:
                audio = AudioSegment.from_file(file_path)
                print("Аудиофайл успешно загружен.")
                # Теперь у вас есть переменная 'audio', содержащая аудиоданные
            except Exception as e:
                print(f"Ошибка при загрузке аудио: {e}")

    def process_signal(self):
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(self, 'Выберите аудиофайл', '', 'Audio files (*.mp3 *.wav *.ogg)')

        if file_path:
            try:
                audio = AudioSegment.from_file(file_path)
                frames = []

                for _ in range(int(44100 * 2 / 1024)):
                    data = audio.read(1024)
                    frames.append(data)

                convert_audio = np.frombuffer(b''.join(frames), dtype=np.int16)
                print("Аудиофайл успешно загружен.")
                # Теперь у вас есть переменная 'audio', содержащая аудиоданные
            except Exception as e:
                print(f"Ошибка при загрузке аудио: {e}")
        self.original_signal = audio[:48000 * 2]
        self.update_error_level()
        self.encoded_signal = self.delta_encode(self.original_signal)
        self.original_signal = self.add_errors(self.original_signal) 
        decoded_signal = self.delta_decode(self.encoded_signal)
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
        signal = [delta_signal[0]]  
        for i in range(1, len(delta_signal)):
            value = signal[i - 1] + delta_signal[i]
            signal.append(value)
        return signal

    def delta_decode_binary(self, delta_signal):
        signal = [delta_signal[0]]
        for i in range(1, len(delta_signal)):
            value = signal[i - 1] + delta_signal[i]
            signal.append(value)
        return signal

    def record_audio(self):
        audio = pyaudio.PyAudio()
        stream = audio.open(format=pyaudio.paInt16, channels=1, rate=44100, input=True, frames_per_buffer=1024)
        frames = []

        for _ in range(int(44100 * 2 / 1024)):
            data = stream.read(1024)
            frames.append(data)

        stream.stop_stream()
        stream.close()
        audio.terminate()

        return np.frombuffer(b''.join(frames), dtype=np.int16)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = DeltaCodecApp()
    window.show()
    sys.exit(app.exec_())
