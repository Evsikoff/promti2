import tkinter as tk
from tkinter import filedialog, messagebox
import sqlite3
import os

class DatabaseProcessorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Обработчик фраз")
        self.root.geometry("500x200")

        # Переменные для хранения путей и значений
        self.file_path = None
        self.default_dir = r"C:\Users\user\Downloads"
        self.db_path = r"C:\Users\user\Documents\promti2\promti2.db"

        # --- Элементы интерфейса ---

        # 1. Выбор файла
        frame_file = tk.Frame(root, padx=10, pady=10)
        frame_file.pack(fill=tk.X)

        lbl_file = tk.Label(frame_file, text="Файл:")
        lbl_file.pack(side=tk.LEFT)

        self.entry_file = tk.Entry(frame_file, width=40)
        self.entry_file.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        
        btn_browse = tk.Button(frame_file, text="Выбрать файл", command=self.browse_file)
        btn_browse.pack(side=tk.RIGHT)

        # 2. Идентификатор словаря
        frame_id = tk.Frame(root, padx=10, pady=5)
        frame_id.pack(fill=tk.X)

        lbl_id = tk.Label(frame_id, text="Идентификатор словаря:")
        lbl_id.pack(side=tk.LEFT)

        # Используем валидацию для ввода только цифр
        vcmd = (root.register(self.validate_number), '%P')
        self.entry_dict_id = tk.Entry(frame_id, validate="key", validatecommand=vcmd)
        self.entry_dict_id.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        # Привязываем событие изменения текста к проверке доступности кнопки
        self.entry_dict_id.bind("<KeyRelease>", self.check_inputs)

        # 3. Кнопка "Начать обработку"
        frame_btn = tk.Frame(root, padx=10, pady=20)
        frame_btn.pack(fill=tk.X)

        self.btn_start = tk.Button(frame_btn, text="Начать обработку", command=self.start_processing, state=tk.DISABLED)
        self.btn_start.pack(fill=tk.X)

    def validate_number(self, value):
        """Проверка, что введены только цифры (целое число)"""
        if value == "":
            return True
        try:
            int(value)
            return True
        except ValueError:
            return False

    def browse_file(self):
        """Открытие диалога выбора файла"""
        # Если папки по умолчанию нет, используем пустую строку (рабочий стол или последнюю папку)
        initial_dir = self.default_dir if os.path.exists(self.default_dir) else ""
        
        file_path = filedialog.askopenfilename(
            title="Выберите файл",
            initialdir=initial_dir,
            filetypes=(("Text files", "*.txt"), ("All files", "*.*")) # Фильтр по .txt
        )
        
        if file_path:
            self.file_path = file_path
            self.entry_file.delete(0, tk.END)
            self.entry_file.insert(0, os.path.basename(file_path)) # Показываем только имя файла
            self.check_inputs()

    def check_inputs(self, event=None):
        """Проверка заполненности полей для активации кнопки"""
        file_selected = self.file_path is not None
        id_filled = self.entry_dict_id.get().strip() != ""

        if file_selected and id_filled:
            self.btn_start.config(state=tk.NORMAL)
        else:
            self.btn_start.config(state=tk.DISABLED)

    def start_processing(self):
        """Основной алгоритм обработки"""
        dict_id = int(self.entry_dict_id.get())
        
        if not os.path.exists(self.db_path):
            messagebox.showerror("Ошибка", f"База данных не найдена по пути:\n{self.db_path}")
            return

        try:
            # Подключение к БД
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            processed_count = 0
            
            # Чтение файла и обработка
            with open(self.file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    # Удаляем лишние пробелы и переносы строк
                    line = line.strip()
                    if not line:
                        continue

                    # 1. Преобразовать первую букву в верхний регистр
                    # Проверяем, что строка не пуста после strip
                    phrase_capitalized = line[0].upper() + line[1:]

                    # 2. Создать запись в таблице "phrases"
                    cursor.execute(
                        "INSERT INTO phrases (phrase, dictionary_id) VALUES (?, ?)",
                        (phrase_capitalized, dict_id)
                    )
                    
                    # 3. Получаем значение поля "id" созданной строки
                    phrase_id = cursor.lastrowid

                    # 4. Преобразовать первую букву обратно в нижний регистр
                    phrase_lower_first = phrase_capitalized[0].lower() + phrase_capitalized[1:]

                    # 5. Делим строку на комбинации из трех букв
                    # Пример: "абрикос" -> "абр", "ико"
                    # Идем по строке с шагом 3
                    for i in range(0, len(phrase_lower_first), 3):
                        combo = phrase_lower_first[i : i+3]
                        
                        # Если комбинация меньше 3 символов (хвост), пропускаем, 
                        # так как в примере указаны только полноценные тройки ("абр", "ико")
                        if len(combo) < 3:
                            continue
                            
                        # 6. Сделать запись в таблицу "forbidden_words"
                        cursor.execute(
                            "INSERT INTO forbidden_words (phrase_id, root) VALUES (?, ?)",
                            (phrase_id, combo)
                        )
                    
                    processed_count += 1

            # Сохраняем изменения в БД
            conn.commit()
            conn.close()

            messagebox.showinfo("Успех", f"Обработка завершена.\nОбработано строк: {processed_count}")

        except sqlite3.Error as e:
            messagebox.showerror("Ошибка БД", f"Произошла ошибка при работе с базой данных:\n{e}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Произошла непредвиденная ошибка:\n{e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = DatabaseProcessorApp(root)
    root.mainloop()