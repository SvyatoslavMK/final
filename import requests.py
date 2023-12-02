import requests
from bs4 import BeautifulSoup
import tkinter as tk
from tkinter import ttk
import sqlite3
import customtkinter


class DataParser:   
    def __init__(self):
        self.url = ""
        self.selected_tags = []
        self.data = []

    def parse_data(self):
        try:
            headers = {'User-Agent': 'My User Agent 1.0'}
            if not self.url.startswith(('http://', 'https://')):
                self.url = 'https://' + self.url

            response = requests.get(self.url,headers=headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            self.data = []
            for tag in self.selected_tags:
                elements = soup.find_all(tag)
                self.data.extend([element.text.strip() for element in elements])

        except requests.exceptions.RequestException as e:
            return f"Error during data parsing: {e}"


class DataViewerWindow:
    def __init__(self, data):
        self.window = tk.Toplevel()
        self.window.title('Data Viewer')
        self.window.geometry('500x300')

        self.listbox = tk.Listbox(self.window)
        self.listbox.pack(expand=True, fill=tk.BOTH)

        for item in data:
            self.listbox.insert(tk.END, item)


class DatabaseManager:
    def __init__(self, db_name='data.db'):
        try:
            self.connection = sqlite3.connect(db_name)
            self.cursor = self.connection.cursor()
            self.create_table()
        except sqlite3.Error as e:
            raise RuntimeError(f"Error connecting to the database: {e}")

    def create_table(self):
        try:
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS parsed_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    data_column TEXT
                )
            ''')
            self.connection.commit()
        except sqlite3.Error as e:
            raise RuntimeError(f"Error creating table: {e}")

    def insert_data(self, data):
        try:
            self.cursor.execute('INSERT INTO parsed_data (data_column) VALUES (?)', (data,))
            self.connection.commit()
        except sqlite3.Error as e:
            raise RuntimeError(f"Error inserting data: {e}")

    def clear_data(self):
        try:
            self.cursor.execute('DELETE FROM parsed_data')
            self.connection.commit()
        except sqlite3.Error as e:
            raise RuntimeError(f"Error clearing data: {e}")

    def fetch_all_data(self):
        try:
            self.cursor.execute('SELECT * FROM parsed_data')
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            raise RuntimeError(f"Error fetching data: {e}")


class GUI:
    def __init__(self, master):
        self.master = master
        self.master.title('Data Parser')

        self.url_label = ttk.Label(self.master, text='Enter URL:')
        self.url_entry = ttk.Entry(self.master, width=50)

        self.tag_label = ttk.Label(self.master, text='Select HTML Tags:')
        self.selected_tags = [
            tk.StringVar(value="h1"),
            tk.StringVar(value="h2"),
            tk.StringVar(value="h3"),
            tk.StringVar(value="h4"),
            tk.StringVar(value="h5"),
            tk.StringVar(value="h6"),
            tk.StringVar(value="title"),
            tk.StringVar(value="span"),
            tk.StringVar(value="p"),
            tk.StringVar(value="a"),
        ]
        self.tag_checkbuttons = [
            ttk.Checkbutton(self.master, text=f"<{tag.get()}>", variable=tag) for tag in self.selected_tags
        ]

        self.parse_button = ttk.Button(self.master, text='Parse and Load', command=self.parse_and_load)
        self.view_data_button = ttk.Button(self.master, text='View Data', command=self.view_data)
        self.clear_button = ttk.Button(self.master, text='Clear Data', command=self.clear_data)
        self.status_label = ttk.Label(self.master, text='Status:')

        self.url_label.grid(row=0, column=0, pady=10)
        self.url_entry.grid(row=0, column=1, pady=10)
        self.tag_label.grid(row=1, column=0, pady=10)
        for i, checkbutton in enumerate(self.tag_checkbuttons):
            checkbutton.grid(row=i + 1, column=1, sticky='w')
        self.parse_button.grid(row=len(self.tag_checkbuttons) + 1, column=0, columnspan=2, pady=10)
        self.view_data_button.grid(row=len(self.tag_checkbuttons) + 2, column=0, columnspan=2, pady=10)
        self.clear_button.grid(row=len(self.tag_checkbuttons) + 3, column=0, columnspan=2, pady=10)
        self.status_label.grid(row=len(self.tag_checkbuttons) + 4, column=0, columnspan=2, pady=10)

        self.parsed_data = []
        self.data_parser = DataParser()
        self.db_manager = DatabaseManager()

    def parse_and_load(self):
        self.data_parser.url = self.url_entry.get()
        self.data_parser.selected_tags = [tag.get() for tag in self.selected_tags if tag.get()]

        if not self.data_parser.url or not self.data_parser.selected_tags:
            self.status_label['text'] = 'Enter URL and select at least one HTML tag.'
            return

        error_message = self.data_parser.parse_data()

        if error_message:
            self.status_label['text'] = error_message
        else:
            self.parsed_data = self.data_parser.data
            for item in self.parsed_data:
                try:
                    self.db_manager.insert_data(item)
                except RuntimeError as e:
                    self.status_label['text'] = f"Error: {e}"

            self.status_label['text'] = 'Data loaded successfully.'

    def view_data(self):
        if not self.parsed_data:
            self.status_label['text'] = 'No data to display. Parse and load data first.'
            return

        data_viewer = DataViewerWindow(self.parsed_data)

    def clear_data(self):
        try:
            self.db_manager.clear_data()
            self.status_label['text'] = 'Data cleared successfully.'
        except RuntimeError as e:
            self.status_label['text'] = f"Error: {e}"


if __name__ == '__main__':
    root = tk.Tk()
    app = GUI(root)
    root.mainloop()
