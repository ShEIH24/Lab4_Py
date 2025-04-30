"""
Реализация библиотечной системы с использованием SQLAlchemy
"""
import hashlib
import json
import xml.etree.ElementTree as ET
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

# Импорт необходимых модулей SQLAlchemy
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Table, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.sql import text

# Создаем базовый класс для декларативных определений
Base = declarative_base()


# Определение моделей SQLAlchemy
class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    is_admin = Column(Integer, default=0)


class Author(Base):
    __tablename__ = 'authors'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    country = Column(String)
    birth_year = Column(Integer)
    death_year = Column(Integer)

    # Отношение один-ко-многим с книгами
    books = relationship("Book", back_populates="author")


class Book(Base):
    __tablename__ = 'books'

    id = Column(Integer, primary_key=True)
    author_id = Column(Integer, ForeignKey('authors.id'))
    title = Column(String, nullable=False)
    pages = Column(Integer)
    publisher = Column(String)
    publication_year = Column(Integer)

    # Отношение многие-к-одному с автором
    author = relationship("Author", back_populates="books")


class LibrarySystem:
    def __init__(self):
        self.current_user = None

        # Инициализация БД с использованием SQLAlchemy
        self.initialize_database()

        # Создание основного окна приложения
        self.root = tk.Tk()
        self.root.title('Библиотечная информационная система (SQLAlchemy)')
        self.root.geometry('800x600')

        # Открытие окна авторизации
        self.show_login_screen()

    def initialize_database(self):
        """Инициализация БД с использованием SQLAlchemy"""
        # Создание подключения к базе данных SQLite
        self.engine = create_engine('sqlite:///library.db')

        # Создание таблиц
        Base.metadata.create_all(self.engine)

        # Создание сессии
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

        # Добавление тестового администратора, если таблица пользователей пуста
        admin_count = self.session.query(User).count()
        if admin_count == 0:
            admin_password = self.hash_password("admin")
            admin_user = User(username="admin", password=admin_password, is_admin=1)
            self.session.add(admin_user)
            self.session.commit()

    def hash_password(self, password):
        """Хэширование пароля с использованием SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()

    def authenticate(self, username, password):
        """Проверка учётных данных пользователя с использованием SQLAlchemy"""
        hashed_password = self.hash_password(password)
        user = self.session.query(User).filter_by(username=username, password=hashed_password).first()

        if user:
            self.current_user = {"id": user.id, "username": username, "is_admin": user.is_admin}
            return True
        return False

    def register_user(self, username, password, confirm_password):
        """Регистрация нового пользователя с использованием SQLAlchemy"""
        if not username or not password:
            messagebox.showerror("Ошибка", "Необходимо заполнить все поля")
            return

        if password != confirm_password:
            messagebox.showerror("Ошибка", "Пароли не совпадают")
            return

        try:
            hashed_password = self.hash_password(password)
            new_user = User(username=username, password=hashed_password)
            self.session.add(new_user)
            self.session.commit()
            messagebox.showinfo("Успех", "Пользователь успешно зарегистрирован")
            self.show_login_screen()
        except Exception as e:
            self.session.rollback()
            messagebox.showerror("Ошибка", f"Пользователь с таким именем уже существует: {str(e)}")

    def show_books(self):
        """Отображение списка всех книг с использованием SQLAlchemy"""
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

        # Получение данных из БД с использованием SQLAlchemy
        books = self.session.query(Book, Author.name).join(Author, Book.author_id == Author.id, isouter=True).all()

        # Заполнение таблицы данными
        for book, author_name in books:
            tree.insert('', tk.END,
                        values=(book.id, book.title, author_name, book.pages, book.publisher, book.publication_year))

        # Добавление кнопки возврата
        ttk.Button(books_frame, text="Назад", command=self.show_main_menu).pack(pady=10)

    def show_authors(self):
        """Отображение списка всех авторов с использованием SQLAlchemy"""
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

        # Получение данных из БД с использованием SQLAlchemy
        authors = self.session.query(Author).all()

        # Заполнение таблицы данными
        for author in authors:
            tree.insert('', tk.END,
                        values=(author.id, author.name, author.country, author.birth_year, author.death_year))

        # Добавление кнопок
        button_frame = ttk.Frame(authors_frame)
        button_frame.pack(pady=10)

        ttk.Button(button_frame, text="Экспорт в JSON",
                   command=lambda: self.export_author_to_json(tree)).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Экспорт в XML",
                   command=lambda: self.export_author_to_xml(tree)).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Назад", command=self.show_main_menu).pack(side=tk.LEFT, padx=5)

    def add_book(self, author, title, pages, publisher, year):
        """Добавление новой книги в БД с использованием SQLAlchemy"""
        if not title:
            messagebox.showerror("Ошибка", "Название книги обязательно для заполнения")
            return

        try:
            # Парсинг ID автора из строки формата "id: name"
            author_id = int(author.split(':')[0]) if author else None
            pages = int(pages) if pages else None
            year = int(year) if year else None

            new_book = Book(
                author_id=author_id,
                title=title,
                pages=pages,
                publisher=publisher,
                publication_year=year
            )

            self.session.add(new_book)
            self.session.commit()

            messagebox.showinfo("Успех", "Книга успешно добавлена")
            self.show_books()
        except ValueError:
            messagebox.showerror("Ошибка", "Проверьте правильность ввода числовых значений")
        except Exception as e:
            self.session.rollback()
            messagebox.showerror("Ошибка", f"Не удалось добавить книгу: {str(e)}")

    def add_author(self, name, country, birth_year, death_year):
        """Добавление нового автора в БД с использованием SQLAlchemy"""
        if not name:
            messagebox.showerror("Ошибка", "Имя автора обязательно для заполнения")
            return

        try:
            birth_year = int(birth_year) if birth_year else None
            death_year = int(death_year) if death_year else None

            new_author = Author(
                name=name,
                country=country,
                birth_year=birth_year,
                death_year=death_year
            )

            self.session.add(new_author)
            self.session.commit()

            messagebox.showinfo("Успех", "Автор успешно добавлен")
            self.show_authors()
        except ValueError:
            messagebox.showerror("Ошибка", "Проверьте правильность ввода годов жизни")
        except Exception as e:
            self.session.rollback()
            messagebox.showerror("Ошибка", f"Не удалось добавить автора: {str(e)}")

    def import_author_from_file(self, file_path, format_type):
        """Импорт автора из файла JSON или XML с использованием SQLAlchemy"""
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

            if author_data:
                name = author_data.get('name')
                country = author_data.get('country')
                birth_year = author_data.get('birth_year')
                death_year = author_data.get('death_year')

                # Добавление автора в БД с использованием SQLAlchemy
                new_author = Author(
                    name=name,
                    country=country,
                    birth_year=birth_year,
                    death_year=death_year
                )

                self.session.add(new_author)
                self.session.commit()

                messagebox.showinfo("Успех", "Автор успешно импортирован")
                self.show_authors()
        except Exception as e:
            self.session.rollback()
            messagebox.showerror("Ошибка", f"Не удалось импортировать автора: {str(e)}")

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

        # Выполнение запроса с использованием SQLAlchemy
        authors = self.session.query(Author).filter(
            Author.birth_year >= start_year,
            Author.birth_year <= end_year
        ).all()

        # Заполнение таблицы данными
        for author in authors:
            tree.insert('', tk.END, values=(author.id, author.name, author.birth_year))

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

        # Выполнение запроса с использованием SQLAlchemy
        books = self.session.query(Book, Author.name).join(Author).filter(
            Author.country.like('%Россия%')
        ).all()

        # Заполнение таблицы данными
        for book, author_name in books:
            tree.insert('', tk.END, values=(book.title, author_name, book.publisher, book.publication_year))

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

        # Выполнение запроса с использованием SQLAlchemy
        books = self.session.query(Book, Author.name).join(Author, isouter=True).filter(
            Book.pages > min_pages
        ).all()

        # Заполнение таблицы данными
        for book, author_name in books:
            tree.insert('', tk.END, values=(book.title, author_name, book.pages, book.publisher))

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

        # Выполнение запроса с использованием SQLAlchemy
        authors = self.session.query(
            Author, func.count(Book.id).label('book_count')
        ).outerjoin(Book).group_by(Author.id).having(
            func.count(Book.id) > min_books
        ).all()

        # Заполнение таблицы данными
        for author, book_count in authors:
            tree.insert('', tk.END, values=(author.name, author.country, book_count))

        # Добавление кнопки возврата
        ttk.Button(result_frame, text="Назад", command=self.show_main_menu).pack(pady=10)

    def show_main_menu(self):
        """Отображение главного меню программы с добавлением новых запросов"""
        # Очистка текущего окна
        for widget in self.root.winfo_children():
            widget.destroy()

        # Создание главного меню
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # Меню "Книги"
        book_menu = tk.Menu(menubar, tearoff=0)
        book_menu.add_command(label="Список книг", command=self.show_books)
        book_menu.add_command(label="Добавить книгу", command=self.show_add_book)
        book_menu.add_command(label="Книги с более N страниц",
                              command=lambda: self.show_books_by_page_count(300))  # Пример: 300 страниц
        menubar.add_cascade(label="Книги", menu=book_menu)

        # Меню "Авторы"
        author_menu = tk.Menu(menubar, tearoff=0)
        author_menu.add_command(label="Список авторов", command=self.show_authors)
        author_menu.add_command(label="Добавить автора", command=self.show_add_author)
        author_menu.add_command(label="Импорт автора из файла", command=self.show_import_author)
        author_menu.add_command(label="Авторы по годам рождения",
                                command=lambda: self.show_authors_by_birth_year_range(1800, 1900))  # Пример: 1800-1900
        author_menu.add_command(label="Авторы с более N книг",
                                command=lambda: self.show_authors_by_book_count(2))  # Пример: 2 книги
        menubar.add_cascade(label="Авторы", menu=author_menu)

        # Меню "Запросы"
        query_menu = tk.Menu(menubar, tearoff=0)
        query_menu.add_command(label="Книги российских авторов", command=self.show_books_by_russian_authors)
        menubar.add_cascade(label="Запросы", menu=query_menu)

        # Меню учетной записи
        account_menu = tk.Menu(menubar, tearoff=0)
        account_menu.add_command(label="Выход", command=self.show_login_screen)
        menubar.add_cascade(label="Учетная запись", menu=account_menu)

        # Создание начального фрейма для приветствия
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(expand=True)

        welcome_label = ttk.Label(main_frame,
                                  text=f"Добро пожаловать в библиотечную систему, {self.current_user['username']}!",
                                  font=("Arial", 16))
        welcome_label.pack(pady=20)

        instruction_label = ttk.Label(main_frame,
                                      text="Пожалуйста, используйте меню для навигации по системе.",
                                      font=("Arial", 12))
        instruction_label.pack(pady=10)

    def show_login_screen(self):
        """Отображение экрана авторизации"""
        # Очистка текущего окна
        for widget in self.root.winfo_children():
            widget.destroy()

        # Создание фрейма авторизации
        login_frame = ttk.Frame(self.root, padding='20')
        login_frame.pack(expand=True)

        # Заголовок
        ttk.Label(login_frame, text="Библиотечная система - Авторизация", font=("Arial", 16)).grid(row=0, column=0,
                                                                                                   columnspan=2,
                                                                                                   pady=10)

        # Поля ввода
        ttk.Label(login_frame, text="Имя пользователя:").grid(row=1, column=0, sticky=tk.W, pady=5)
        username_entry = ttk.Entry(login_frame, width=30)
        username_entry.grid(row=1, column=1, pady=5)

        ttk.Label(login_frame, text="Пароль:").grid(row=2, column=0, sticky=tk.W, pady=5)
        password_entry = ttk.Entry(login_frame, width=30, show="*")
        password_entry.grid(row=2, column=1, pady=5)

        # Кнопка входа
        ttk.Button(login_frame, text="Войти",
                   command=lambda: self.login(username_entry.get(), password_entry.get())).grid(row=3, column=0,
                                                                                                columnspan=2, pady=10)

        # Кнопка регистрации (только для демонстрации)
        ttk.Button(login_frame, text="Регистрация",
                   command=self.show_registration_screen).grid(row=4, column=0, columnspan=2)

    def show_registration_screen(self):
        """Отображение экрана регистрации"""
        # Очистка текущего окна
        for widget in self.root.winfo_children():
            widget.destroy()

        # Создание фрейма регистрации
        reg_frame = ttk.Frame(self.root, padding="20")
        reg_frame.pack(expand=True)

        # Заголовок
        ttk.Label(reg_frame, text="Библиотечная система - Регистрация", font=("Arial", 16)).grid(row=0, column=0,
                                                                                                 columnspan=2, pady=10)

        # Поля ввода
        ttk.Label(reg_frame, text="Имя пользователя:").grid(row=1, column=0, sticky=tk.W, pady=5)
        username_entry = ttk.Entry(reg_frame, width=30)
        username_entry.grid(row=1, column=1, pady=5)

        ttk.Label(reg_frame, text="Пароль:").grid(row=2, column=0, sticky=tk.W, pady=5)
        password_entry = ttk.Entry(reg_frame, width=30, show="*")
        password_entry.grid(row=2, column=1, pady=5)

        ttk.Label(reg_frame, text="Подтверждение пароля:").grid(row=3, column=0, sticky=tk.W, pady=5)
        confirm_entry = ttk.Entry(reg_frame, width=30, show="*")
        confirm_entry.grid(row=3, column=1, pady=5)

        # Кнопка регистрации
        ttk.Button(reg_frame, text="Зарегистрироваться",
                   command=lambda: self.register_user(username_entry.get(), password_entry.get(),
                                                      confirm_entry.get())).grid(row=4, column=0, columnspan=2, pady=10)

        # Кнопка возврата
        ttk.Button(reg_frame, text="Вернуться к авторизации",
                   command=self.show_login_screen).grid(row=5, column=0, columnspan=2)

    def login(self, username, password):
        """Обработка входа пользователя"""
        if not username or not password:
            messagebox.showerror("Ошибка", "Введите имя пользователя и пароль")
            return

        if self.authenticate(username, password):
            messagebox.showinfo("Успех", f"Добро пожаловать, {username}!")
            self.show_main_menu()
        else:
            messagebox.showerror("Ошибка", "Неверное имя пользователя или пароль")

    def show_add_book(self):
        """Отображение формы добавления новой книги"""
        # Очистка рабочей области
        self.clear_workspace()

        # Создание фрейма для добавления книги
        book_frame = ttk.Frame(self.root, padding="20")
        book_frame.pack(expand=True)

        # Заголовок
        ttk.Label(book_frame, text="Добавление новой книги", font=("Arial", 16)).grid(row=0, column=0, columnspan=2,
                                                                                      pady=10)

        # Выбор автора
        ttk.Label(book_frame, text="Автор:").grid(row=1, column=0, sticky=tk.W, pady=5)

        # Получение списка авторов из БД с использованием SQLAlchemy
        authors = self.session.query(Author.id, Author.name).all()

        # Создание комбобокса с авторами
        author_var = tk.StringVar()
        author_combo = ttk.Combobox(book_frame, textvariable=author_var, width=30)
        author_combo['values'] = [f"{author.id}: {author.name}" for author in authors]
        author_combo.grid(row=1, column=1, pady=5)

        # Поля для ввода данных о книге
        ttk.Label(book_frame, text="Название:").grid(row=2, column=0, sticky=tk.W, pady=5)
        title_entry = ttk.Entry(book_frame, width=30)
        title_entry.grid(row=2, column=1, pady=5)

        ttk.Label(book_frame, text="Количество страниц:").grid(row=3, column=0, sticky=tk.W, pady=5)
        pages_entry = ttk.Entry(book_frame, width=30)
        pages_entry.grid(row=3, column=1, pady=5)

        ttk.Label(book_frame, text="Издательство:").grid(row=4, column=0, sticky=tk.W, pady=5)
        publisher_entry = ttk.Entry(book_frame, width=30)
        publisher_entry.grid(row=4, column=1, pady=5)

        ttk.Label(book_frame, text="Год издания:").grid(row=5, column=0, sticky=tk.W, pady=5)
        year_entry = ttk.Entry(book_frame, width=30)
        year_entry.grid(row=5, column=1, pady=5)

        # Кнопки
        button_frame = ttk.Frame(book_frame)
        button_frame.grid(row=6, column=0, columnspan=2, pady=10)

        ttk.Button(button_frame, text="Добавить",
                   command=lambda: self.add_book(
                       author_var.get(), title_entry.get(), pages_entry.get(),
                       publisher_entry.get(), year_entry.get()
                   )).pack(side=tk.LEFT, padx=5)

        ttk.Button(button_frame, text="Отмена", command=self.show_main_menu).pack(side=tk.LEFT, padx=5)

    def show_add_author(self):
        """Отображение формы добавления нового автора"""
        # Очистка рабочей области
        self.clear_workspace()

        # Создание фрейма для добавления автора
        author_frame = ttk.Frame(self.root, padding="20")
        author_frame.pack(expand=True)

        # Заголовок
        ttk.Label(author_frame, text="Добавление нового автора", font=("Arial", 16)).grid(row=0, column=0, columnspan=2,
                                                                                          pady=10)

        # Поля для ввода данных об авторе
        ttk.Label(author_frame, text="Имя:").grid(row=1, column=0, sticky=tk.W, pady=5)
        name_entry = ttk.Entry(author_frame, width=30)
        name_entry.grid(row=1, column=1, pady=5)

        ttk.Label(author_frame, text="Страна:").grid(row=2, column=0, sticky=tk.W, pady=5)
        country_entry = ttk.Entry(author_frame, width=30)
        country_entry.grid(row=2, column=1, pady=5)

        ttk.Label(author_frame, text="Год рождения:").grid(row=3, column=0, sticky=tk.W, pady=5)
        birth_entry = ttk.Entry(author_frame, width=30)
        birth_entry.grid(row=3, column=1, pady=5)

        ttk.Label(author_frame, text="Год смерти:").grid(row=4, column=0, sticky=tk.W, pady=5)
        death_entry = ttk.Entry(author_frame, width=30)
        death_entry.grid(row=4, column=1, pady=5)

        # Кнопки
        button_frame = ttk.Frame(author_frame)
        button_frame.grid(row=5, column=0, columnspan=2, pady=10)

        ttk.Button(button_frame, text="Добавить",
                   command=lambda: self.add_author(
                       name_entry.get(), country_entry.get(), birth_entry.get(), death_entry.get()
                   )).pack(side=tk.LEFT, padx=5)

        ttk.Button(button_frame, text="Отмена", command=self.show_main_menu).pack(side=tk.LEFT, padx=5)

    def show_import_author(self):
        """Отображение формы импорта автора из файла"""
        # Очистка рабочей области
        self.clear_workspace()

        # Создание фрейма для импорта автора
        import_frame = ttk.Frame(self.root, padding="20")
        import_frame.pack(expand=True)

        # Заголовок
        ttk.Label(import_frame, text="Импорт автора из файла", font=("Arial", 16)).grid(row=0, column=0, columnspan=3,
                                                                                        pady=10)

        # Выбор формата файла
        ttk.Label(import_frame, text="Формат файла:").grid(row=1, column=0, sticky=tk.W, pady=5)

        format_var = tk.StringVar(value="json")
        ttk.Radiobutton(import_frame, text="JSON", variable=format_var, value="json").grid(row=1, column=1, pady=5)
        ttk.Radiobutton(import_frame, text="XML", variable=format_var, value="xml").grid(row=1, column=2, pady=5)

        # Выбор файла
        ttk.Label(import_frame, text="Файл:").grid(row=2, column=0, sticky=tk.W, pady=5)

        file_path_var = tk.StringVar()
        file_entry = ttk.Entry(import_frame, textvariable=file_path_var, width=40)
        file_entry.grid(row=2, column=1, pady=5)

        ttk.Button(import_frame, text="Обзор", command=lambda: self.browse_file(file_path_var, format_var.get())).grid(
            row=2, column=2, pady=5)

        # Кнопки
        button_frame = ttk.Frame(import_frame)
        button_frame.grid(row=3, column=0, columnspan=3, pady=10)

        ttk.Button(button_frame, text="Импортировать",
                   command=lambda: self.import_author_from_file(file_path_var.get(), format_var.get())
                   ).pack(side=tk.LEFT, padx=5)

        ttk.Button(button_frame, text="Отмена", command=self.show_main_menu).pack(side=tk.LEFT, padx=5)

    def clear_workspace(self):
        """Очистка рабочей области, сохраняя меню"""
        # Сохраняем главное меню
        menu = self.root.winfo_children()[0] if self.root.winfo_children() and isinstance(self.root.winfo_children()[0],
                                                                                          tk.Menu) else None

        # Удаляем все виджеты, кроме меню
        for widget in self.root.winfo_children():
            if widget != menu:
                widget.destroy()

    def parse_author_from_json(self, file_path):
        """Парсинг данных автора из JSON файла"""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        author_data = {
            'name': data.get('name'),
            'country': data.get('country'),
            'birth_year': None,
            'death_year': None
        }

        # Обработка годов жизни
        years = data.get('years', [])
        if len(years) >= 2:
            author_data['birth_year'] = years[0]
            author_data['death_year'] = years[1]

        return author_data

    def parse_author_from_xml(self, file_path):
        """Парсинг данных автора из XML файла"""
        tree = ET.parse(file_path)
        root = tree.getroot()

        author_data = {
            'name': None,
            'country': None,
            'birth_year': None,
            'death_year': None
        }

        # Получение имени автора
        name_elem = root.find('name')
        if name_elem is not None and name_elem.text:
            author_data['name'] = name_elem.text

        # Получение страны автора
        country_elem = root.find('country')
        if country_elem is not None and country_elem.text:
            author_data['country'] = country_elem.text

        # Получение годов жизни
        years_elem = root.find('years')
        if years_elem is not None:
            if 'born' in years_elem.attrib:
                try:
                    author_data['birth_year'] = int(years_elem.attrib['born'])
                except ValueError:
                    pass

            if 'died' in years_elem.attrib:
                try:
                    author_data['death_year'] = int(years_elem.attrib['died'])
                except ValueError:
                    pass

        return author_data

    def run(self):
        """Запуск приложения"""
        self.root.mainloop()

        # Закрытие соединения с БД при выходе
        if hasattr(self, 'session'):
            self.session.close()

app = LibrarySystem()
app.run()