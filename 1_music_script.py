# Скрипт, читающий во всех mp3-файлах указанной
# директории ID3v1-теги и выводящий информацию о каждом файле в
# виде: [имя исполнителя] - [название трека] - [название альбома].
# Команда в консоли: python 1_music_script.py C:\Users\korol\Downloads\music
import os
import argparse
import chardet
from typing import Dict, Optional, Tuple


def detect_encoding(data: bytes) -> str:
    """
    Определяет возможную кодировку данных.

    Args:
        data: Байты для определения кодировки

    Returns:
        Строка с названием кодировки
    """
    # Пробуем определить кодировку с помощью chardet
    detection = chardet.detect(data)
    encoding = detection['encoding']

    # Если кодировка не обнаружена или confidence низкий, выбираем windows-1251 для кириллицы
    if not encoding or detection['confidence'] < 0.6:
        if any(b > 127 for b in data):  # Наличие символов вне ASCII может указывать на кириллицу
            return 'windows-1251'
        return 'latin1'

    return encoding


def decode_string(byte_data: bytes) -> str:
    """
    Декодирует строку с определением кодировки.

    Args:
        byte_data: Байты для декодирования

    Returns:
        Декодированная строка
    """
    # Удаляем нулевые байты в конце
    clean_data = byte_data.rstrip(b'\x00')

    # Если данных нет, возвращаем пустую строку
    if not clean_data:
        return ""

    # Пытаемся определить кодировку
    encoding = detect_encoding(clean_data)

    # Пробуем декодировать с определенной кодировкой
    try:
        return clean_data.decode(encoding)
    except UnicodeDecodeError:
        # Если не получилось, пробуем распространенные кодировки для кириллицы
        for enc in ['windows-1251', 'koi8-r', 'utf-8', 'latin1']:
            try:
                return clean_data.decode(enc)
            except UnicodeDecodeError:
                continue

    # Если ничего не помогло, возвращаем строку с заменой непонятных символов
    return clean_data.decode('latin1', errors='replace')


def get_id3v1_tag(file_path: str) -> Tuple[Optional[Dict], bytes]:
    """
    Извлекает ID3v1-тег из MP3 файла.

    Args:
        file_path: Путь к MP3 файлу

    Returns:
        Кортеж (словарь с тегами или None, если тег не найден, и сырые данные тега)
    """
    try:
        with open(file_path, 'rb') as f:
            # Перемещаемся к концу файла минус 128 байт (размер ID3v1 тега)
            f.seek(-128, os.SEEK_END)
            tag_data = f.read(128)

            # Проверяем, что это действительно ID3v1-тег (первые 3 байта должны быть "TAG")
            if tag_data[:3] != b'TAG':
                return None, b''

            # Распаковываем данные с учетом кодировки
            title = decode_string(tag_data[3:33])
            artist = decode_string(tag_data[33:63])
            album = decode_string(tag_data[63:93])
            year = decode_string(tag_data[93:97])

            # Проверяем, содержит ли комментарийный раздел информацию о треке
            if tag_data[125] == 0:
                comment = decode_string(tag_data[97:125])
                track = tag_data[126]
            else:
                comment = decode_string(tag_data[97:127])
                track = 0

            genre = tag_data[127]

            return {
                'title': title,
                'artist': artist,
                'album': album,
                'year': year,
                'comment': comment,
                'track': track,
                'genre': genre
            }, tag_data
    except Exception as e:
        print(f"Ошибка при чтении файла {file_path}: {e}")
        return None, b''


def encode_string(text: str, max_length: int, encoding: str = 'windows-1251') -> bytes:
    """
    Кодирует строку в определенную кодировку и обрезает до заданной длины.

    Args:
        text: Текст для кодирования
        max_length: Максимальная длина в байтах
        encoding: Кодировка (по умолчанию windows-1251 для русских текстов)

    Returns:
        Байты закодированного текста
    """
    try:
        encoded = text.encode(encoding)
    except UnicodeEncodeError:
        # Если не получилось закодировать, пробуем другие кодировки
        for enc in ['utf-8', 'latin1']:
            try:
                encoded = text.encode(enc)
                break
            except UnicodeEncodeError:
                continue
        else:
            # Если все плохо, используем latin1 с заменой
            encoded = text.encode('latin1', errors='replace')

    # Обрезаем до нужной длины
    return encoded[:max_length]


def write_id3v1_tag(file_path: str, tag_data: Dict, encoding: str = 'windows-1251') -> bool:
    """
    Записывает ID3v1-тег в MP3 файл.

    Args:
        file_path: Путь к MP3 файлу
        tag_data: Словарь с тегами для записи
        encoding: Кодировка для записи текста (по умолчанию windows-1251)

    Returns:
        True если запись прошла успешно, иначе False
    """
    try:
        # Определяем, есть ли уже ID3v1-тег
        has_tag = False
        with open(file_path, 'rb') as f:
            f.seek(-128, os.SEEK_END)
            has_tag = f.read(3) == b'TAG'

        with open(file_path, 'r+b') as f:
            if has_tag:
                # Если тег уже есть, перемещаемся к его началу
                f.seek(-128, os.SEEK_END)
            else:
                # Если тега нет, перемещаемся в конец файла
                f.seek(0, os.SEEK_END)

            # Формируем новый тег
            new_tag = bytearray(128)

            # Заголовок "TAG"
            new_tag[0:3] = b'TAG'

            # Записываем поля с указанной кодировкой
            title_bytes = encode_string(tag_data['title'], 30, encoding)
            new_tag[3:3 + len(title_bytes)] = title_bytes

            artist_bytes = encode_string(tag_data['artist'], 30, encoding)
            new_tag[33:33 + len(artist_bytes)] = artist_bytes

            album_bytes = encode_string(tag_data['album'], 30, encoding)
            new_tag[63:63 + len(album_bytes)] = album_bytes

            year_bytes = encode_string(tag_data['year'], 4, encoding)
            new_tag[93:93 + len(year_bytes)] = year_bytes

            comment_bytes = encode_string(tag_data['comment'], 28, encoding)
            new_tag[97:97 + len(comment_bytes)] = comment_bytes

            # Zero-byte для трека
            new_tag[125] = 0

            # Номер трека
            new_tag[126] = tag_data['track']

            # Жанр
            new_tag[127] = tag_data['genre']

            # Записываем тег
            f.write(new_tag)

        return True
    except Exception as e:
        print(f"Ошибка при записи тега в файл {file_path}: {e}")
        return False


def hex_dump(data: bytes) -> str:
    """
    Создает 16-ричный дамп данных.

    Args:
        data: Байты для дампа

    Returns:
        Строка с 16-ричным дампом
    """
    hex_lines = []
    for i in range(0, len(data), 16):
        chunk = data[i:i + 16]
        hex_values = ' '.join(f'{b:02X}' for b in chunk)

        # Добавляем символьное представление
        ascii_repr = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)

        # Форматируем строку
        line = f"{i:04X}: {hex_values:<48} | {ascii_repr}"
        hex_lines.append(line)

    return '\n'.join(hex_lines)


def main():
    parser = argparse.ArgumentParser(description='Обработка ID3v1-тегов в MP3 файлах')
    parser.add_argument('directory', help='Директория с MP3 файлами')
    parser.add_argument('-d', '--dump', action='store_true', help='Вывести 16-ричный дамп тега')
    parser.add_argument('-g', '--genre', type=int, default=255,
                        help='Номер жанра для автоматической простановки (0-255, по умолчанию 255)')
    parser.add_argument('-e', '--encoding', default='windows-1251',
                        help='Кодировка для чтения/записи тегов (по умолчанию windows-1251)')

    args = parser.parse_args()

    # Проверяем, что указанная директория существует
    if not os.path.isdir(args.directory):
        print(f"Ошибка: директория {args.directory} не существует")
        return

    # Проверка диапазона жанра
    if not 0 <= args.genre <= 255:
        print(f"Ошибка: номер жанра должен быть в диапазоне 0-255")
        return

    # Проходим по всем файлам в директории
    for filename in os.listdir(args.directory):
        if filename.lower().endswith('.mp3'):
            file_path = os.path.join(args.directory, filename)

            # Получаем теги
            tag_info, tag_data = get_id3v1_tag(file_path)

            if tag_info:
                # Выводим информацию о файле
                print(f"{tag_info['artist']} - {tag_info['title']} - {tag_info['album']}")

                # Если запрошен дамп, выводим его
                if args.dump:
                    print("Дамп ID3v1-тега:")
                    print(hex_dump(tag_data))
                    print()

                # Проверяем, нужно ли проставить трек или жанр
                needs_update = False

                if tag_info['track'] == 0:
                    # В качестве примера, мы можем извлечь номер трека из имени файла, если оно начинается с цифр
                    # Например, "01 - Название трека.mp3"
                    try:
                        track_num = int(filename.split()[0])
                        tag_info['track'] = min(track_num, 255)  # Ограничиваем 255
                        needs_update = True
                        print(f"Проставлен номер трека: {tag_info['track']}")
                    except (ValueError, IndexError):
                        pass

                if tag_info['genre'] == 255:
                    tag_info['genre'] = args.genre
                    needs_update = True
                    print(f"Проставлен жанр: {args.genre}")

                # Если нужно обновить теги, делаем это
                if needs_update:
                    if write_id3v1_tag(file_path, tag_info, args.encoding):
                        print(f"Файл {filename} обновлен успешно")
                    else:
                        print(f"Не удалось обновить теги в файле {filename}")

                print("---")
            else:
                print(f"Файл {filename} не содержит ID3v1-тегов")
                print("---")


if __name__ == "__main__":
    main()