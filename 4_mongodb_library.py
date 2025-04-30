"""
Реализация библиотечной системы с использованием MongoDB
"""
import hashlib
import json
import xml.etree.ElementTree as ET
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime


class LibrarySystem:
    def __init__(self):
        self.current_user = None

        # Инициализация БД с использованием MongoDB
        self.initialize_database()

        # Создание основного окна приложения
        self.root = tk.Tk()
        self.root.title('Библиотечная информационная система (MongoDB)')
        self.root.geometry('800x600')

        # Открытие окна авторизации
        self.show_login_screen()

    def initialize_database(self):
        """Инициализация БД с использованием MongoDB"""
        # Создание подключения к MongoDB
        self.client = MongoClient('mongodb://localhost:27017/')
        self.db = self.client['library_db']

        # Получение коллекций (аналог таблиц в SQL)
        self.users_collection = self.db['users']
        self.authors_collection = self.db['authors']
        self.books_collection = self.db['books']

        # Добавление тестового администратора, если коллекция пользователей пуста
        admin_count = self.users_collection.count_documents({})
        if admin_count == 0:
            admin_password = self.hash_password("admin")
            admin_user = {
                "username": "admin",
                "password": admin_password,
                "is_admin": 1,
                "created_at": datetime.now()
            }
            self.users_collection.insert_one(admin_user)

    def hash_password(self, password):
        """Хэширование пароля с использованием SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()

    def authenticate(self, username, password):
        """Проверка учётных данных пользователя с использованием MongoDB"""
        hashed_password = self.hash_password(password)
        user = self.users_collection.find_one({"username": username, "password": hashed_password})

        if user:
            self.current_user = {
                "id": str(user["_id"]),
                "username": username,
                "is_admin": user.get("is_admin", 0)
            }
            return True
        return False

    def register_user(self, username, password, confirm_password):
        """Регистрация нового пользователя с использованием MongoDB"""
        if not username or not password:
            messagebox.showerror("Ошибка", "Необходимо заполнить все поля")
            return

        if password != confirm_password:
            messagebox.showerror("Ошибка", "Пароли не совпадают")
            return

        try:
            # Проверка существования пользователя
            existing_user = self.users_collection.find_one({"username": username})
            if existing_user:
                messagebox.showerror("Ошибка", "Пользователь с таким именем уже существует")
                return

            hashed_password = self.hash_password(password)
            new_user = {
                "username": username,
                "password": hashed_password,
                "is_admin": 0,
                "created_at": datetime.now()
            }

            self.users_collection.insert_one(new_user)
            messagebox.showinfo("Успех", "Пользователь успешно зарегистрирован")
            self.show_login_screen()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось зарегистрировать пользователя: {str(e)}")

    def show_books(self):
        """Отображение списка всех книг с использованием MongoDB"""
        # Очистка рабочей области
        self.clear_workspace()

        # Создание фрейма для отображения книг
        books_frame = ttk.Frame(self.root, padding="10")
        books_frame.pack(fill=tk.BOTH, expand=True)

        # Заголовок
        ttk.Label(books_frame, text="Список книг", font=("Arial", 16)).pack(pady=10)

        # Создание таблицы для отображения книг
        columns = ('id', 'title', 'author', 'pages', 'publisher', 'year')
        tree = ttk.Treeview(books_frame, columns=columns, show='headings')

        # Настройка заголовков столбцов
        tree.heading('id', text='ID')
        tree.heading('title', text='Название')
        tree.heading('author', text='Автор')
        tree.heading('pages', text='Страниц')
        tree.heading('publisher', text='Издательство')
        tree.heading('year', text='Год издания')

        # Настройка ширины столбцов
        tree.column('id', width=30)
        tree.column('title', width=200)
        tree.column('author', width=150)
        tree.column('pages', width=80)
        tree.column('publisher', width=150)
        tree.column('year', width=100)

        # Добавление скроллбара
        scrollbar = ttk.Scrollbar(books_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        tree.pack(fill=tk.BOTH, expand=True)

        # Получение данных из БД с использованием MongoDB (с выполнением JOIN через $lookup)
        pipeline = [
            {
                "$lookup": {
                    "from": "authors",
                    "localField": "author_id",
                    "foreignField": "_id",
                    "as": "author_info"
                }
            },
            {
                "$unwind": {
                    "path": "$author_info",
                    "preserveNullAndEmptyArrays": True
                }
            }
        ]

        books = list(self.books_collection.aggregate(pipeline))

        # Заполнение таблицы данными
        for book in books:
            author_name = book.get("author_info", {}).get("name", "Неизвестен")
            book_id = str(book.get("_id"))[:8]  # Сокращаем ID для отображения
            tree.insert('', tk.END, values=(
                book_id,
                book.get("title", ""),
                author_name,
                book.get("pages", ""),
                book.get("publisher", ""),
                book.get("publication_year", "")
            ))

        # Добавление кнопки возврата
        ttk.Button(books_frame, text="Назад", command=self.show_main_menu).pack(pady=10)

    def show_authors(self):
        """Отображение списка всех авторов с использованием MongoDB"""
        # Очистка рабочей области
        self.clear_workspace()

        # Создание фрейма для отображения авторов
        authors_frame = ttk.Frame(self.root, padding="10")
        authors_frame.pack(fill=tk.BOTH, expand=True)

        # Заголовок
        ttk.Label(authors_frame, text="Список авторов", font=("Arial", 16)).pack(pady=10)

        # Создание таблицы для отображения авторов
        columns = ('id', 'name', 'country', 'birth_year', 'death_year')
        tree = ttk.Treeview(authors_frame, columns=columns, show='headings')

        # Настройка заголовков столбцов
        tree.heading('id', text='ID')
        tree.heading('name', text='Имя')
        tree.heading('country', text='Страна')
        tree.heading('birth_year', text='Год рождения')
        tree.heading('death_year', text='Год смерти')

        # Настройка ширины столбцов
        tree.column('id', width=30)
        tree.column('name', width=200)
        tree.column('country', width=150)
        tree.column('birth_year', width=100)
        tree.column('death_year', width=100)

        # Добавление скроллбара
        scrollbar = ttk.Scrollbar(authors_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        tree.pack(fill=tk.BOTH, expand=True)

        # Получение данных из БД с использованием MongoDB
        authors = list(self.authors_collection.find())

        # Заполнение таблицы данными
        for author in authors:
            author_id = str(author.get("_id"))[:8]  # Сокращаем ID для отображения
            tree.insert('', tk.END, values=(
                author_id,
                author.get("name", ""),
                author.get("country", ""),
                author.get("birth_year", ""),
                author.get("death_year", "")
            ))

        # Добавление кнопок
        button_frame = ttk.Frame(authors_frame)
        button_frame.pack(pady=10)

        ttk.Button(button_frame, text="Экспорт в JSON",
                   command=lambda: self.export_author_to_json(tree)).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Экспорт в XML",
                   command=lambda: self.export_author_to_xml(tree)).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Назад", command=self.show_main_menu).pack(side=tk.LEFT, padx=5)

    def add_book(self, author, title, pages, publisher, year):
        """Добавление новой книги в БД с использованием MongoDB"""
        if not title:
            messagebox.showerror("Ошибка", "Название книги обязательно для заполнения")
            return

        try:
            # Парсинг ID автора из строки формата "id: name"
            author_id = None
            if author:
                try:
                    author_id = ObjectId(author.split(':')[0].strip())
                except:
                    pass

            # Преобразование строковых данных в соответствующие типы
            pages_int = int(pages) if pages and pages.isdigit() else None
            year_int = int(year) if year and year.isdigit() else None

            new_book = {
                "author_id": author_id,
                "title": title,
                "pages": pages_int,
                "publisher": publisher,
                "publication_year": year_int,
                "created_at": datetime.now()
            }

            self.books_collection.insert_one(new_book)
            messagebox.showinfo("Успех", "Книга успешно добавлена")
            self.show_books()
        except ValueError:
            messagebox.showerror("Ошибка", "Проверьте правильность ввода числовых значений")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось добавить книгу: {str(e)}")

    def add_author(self, name, country, birth_year, death_year):
        """Добавление нового автора в БД с использованием MongoDB"""
        if not name:
            messagebox.showerror("Ошибка", "Имя автора обязательно для заполнения")
            return

        try:
            # Преобразование строковых данных в соответствующие типы
            birth_year_int = int(birth_year) if birth_year and birth_year.isdigit() else None
            death_year_int = int(death_year) if death_year and death_year.isdigit() else None

            new_author = {
                "name": name,
                "country": country,
                "birth_year": birth_year_int,
                "death_year": death_year_int,
                "created_at": datetime.now()
            }

            self.authors_collection.insert_one(new_author)
            messagebox.showinfo("Успех", "Автор успешно добавлен")
            self.show_authors()
        except ValueError:
            messagebox.showerror("Ошибка", "Проверьте правильность ввода годов жизни")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось добавить автора: {str(e)}")

    def import_author_from_file(self, file_path, format_type):
        """Импорт автора из файла JSON или XML с использованием MongoDB"""
        if not file_path:
            messagebox.showerror("Ошибка", "Выберите файл для импорта")
            return

        try:
            author_data = None

            if format_type == "json":
                author_data = self.parse_author_from_json(file_path)
            elif format_type == "xml":
                author_data = self.parse_author_from_xml(file_path)
            else:
                messagebox.showerror("Ошибка", "Неподдерживаемый формат файла")
                return

            if author_data and author_data['name']:
                # Добавление дополнительных полей для MongoDB
                author_data['created_at'] = datetime.now()

                # Преобразование типов данных
                if 'birth_year' in author_data and author_data['birth_year']:
                    author_data['birth_year'] = int(author_data['birth_year'])
                if 'death_year' in author_data and author_data['death_year']:
                    author_data['death_year'] = int(author_data['death_year'])

                # Добавление автора в MongoDB
                self.authors_collection.insert_one(author_data)

                messagebox.showinfo("Успех", "Автор успешно импортирован")
                self.show_authors()
            else:
                messagebox.showerror("Ошибка", "Не удалось получить необходимые данные из файла")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось импортировать автора: {str(e)}")

    def export_author_to_json(self, tree):
        """Экспорт выбранного автора в JSON файл"""
        selected_item = tree.selection()
        if not selected_item:
            messagebox.showerror("Ошибка", "Выберите автора для экспорта")
            return

        try:
            # Получение данных выбранного автора
            item_values = tree.item(selected_item[0])['values']
            author_id = item_values[0]

            # Поиск автора в базе данных по ID
            author = self.authors_collection.find_one({"_id": ObjectId(author_id)})

            if not author:
                messagebox.showerror("Ошибка", "Автор не найден в базе данных")
                return

            # Получение пути для сохранения файла
            file_path = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON файлы", "*.json"), ("Все файлы", "*.*")]
            )

            if not file_path:
                return

            # Подготовка данных для экспорта
            export_data = {
                "name": author.get("name", ""),
                "country": author.get("country", ""),
                "years": [author.get("birth_year"), author.get("death_year")]
            }

            # Удаление полей MongoDB перед экспортом
            if "_id" in export_data:
                del export_data["_id"]

            # Запись данных в файл
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=4)

            messagebox.showinfo("Успех", f"Автор успешно экспортирован в файл {file_path}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось экспортировать автора: {str(e)}")

    def export_author_to_xml(self, tree):
        """Экспорт выбранного автора в XML файл"""
        selected_item = tree.selection()
        if not selected_item:
            messagebox.showerror("Ошибка", "Выберите автора для экспорта")
            return

        try:
            # Получение данных выбранного автора
            item_values = tree.item(selected_item[0])['values']
            author_id = item_values[0]

            # Поиск автора в базе данных по ID
            author = self.authors_collection.find_one({"_id": ObjectId(author_id)})

            if not author:
                messagebox.showerror("Ошибка", "Автор не найден в базе данных")
                return

            # Получение пути для сохранения файла
            file_path = filedialog.asksaveasfilename(
                defaultextension=".xml",
                filetypes=[("XML файлы", "*.xml"), ("Все файлы", "*.*")]
            )

            if not file_path:
                return

            # Создание XML-документа
            root = ET.Element("author")

            name_elem = ET.SubElement(root, "name")
            name_elem.text = author.get("name", "")

            country_elem = ET.SubElement(root, "country")
            country_elem.text = author.get("country", "")

            years_elem = ET.SubElement(root, "years")
            if author.get("birth_year"):
                years_elem.set("born", str(author.get("birth_year")))
            if author.get("death_year"):
                years_elem.set("died", str(author.get("death_year")))

            # Запись XML в файл
            tree = ET.ElementTree(root)
            tree.write(file_path, encoding='utf-8', xml_declaration=True)

            messagebox.showinfo("Успех", f"Автор успешно экспортирован в файл {file_path}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось экспортировать автора: {str(e)}")

    # Реализация запрошенных запросов
    def show_authors_by_birth_year_range(self, start_year, end_year):
        """Вывод фамилий всех авторов, родившихся в диапазоне между X и Y годами"""
        # Очистка рабочей области
        self.clear_workspace()

        # Создание фрейма для отображения результатов
        result_frame = ttk.Frame(self.root, padding="10")
        result_frame.pack(fill=tk.BOTH, expand=True)

        # Заголовок
        ttk.Label(
            result_frame,
            text=f"Авторы, родившиеся между {start_year} и {end_year} годами",
            font=("Arial", 16)
        ).pack(pady=10)

        # Создание таблицы для отображения результатов
        columns = ('id', 'name', 'birth_year')
        tree = ttk.Treeview(result_frame, columns=columns, show='headings')

        # Настройка заголовков столбцов
        tree.heading('id', text='ID')
        tree.heading('name', text='Имя')
        tree.heading('birth_year', text='Год рождения')

        # Настройка ширины столбцов
        tree.column('id', width=30)
        tree.column('name', width=250)
        tree.column('birth_year', width=100)

        # Добавление скроллбара
        scrollbar = ttk.Scrollbar(result_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        tree.pack(fill=tk.BOTH, expand=True)

        # Выполнение запроса с использованием MongoDB
        authors = list(self.authors_collection.find({
            "birth_year": {"$gte": start_year, "$lte": end_year}
        }))

        # Заполнение таблицы данными
        for author in authors:
            author_id = str(author.get("_id"))[:8]  # Сокращаем ID для отображения
            tree.insert('', tk.END, values=(
                author_id,
                author.get("name", ""),
                author.get("birth_year", "")
            ))

        # Добавление кнопки возврата
        ttk.Button(result_frame, text="Назад", command=self.show_main_menu).pack(pady=10)

    def show_books_by_russian_authors(self):
        """Вывод всех книг, написанных авторами из России"""
        # Очистка рабочей области
        self.clear_workspace()

        # Создание фрейма для отображения результатов
        result_frame = ttk.Frame(self.root, padding="10")
        result_frame.pack(fill=tk.BOTH, expand=True)

        # Заголовок
        ttk.Label(result_frame, text="Книги авторов из России", font=("Arial", 16)).pack(pady=10)

        # Создание таблицы для отображения результатов
        columns = ('title', 'author', 'publisher', 'year')
        tree = ttk.Treeview(result_frame, columns=columns, show='headings')

        # Настройка заголовков столбцов
        tree.heading('title', text='Название')
        tree.heading('author', text='Автор')
        tree.heading('publisher', text='Издательство')
        tree.heading('year', text='Год издания')

        # Настройка ширины столбцов
        tree.column('title', width=200)
        tree.column('author', width=150)
        tree.column('publisher', width=150)
        tree.column('year', width=100)

        # Добавление скроллбара
        scrollbar = ttk.Scrollbar(result_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        tree.pack(fill=tk.BOTH, expand=True)

        # Выполнение запроса с использованием MongoDB (аналог JOIN в SQL)
        pipeline = [
            {
                "$lookup": {
                    "from": "authors",
                    "localField": "author_id",
                    "foreignField": "_id",
                    "as": "author_info"
                }
            },
            {
                "$unwind": {
                    "path": "$author_info",
                    "preserveNullAndEmptyArrays": False
                }
            },
            {
                "$match": {
                    "author_info.country": {"$regex": "Россия", "$options": "i"}
                }
            }
        ]

        books = list(self.books_collection.aggregate(pipeline))

        # Заполнение таблицы данными
        for book in books:
            author_name = book.get("author_info", {}).get("name", "")
            tree.insert('', tk.END, values=(
                book.get("title", ""),
                author_name,
                book.get("publisher", ""),
                book.get("publication_year", "")
            ))

        # Добавление кнопки возврата
        ttk.Button(result_frame, text="Назад", command=self.show_main_menu).pack(pady=10)

    def show_books_by_page_count(self, min_pages):
        """Вывод всех книг с количеством страниц более N"""
        # Очистка рабочей области
        self.clear_workspace()

        # Создание фрейма для отображения результатов
        result_frame = ttk.Frame(self.root, padding="10")
        result_frame.pack(fill=tk.BOTH, expand=True)

        # Заголовок
        ttk.Label(result_frame, text=f"Книги с количеством страниц более {min_pages}", font=("Arial", 16)).pack(pady=10)

        # Создание таблицы для отображения результатов
        columns = ('title', 'author', 'pages', 'publisher')
        tree = ttk.Treeview(result_frame, columns=columns, show='headings')

        # Настройка заголовков столбцов
        tree.heading('title', text='Название')
        tree.heading('author', text='Автор')
        tree.heading('pages', text='Страниц')
        tree.heading('publisher', text='Издательство')

        # Настройка ширины столбцов
        tree.column('title', width=200)
        tree.column('author', width=150)
        tree.column('pages', width=80)
        tree.column('publisher', width=150)

        # Добавление скроллбара
        scrollbar = ttk.Scrollbar(result_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        tree.pack(fill=tk.BOTH, expand=True)

        # Выполнение запроса с использованием MongoDB
        pipeline = [
            {
                "$match": {
                    "pages": {"$gt": min_pages}
                }
            },
            {
                "$lookup": {
                    "from": "authors",
                    "localField": "author_id",
                    "foreignField": "_id",
                    "as": "author_info"
                }
            },
            {
                "$unwind": {
                    "path": "$author_info",
                    "preserveNullAndEmptyArrays": True
                }
            }
        ]

        books = list(self.books_collection.aggregate(pipeline))

        # Заполнение таблицы данными
        for book in books:
            author_name = book.get("author_info", {}).get("name", "Неизвестен")
            tree.insert('', tk.END, values=(
                book.get("title", ""),
                author_name,
                book.get("pages", ""),
                book.get("publisher", "")
            ))

        # Добавление кнопки возврата
        ttk.Button(result_frame, text="Назад", command=self.show_main_menu).pack(pady=10)

    def show_authors_by_book_count(self, min_books):
        """Вывод всех авторов с числом книг более N"""
        # Очистка рабочей области
        self.clear_workspace()

        # Создание фрейма для отображения результатов
        result_frame = ttk.Frame(self.root, padding="10")
        result_frame.pack(fill=tk.BOTH, expand=True)

        # Заголовок
        ttk.Label(result_frame, text=f"Авторы с числом книг более {min_books}", font=("Arial", 16)).pack(pady=10)

        # Создание таблицы для отображения результатов
        columns = ('name', 'country', 'book_count')
        tree = ttk.Treeview(result_frame, columns=columns, show='headings')

        # Настройка заголовков столбцов
        tree.heading('name', text='Имя')
        tree.heading('country', text='Страна')
        tree.heading('book_count', text='Количество книг')

        # Настройка ширины столбцов
        tree.column('name', width=200)
        tree.column('country', width=150)
        tree.column('book_count', width=150)

        # Добавление скроллбара
        scrollbar = ttk.Scrollbar(result_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        tree.pack(fill=tk.BOTH, expand=True)

        # Выполнение запроса с использованием MongoDB (аналог GROUP BY и HAVING в SQL)
        pipeline = [
            {
                "$lookup": {
                    "from": "books",
                    "localField": "_id",
                    "foreignField": "author_id",
                    "as": "books"
                }
            },
            {
                "$project": {
                    "name": 1,
                    "country": 1,
                    "book_count": {"$size": "$books"}
                }
            },
            {
                "$match": {
                    "book_count": {"$gt": min_books}
                }
            }
        ]

        authors = list(self.authors_collection.aggregate(pipeline))

        # Заполнение таблицы данными
        for author in authors:
            tree.insert('', tk.END, values=(
                author.get("name", ""),
                author.get("country", ""),
                author.get("book_count", 0)
            ))

            # Добавление кнопки возврата
            ttk.Button(result_frame, text="Назад", command=self.show_main_menu).pack(pady=10)

    def parse_author_from_json(self, file_path):
        """Парсинг данных автора из JSON-файла"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                author_data = json.load(f)

            # Проверяем необходимые поля
            if 'name' not in author_data:
                raise ValueError("В файле отсутствует обязательное поле 'name'")

            # Преобразование полей для соответствия структуре БД
            result = {
                "name": author_data.get("name", ""),
                "country": author_data.get("country", "")
            }

            # Обработка годов жизни (могут быть в разных форматах)
            if "years" in author_data and isinstance(author_data["years"], list):
                if len(author_data["years"]) >= 1 and author_data["years"][0]:
                    result["birth_year"] = int(author_data["years"][0])
                if len(author_data["years"]) >= 2 and author_data["years"][1]:
                    result["death_year"] = int(author_data["years"][1])

            return result
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось разобрать JSON-файл: {str(e)}")
            return None

    def parse_author_from_xml(self, file_path):
        """Парсинг данных автора из XML-файла"""
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()

            if root.tag != "author":
                raise ValueError("Неверный формат XML: корневой элемент должен быть 'author'")

            result = {
                "name": "",
                "country": ""
            }

            # Парсинг имени
            name_elem = root.find("name")
            if name_elem is not None and name_elem.text:
                result["name"] = name_elem.text
            else:
                raise ValueError("В XML-файле отсутствует обязательное поле 'name'")

            # Парсинг страны
            country_elem = root.find("country")
            if country_elem is not None and country_elem.text:
                result["country"] = country_elem.text

            # Парсинг годов жизни
            years_elem = root.find("years")
            if years_elem is not None:
                if "born" in years_elem.attrib:
                    result["birth_year"] = int(years_elem.attrib["born"])
                if "died" in years_elem.attrib:
                    result["death_year"] = int(years_elem.attrib["died"])

            return result
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось разобрать XML-файл: {str(e)}")
            return None

    def show_login_screen(self):
        """Отображение экрана авторизации"""
        # Очистка рабочей области
        self.clear_workspace()

        # Создание фрейма для авторизации
        login_frame = ttk.Frame(self.root, padding="20")
        login_frame.pack(expand=True)

        # Заголовок
        ttk.Label(login_frame, text="Вход в систему", font=("Arial", 16)).pack(pady=10)

        # Поля ввода
        username_frame = ttk.Frame(login_frame)
        username_frame.pack(pady=5, fill=tk.X)
        ttk.Label(username_frame, text="Имя пользователя:").pack(side=tk.LEFT)
        username_entry = ttk.Entry(username_frame, width=30)
        username_entry.pack(side=tk.LEFT, padx=5)

        password_frame = ttk.Frame(login_frame)
        password_frame.pack(pady=5, fill=tk.X)
        ttk.Label(password_frame, text="Пароль:").pack(side=tk.LEFT)
        password_entry = ttk.Entry(password_frame, width=30, show="*")
        password_entry.pack(side=tk.LEFT, padx=5)

        # Кнопки
        button_frame = ttk.Frame(login_frame)
        button_frame.pack(pady=10)

        ttk.Button(button_frame, text="Войти",
                   command=lambda: self.login(username_entry.get(), password_entry.get())
                   ).pack(side=tk.LEFT, padx=5)

        ttk.Button(button_frame, text="Регистрация",
                   command=self.show_registration_screen
                   ).pack(side=tk.LEFT, padx=5)

    def show_registration_screen(self):
        """Отображение экрана регистрации"""
        # Очистка рабочей области
        self.clear_workspace()

        # Создание фрейма для регистрации
        reg_frame = ttk.Frame(self.root, padding="20")
        reg_frame.pack(expand=True)

        # Заголовок
        ttk.Label(reg_frame, text="Регистрация пользователя", font=("Arial", 16)).pack(pady=10)

        # Поля ввода
        username_frame = ttk.Frame(reg_frame)
        username_frame.pack(pady=5, fill=tk.X)
        ttk.Label(username_frame, text="Имя пользователя:").pack(side=tk.LEFT)
        username_entry = ttk.Entry(username_frame, width=30)
        username_entry.pack(side=tk.LEFT, padx=5)

        password_frame = ttk.Frame(reg_frame)
        password_frame.pack(pady=5, fill=tk.X)
        ttk.Label(password_frame, text="Пароль:").pack(side=tk.LEFT)
        password_entry = ttk.Entry(password_frame, width=30, show="*")
        password_entry.pack(side=tk.LEFT, padx=5)

        confirm_frame = ttk.Frame(reg_frame)
        confirm_frame.pack(pady=5, fill=tk.X)
        ttk.Label(confirm_frame, text="Подтверждение:").pack(side=tk.LEFT)
        confirm_entry = ttk.Entry(confirm_frame, width=30, show="*")
        confirm_entry.pack(side=tk.LEFT, padx=5)

        # Кнопки
        button_frame = ttk.Frame(reg_frame)
        button_frame.pack(pady=10)

        ttk.Button(button_frame, text="Зарегистрироваться",
                   command=lambda: self.register_user(
                       username_entry.get(),
                       password_entry.get(),
                       confirm_entry.get()
                   )).pack(side=tk.LEFT, padx=5)

        ttk.Button(button_frame, text="Назад",
                   command=self.show_login_screen
                   ).pack(side=tk.LEFT, padx=5)

    def login(self, username, password):
        """Обработка входа пользователя"""
        if not username or not password:
            messagebox.showerror("Ошибка", "Необходимо заполнить все поля")
            return

        if self.authenticate(username, password):
            self.show_main_menu()
        else:
            messagebox.showerror("Ошибка", "Неверное имя пользователя или пароль")

    def show_main_menu(self):
        """Отображение главного меню"""
        # Очистка рабочей области
        self.clear_workspace()

        # Создание фрейма для главного меню
        menu_frame = ttk.Frame(self.root, padding="20")
        menu_frame.pack(expand=True)

        # Приветствие
        ttk.Label(
            menu_frame,
            text=f"Добро пожаловать, {self.current_user['username']}!",
            font=("Arial", 16)
        ).pack(pady=10)

        # Кнопки основных функций
        ttk.Button(menu_frame, text="Просмотр книг",
                   command=self.show_books, width=30
                   ).pack(pady=5)

        ttk.Button(menu_frame, text="Просмотр авторов",
                   command=self.show_authors, width=30
                   ).pack(pady=5)

        # Кнопки для добавления данных (только для администратора)
        if self.current_user['is_admin']:
            ttk.Button(menu_frame, text="Добавить книгу",
                       command=self.show_add_book_form, width=30
                       ).pack(pady=5)

            ttk.Button(menu_frame, text="Добавить автора",
                       command=self.show_add_author_form, width=30
                       ).pack(pady=5)

            ttk.Button(menu_frame, text="Импорт автора",
                       command=self.show_import_author_form, width=30
                       ).pack(pady=5)

        # Кнопки специальных запросов
        ttk.Label(menu_frame, text="Специальные запросы:", font=("Arial", 12)).pack(pady=(15, 5))

        ttk.Button(menu_frame, text="Авторы по году рождения",
                   command=self.show_authors_by_birth_year_form, width=30
                   ).pack(pady=5)

        ttk.Button(menu_frame, text="Книги российских авторов",
                   command=self.show_books_by_russian_authors, width=30
                   ).pack(pady=5)

        ttk.Button(menu_frame, text="Книги по числу страниц",
                   command=self.show_books_by_page_count_form, width=30
                   ).pack(pady=5)

        ttk.Button(menu_frame, text="Авторы по числу книг",
                   command=self.show_authors_by_book_count_form, width=30
                   ).pack(pady=5)

        # Кнопка выхода
        ttk.Button(menu_frame, text="Выйти",
                   command=self.logout, width=30
                   ).pack(pady=(15, 5))

    def logout(self):
        """Выход из системы"""
        self.current_user = None
        self.show_login_screen()

    def clear_workspace(self):
        """Очистка рабочей области от всех виджетов"""
        for widget in self.root.winfo_children():
            widget.destroy()

    def show_add_book_form(self):
        """Отображение формы для добавления новой книги"""
        # Очистка рабочей области
        self.clear_workspace()

        # Создание фрейма для формы
        form_frame = ttk.Frame(self.root, padding="20")
        form_frame.pack(expand=True)

        # Заголовок
        ttk.Label(form_frame, text="Добавление новой книги", font=("Arial", 16)).pack(pady=10)

        # Поля формы
        # Выбор автора из выпадающего списка
        author_frame = ttk.Frame(form_frame)
        author_frame.pack(pady=5, fill=tk.X)
        ttk.Label(author_frame, text="Автор:").pack(side=tk.LEFT)

        # Получение списка авторов из БД
        authors = list(self.authors_collection.find().sort("name"))
        author_list = [""] + [f"{str(a['_id'])}: {a['name']}" for a in authors]

        author_var = tk.StringVar()
        author_combobox = ttk.Combobox(author_frame, textvariable=author_var, width=30)
        author_combobox['values'] = author_list
        author_combobox.pack(side=tk.LEFT, padx=5)

        # Название книги
        title_frame = ttk.Frame(form_frame)
        title_frame.pack(pady=5, fill=tk.X)
        ttk.Label(title_frame, text="Название:").pack(side=tk.LEFT)
        title_entry = ttk.Entry(title_frame, width=30)
        title_entry.pack(side=tk.LEFT, padx=5)

        # Количество страниц
        pages_frame = ttk.Frame(form_frame)
        pages_frame.pack(pady=5, fill=tk.X)
        ttk.Label(pages_frame, text="Страниц:").pack(side=tk.LEFT)
        pages_entry = ttk.Entry(pages_frame, width=30)
        pages_entry.pack(side=tk.LEFT, padx=5)

        # Издательство
        publisher_frame = ttk.Frame(form_frame)
        publisher_frame.pack(pady=5, fill=tk.X)
        ttk.Label(publisher_frame, text="Издательство:").pack(side=tk.LEFT)
        publisher_entry = ttk.Entry(publisher_frame, width=30)
        publisher_entry.pack(side=tk.LEFT, padx=5)

        # Год издания
        year_frame = ttk.Frame(form_frame)
        year_frame.pack(pady=5, fill=tk.X)
        ttk.Label(year_frame, text="Год издания:").pack(side=tk.LEFT)
        year_entry = ttk.Entry(year_frame, width=30)
        year_entry.pack(side=tk.LEFT, padx=5)

        # Кнопки
        button_frame = ttk.Frame(form_frame)
        button_frame.pack(pady=10)

        ttk.Button(button_frame, text="Добавить",
                   command=lambda: self.add_book(
                       author_var.get(),
                       title_entry.get(),
                       pages_entry.get(),
                       publisher_entry.get(),
                       year_entry.get()
                   )).pack(side=tk.LEFT, padx=5)

        ttk.Button(button_frame, text="Назад",
                   command=self.show_main_menu
                   ).pack(side=tk.LEFT, padx=5)

    def show_add_author_form(self):
        """Отображение формы для добавления нового автора"""
        # Очистка рабочей области
        self.clear_workspace()

        # Создание фрейма для формы
        form_frame = ttk.Frame(self.root, padding="20")
        form_frame.pack(expand=True)

        # Заголовок
        ttk.Label(form_frame, text="Добавление нового автора", font=("Arial", 16)).pack(pady=10)

        # Поля формы
        # Имя автора
        name_frame = ttk.Frame(form_frame)
        name_frame.pack(pady=5, fill=tk.X)
        ttk.Label(name_frame, text="Имя:").pack(side=tk.LEFT)
        name_entry = ttk.Entry(name_frame, width=30)
        name_entry.pack(side=tk.LEFT, padx=5)

        # Страна
        country_frame = ttk.Frame(form_frame)
        country_frame.pack(pady=5, fill=tk.X)
        ttk.Label(country_frame, text="Страна:").pack(side=tk.LEFT)
        country_entry = ttk.Entry(country_frame, width=30)
        country_entry.pack(side=tk.LEFT, padx=5)

        # Год рождения
        birth_frame = ttk.Frame(form_frame)
        birth_frame.pack(pady=5, fill=tk.X)
        ttk.Label(birth_frame, text="Год рождения:").pack(side=tk.LEFT)
        birth_entry = ttk.Entry(birth_frame, width=30)
        birth_entry.pack(side=tk.LEFT, padx=5)

        # Год смерти
        death_frame = ttk.Frame(form_frame)
        death_frame.pack(pady=5, fill=tk.X)
        ttk.Label(death_frame, text="Год смерти:").pack(side=tk.LEFT)
        death_entry = ttk.Entry(death_frame, width=30)
        death_entry.pack(side=tk.LEFT, padx=5)

        # Кнопки
        button_frame = ttk.Frame(form_frame)
        button_frame.pack(pady=10)

        ttk.Button(button_frame, text="Добавить",
                   command=lambda: self.add_author(
                       name_entry.get(),
                       country_entry.get(),
                       birth_entry.get(),
                       death_entry.get()
                   )).pack(side=tk.LEFT, padx=5)

        ttk.Button(button_frame, text="Назад",
                   command=self.show_main_menu
                   ).pack(side=tk.LEFT, padx=5)

    def show_import_author_form(self):
        """Отображение формы для импорта автора из файла"""
        # Очистка рабочей области
        self.clear_workspace()

        # Создание фрейма для формы
        form_frame = ttk.Frame(self.root, padding="20")
        form_frame.pack(expand=True)

        # Заголовок
        ttk.Label(form_frame, text="Импорт автора из файла", font=("Arial", 16)).pack(pady=10)

        # Переменные для хранения пути к файлу и формата
        file_path_var = tk.StringVar()
        format_var = tk.StringVar(value="json")

        # Выбор файла
        file_frame = ttk.Frame(form_frame)
        file_frame.pack(pady=5, fill=tk.X)
        ttk.Label(file_frame, text="Файл:").pack(side=tk.LEFT)
        ttk.Entry(file_frame, textvariable=file_path_var, width=30).pack(side=tk.LEFT, padx=5)
        ttk.Button(file_frame, text="Обзор",
                   command=lambda: file_path_var.set(filedialog.askopenfilename(
                       filetypes=[("JSON файлы", "*.json"), ("XML файлы", "*.xml"), ("Все файлы", "*.*")]
                   ))
                   ).pack(side=tk.LEFT)

        # Выбор формата
        format_frame = ttk.Frame(form_frame)
        format_frame.pack(pady=5, fill=tk.X)
        ttk.Label(format_frame, text="Формат:").pack(side=tk.LEFT)
        ttk.Radiobutton(format_frame, text="JSON", variable=format_var, value="json").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(format_frame, text="XML", variable=format_var, value="xml").pack(side=tk.LEFT, padx=5)

        # Кнопки
        button_frame = ttk.Frame(form_frame)
        button_frame.pack(pady=10)

        ttk.Button(button_frame, text="Импортировать",
                   command=lambda: self.import_author_from_file(
                       file_path_var.get(),
                       format_var.get()
                   )).pack(side=tk.LEFT, padx=5)

        ttk.Button(button_frame, text="Назад",
                   command=self.show_main_menu
                   ).pack(side=tk.LEFT, padx=5)

    def show_authors_by_birth_year_form(self):
        """Отображение формы для поиска авторов по диапазону лет рождения"""
        # Очистка рабочей области
        self.clear_workspace()

        # Создание фрейма для формы
        form_frame = ttk.Frame(self.root, padding="20")
        form_frame.pack(expand=True)

        # Заголовок
        ttk.Label(form_frame, text="Поиск авторов по году рождения", font=("Arial", 16)).pack(pady=10)

        # Поля формы
        # Начальный год
        start_frame = ttk.Frame(form_frame)
        start_frame.pack(pady=5, fill=tk.X)
        ttk.Label(start_frame, text="С года:").pack(side=tk.LEFT)
        start_entry = ttk.Entry(start_frame, width=30)
        start_entry.pack(side=tk.LEFT, padx=5)

        # Конечный год
        end_frame = ttk.Frame(form_frame)
        end_frame.pack(pady=5, fill=tk.X)
        ttk.Label(end_frame, text="По год:").pack(side=tk.LEFT)
        end_entry = ttk.Entry(end_frame, width=30)
        end_entry.pack(side=tk.LEFT, padx=5)

        # Кнопки
        button_frame = ttk.Frame(form_frame)
        button_frame.pack(pady=10)

        ttk.Button(button_frame, text="Найти",
                   command=lambda: self.find_authors_by_birth_year(
                       start_entry.get(),
                       end_entry.get()
                   )).pack(side=tk.LEFT, padx=5)

        ttk.Button(button_frame, text="Назад",
                   command=self.show_main_menu
                   ).pack(side=tk.LEFT, padx=5)

    def find_authors_by_birth_year(self, start_year_str, end_year_str):
        """Поиск и отображение авторов по диапазону лет рождения"""
        try:
            # Проверка и преобразование ввода
            if not start_year_str or not end_year_str:
                messagebox.showerror("Ошибка", "Необходимо заполнить оба поля")
                return

            start_year = int(start_year_str)
            end_year = int(end_year_str)

            if start_year > end_year:
                messagebox.showerror("Ошибка", "Начальный год должен быть меньше или равен конечному")
                return

            # Вызов метода для отображения результатов
            self.show_authors_by_birth_year_range(start_year, end_year)
        except ValueError:
            messagebox.showerror("Ошибка", "Годы должны быть целыми числами")

    def show_books_by_page_count_form(self):
        """Отображение формы для поиска книг по количеству страниц"""
        # Очистка рабочей области
        self.clear_workspace()

        # Создание фрейма для формы
        form_frame = ttk.Frame(self.root, padding="20")
        form_frame.pack(expand=True)

        # Заголовок
        ttk.Label(form_frame, text="Поиск книг по количеству страниц", font=("Arial", 16)).pack(pady=10)

        # Поля формы
        # Минимальное количество страниц
        pages_frame = ttk.Frame(form_frame)
        pages_frame.pack(pady=5, fill=tk.X)
        ttk.Label(pages_frame, text="Минимум страниц:").pack(side=tk.LEFT)
        pages_entry = ttk.Entry(pages_frame, width=30)
        pages_entry.pack(side=tk.LEFT, padx=5)

        # Кнопки
        button_frame = ttk.Frame(form_frame)
        button_frame.pack(pady=10)

        ttk.Button(button_frame, text="Найти",
                   command=lambda: self.find_books_by_page_count(
                       pages_entry.get()
                   )).pack(side=tk.LEFT, padx=5)

        ttk.Button(button_frame, text="Назад",
                   command=self.show_main_menu
                   ).pack(side=tk.LEFT, padx=5)

    def find_books_by_page_count(self, min_pages_str):
        """Поиск и отображение книг по минимальному количеству страниц"""
        try:
            # Проверка и преобразование ввода
            if not min_pages_str:
                messagebox.showerror("Ошибка", "Необходимо указать минимальное количество страниц")
                return

            min_pages = int(min_pages_str)

            if min_pages < 0:
                messagebox.showerror("Ошибка", "Количество страниц должно быть положительным числом")
                return

            # Вызов метода для отображения результатов
            self.show_books_by_page_count(min_pages)
        except ValueError:
            messagebox.showerror("Ошибка", "Количество страниц должно быть целым числом")

    def show_authors_by_book_count_form(self):
        """Отображение формы для поиска авторов по количеству книг"""
        # Очистка рабочей области
        self.clear_workspace()

        # Создание фрейма для формы
        form_frame = ttk.Frame(self.root, padding="20")
        form_frame.pack(expand=True)

        # Заголовок
        ttk.Label(form_frame, text="Поиск авторов по количеству книг", font=("Arial", 16)).pack(pady=10)

        # Поля формы
        # Минимальное количество книг
        books_frame = ttk.Frame(form_frame)
        books_frame.pack(pady=5, fill=tk.X)
        ttk.Label(books_frame, text="Минимум книг:").pack(side=tk.LEFT)
        books_entry = ttk.Entry(books_frame, width=30)
        books_entry.pack(side=tk.LEFT, padx=5)

        # Кнопки
        button_frame = ttk.Frame(form_frame)
        button_frame.pack(pady=10)

        ttk.Button(button_frame, text="Найти",
                   command=lambda: self.find_authors_by_book_count(
                       books_entry.get()
                   )).pack(side=tk.LEFT, padx=5)

        ttk.Button(button_frame, text="Назад",
                   command=self.show_main_menu
                   ).pack(side=tk.LEFT, padx=5)

    def find_authors_by_book_count(self, min_books_str):
        """Поиск и отображение авторов по минимальному количеству книг"""
        try:
            # Проверка и преобразование ввода
            if not min_books_str:
                messagebox.showerror("Ошибка", "Необходимо указать минимальное количество книг")
                return

            min_books = int(min_books_str)

            if min_books < 0:
                messagebox.showerror("Ошибка", "Количество книг должно быть положительным числом")
                return

            # Вызов метода для отображения результатов
            self.show_authors_by_book_count(min_books)
        except ValueError:
            messagebox.showerror("Ошибка", "Количество книг должно быть целым числом")

    def run(self):
        """Запуск приложения"""
        self.root.mainloop()

app = LibrarySystem()
app.run()