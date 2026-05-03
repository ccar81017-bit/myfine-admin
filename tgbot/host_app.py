import sys
import asyncio
import threading
import logging
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QTextEdit, QPushButton, QTableWidget, 
                             QTableWidgetItem, QTabWidget, QLabel)
from PyQt6.QtCore import pyqtSignal, QObject, Qt
from PyQt6.QtGui import QFont, QColor

# Импортируем объекты из твоего файла (убедись, что файл называется tgbot.py)
from tgbot import dp, bot, USERS_DB

# Настройка логирования для перехвата в консоль приложения
class QtLogHandler(logging.Handler):
    def __init__(self, signal):
        super().__init__()
        self.signal = signal

    def emit(self, record):
        msg = self.format(record)
        self.signal.emit(msg)

class BotWorker(QObject):
    log_signal = pyqtSignal(str)
    status_signal = pyqtSignal(bool)

    def __init__(self):
        super().__init__()
        self._is_running = False
        self.loop = None

    def run_bot(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
        # Подключаем логгер aiogram к нашему окну
        logger = logging.getLogger('aiogram')
        handler = QtLogHandler(self.log_signal)
        logger.addHandler(handler)
        
        self._is_running = True
        self.status_signal.emit(True)
        
        try:
            self.loop.run_until_complete(dp.start_polling(bot))
        except Exception as e:
            self.log_signal.emit(f"Ошибка: {e}")
        finally:
            self._is_running = False
            self.status_signal.emit(False)

class MyFineAdminApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MyFine ✨ Bot Host & Panel")
        self.resize(800, 600)
        
        self.worker = BotWorker()
        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # --- ВКЛАДКА 1: КОНСОЛЬ ---
        console_widget = QWidget()
        console_layout = QVBoxLayout(console_widget)
        
        self.console_output = QTextEdit()
        self.console_output.setReadOnly(True)
        self.console_output.setStyleSheet("background-color: #1e1e1e; color: #d4d4d4; font-family: 'Consolas';")
        
        self.btn_start = QPushButton("🚀 Запустить бота")
        self.btn_start.setFixedHeight(40)
        self.btn_start.clicked.connect(self.start_bot_thread)
        self.btn_start.setStyleSheet("background-color: #28a745; color: white; font-weight: bold;")

        console_layout.addWidget(QLabel("📝 Консоль событий (Live):"))
        console_layout.addWidget(self.console_output)
        console_layout.addWidget(self.btn_start)
        
        # --- ВКЛАДКА 2: БАЗА АДМИНОВ ---
        admin_widget = QWidget()
        admin_layout = QVBoxLayout(admin_widget)
        
        self.admin_table = QTableWidget()
        self.admin_table.setColumnCount(2)
        self.admin_table.setHorizontalHeaderLabels(["Логин", "Пароль"])
        self.load_admins()

        admin_layout.addWidget(QLabel("🔐 Список учетных записей модераторов:"))
        admin_layout.addWidget(self.admin_table)

        self.tabs.addTab(console_widget, "🖥 Консоль")
        self.tabs.addTab(admin_widget, "👥 Админы")

        # Сигналы
        self.worker.log_signal.connect(self.update_console)
        self.worker.status_signal.connect(self.update_status)

    def load_admins(self):
        self.admin_table.setRowCount(len(USERS_DB))
        for i, (login, password) in enumerate(USERS_DB.items()):
            self.admin_table.setItem(i, 0, QTableWidgetItem(login))
            self.admin_table.setItem(i, 1, QTableWidgetItem(password))

    def update_console(self, text):
        self.console_output.append(text)

    def update_status(self, running):
        if running:
            self.btn_start.setText("✅ Бот запущен (Работает)")
            self.btn_start.setEnabled(False)
            self.btn_start.setStyleSheet("background-color: #555; color: #ccc;")

    def start_bot_thread(self):
        self.update_console("--- Запуск систем MyFine... ---")
        threading.Thread(target=self.worker.run_bot, daemon=True).start()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MyFineAdminApp()
    window.show()
    sys.exit(app.exec())