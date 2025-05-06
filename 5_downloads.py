"""
Напишите приложение для загрузки файлов из интернета. В главном
окне должно быть три текстовых поля, в которые можно вводить
URL файла на закачку; под каждым из текстовых полей должны
быть индикаторы загрузки и рядом поля с процентом загрузки
каждого файла. Необходимо организовать возможность качать от
одного до трех файлов параллельно.
"""
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import requests
import time
import os
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from io import BytesIO
import re


class DownloaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("File Downloader")
        self.root.geometry("600x500")
        self.root.resizable(True, True)

        # Создаем переменные для хранения URL-адресов и активных потоков
        self.urls = []
        self.progress_bars = []
        self.progress_labels = []
        self.active_threads = []
        self.download_times = [0, 0, 0]
        self.file_sizes = [0, 0, 0]
        self.file_names = ["", "", ""]
        self.focused_entry = None  # Для отслеживания текущего активного поля

        # Создаем и размещаем элементы интерфейса
        self.create_widgets()

        # Привязываем обработчик Ctrl+V
        self.root.bind('<Control-v>', self.paste_from_clipboard)

    def create_widgets(self):
        # Главный фрейм
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Заголовок
        header_label = ttk.Label(main_frame, text="Enter URLs to download:", font=("Arial", 12, "bold"))
        header_label.pack(pady=10)

        # Контейнер для полей ввода и индикаторов
        url_frame = ttk.Frame(main_frame)
        url_frame.pack(fill=tk.BOTH, expand=True)

        # Создаем три поля для URL, индикаторы прогресса и метки
        for i in range(3):
            # Фрейм для группировки элементов
            entry_frame = ttk.Frame(url_frame)
            entry_frame.pack(fill=tk.X, pady=5)

            # Поле ввода URL
            url_entry = ttk.Entry(entry_frame, width=50)
            url_entry.pack(fill=tk.X, pady=2)
            # Привязываем обработчики фокуса к полю ввода
            url_entry.bind("<FocusIn>", lambda event, idx=i: self.on_entry_focus_in(event, idx))
            url_entry.bind("<FocusOut>", self.on_entry_focus_out)
            self.urls.append(url_entry)

            # Фрейм для прогресс-бара и метки процента
            progress_frame = ttk.Frame(entry_frame)
            progress_frame.pack(fill=tk.X, pady=2)

            # Индикатор прогресса
            progress_bar = ttk.Progressbar(progress_frame, orient=tk.HORIZONTAL, length=450, mode='determinate')
            progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True)
            self.progress_bars.append(progress_bar)

            # Метка для отображения процента
            progress_label = ttk.Label(progress_frame, text="0%")
            progress_label.pack(side=tk.RIGHT, padx=5)
            self.progress_labels.append(progress_label)

        # Кнопка для начала загрузки
        self.download_button = ttk.Button(main_frame, text="Start downloading!", command=self.start_download)
        self.download_button.pack(pady=15)

        # Устанавливаем фокус на первое поле ввода по умолчанию
        self.urls[0].focus_set()
        self.focused_entry = 0

    def on_entry_focus_in(self, event, idx):
        """Обработчик события получения фокуса полем ввода"""
        self.focused_entry = idx

    def on_entry_focus_out(self, event):
        """Обработчик события потери фокуса полем ввода"""
        self.focused_entry = None

    def paste_from_clipboard(self, event):
        """Обработчик для вставки из буфера обмена по Ctrl+V"""
        try:
            # Если есть активное поле ввода
            if self.focused_entry is not None:
                # Получаем текст из буфера обмена
                clipboard_text = self.root.clipboard_get()
                # Вставляем в текущее поле
                self.urls[self.focused_entry].delete(0, tk.END)
                self.urls[self.focused_entry].insert(0, clipboard_text)
                return "break"  # Предотвращаем стандартную обработку Ctrl+V
            return None
        except Exception as e:
            # Игнорируем ошибки буфера обмена
            return None

    def start_download(self):
        # Сбрасываем прогресс и останавливаем активные потоки
        self.stop_active_threads()

        # Сбрасываем информацию о предыдущих загрузках
        self.download_times = [0, 0, 0]
        self.file_sizes = [0, 0, 0]
        self.file_names = ["", "", ""]

        # Проверяем введенные URL
        urls_to_download = []
        for i, url_entry in enumerate(self.urls):
            url = url_entry.get().strip()
            if url:
                urls_to_download.append((i, url))
                # Сбрасываем прогресс
                self.progress_bars[i]['value'] = 0
                self.progress_labels[i]['text'] = "0%"

        if not urls_to_download:
            messagebox.showwarning("Предупреждение", "Пожалуйста, введите хотя бы один URL для загрузки.")
            return

        # Запускаем загрузку в отдельных потоках
        for idx, url in urls_to_download:
            thread = threading.Thread(target=self.download_file, args=(idx, url))
            thread.daemon = True
            thread.start()
            self.active_threads.append(thread)

    def download_file(self, idx, url):
        try:
            start_time = time.time()

            # Отправляем HEAD-запрос для получения размера файла
            response = requests.head(url)
            total_size = int(response.headers.get('content-length', 0))

            # Получаем имя файла из URL
            if 'content-disposition' in response.headers:
                cd = response.headers['content-disposition']
                filename = re.findall('filename="(.+)"', cd) or re.findall('filename=(.+)', cd)
                if filename:
                    filename = filename[0]
                else:
                    filename = os.path.basename(url)
            else:
                filename = os.path.basename(url)

            # Если имя пустое, используем часть URL
            if not filename:
                filename = f"file_{idx + 1}"

            self.file_names[idx] = filename

            # Создаем объект BytesIO для хранения загружаемых данных
            file_data = BytesIO()

            # Инициируем загрузку по частям
            response = requests.get(url, stream=True)
            downloaded_size = 0

            for chunk in response.iter_content(chunk_size=4096):
                if chunk:
                    file_data.write(chunk)
                    downloaded_size += len(chunk)

                    # Обновляем прогресс
                    if total_size > 0:
                        progress = (downloaded_size / total_size) * 100
                        # Обновляем интерфейс из основного потока
                        self.root.after(0, lambda prog=progress, i=idx: self.update_progress(i, prog))

            # Сохраняем файл
            with open(filename, 'wb') as f:
                f.write(file_data.getvalue())

            # Завершение загрузки
            end_time = time.time()
            download_time = end_time - start_time
            self.download_times[idx] = download_time
            self.file_sizes[idx] = downloaded_size

            # Обновляем прогресс до 100%
            self.root.after(0, lambda i=idx: self.update_progress(i, 100))

            # Проверяем, все ли загрузки завершены
            self.root.after(100, self.check_all_downloads_completed)

        except Exception as e:
            self.root.after(0, lambda err=str(e), i=idx: self.show_error(i, err))

    def update_progress(self, idx, progress):
        self.progress_bars[idx]['value'] = progress
        self.progress_labels[idx]['text'] = f"{int(progress)}%"

    def show_error(self, idx, error_message):
        self.progress_labels[idx]['text'] = "Error"
        messagebox.showerror("Ошибка загрузки", f"Не удалось загрузить файл #{idx + 1}: {error_message}")

    def check_all_downloads_completed(self):
        all_completed = True
        for i, url_entry in enumerate(self.urls):
            if url_entry.get().strip() and self.progress_bars[i]['value'] < 100:
                all_completed = False
                break

        if all_completed and any(self.download_times):
            self.show_results()

    def show_results(self):
        # Создаем всплывающее окно с графиком
        results_window = tk.Toplevel(self.root)
        results_window.title("Download Results")
        results_window.geometry("600x500")

        # Создаем метки для отображения времени загрузки и размеров файлов
        info_frame = ttk.Frame(results_window, padding=10)
        info_frame.pack(fill=tk.X)

        # Добавляем заголовок
        ttk.Label(info_frame, text="Download Results", font=("Arial", 12, "bold")).pack(pady=5)

        # Выводим информацию о загрузке для каждого файла
        for i in range(3):
            if self.download_times[i] > 0:
                time_str = self.format_time(self.download_times[i])
                size_str = self.format_size(self.file_sizes[i])
                file_name = self.file_names[i]
                info_text = f"File: {file_name} | Size: {size_str} | Time: {time_str}"
                ttk.Label(info_frame, text=info_text).pack(anchor='w', pady=2)

        # Создаем график
        fig = plt.Figure(figsize=(8, 6), dpi=100)
        ax = fig.add_subplot(111)

        # Подготавливаем данные для графика
        labels = []
        times = []
        sizes = []

        for i in range(3):
            if self.download_times[i] > 0:
                labels.append(f"File {i + 1}")
                times.append(self.download_times[i])
                sizes.append(self.file_sizes[i])

        # Рисуем столбчатую диаграмму
        bars = ax.bar(labels, times, color='skyblue')

        # Добавляем метки с временем и размером
        for i, bar in enumerate(bars):
            time_str = self.format_time(times[i])
            size_str = self.format_size(sizes[i])
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.1,
                    f"{time_str}\n{size_str}",
                    ha='center', va='bottom', fontsize=9)

        ax.set_ylabel('Download Time (seconds)')
        ax.set_title('File Download Statistics')

        # Добавляем график на форму
        canvas = FigureCanvasTkAgg(fig, master=results_window)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def format_time(self, seconds):
        """Форматирует время в формате '2s 322ms'"""
        s = int(seconds)
        ms = int((seconds - s) * 1000)
        return f"{s}s {ms}ms"

    def format_size(self, size_bytes):
        """Форматирует размер файла в читаемый вид"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"

    def stop_active_threads(self):
        # Очищаем список активных потоков
        self.active_threads.clear()


def main():
    root = tk.Tk()
    app = DownloaderApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()