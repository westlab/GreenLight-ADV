import tkinter as tk
from tkinter import filedialog, messagebox
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from datetime import datetime
import signal
import sys

class CSVPlotter:
    def __init__(self, master):
        self.master = master
        self.master.title("CSV Graph Tool")
        self.data = None
        self.columns_info = {}
        self.selected_columns = []
        self.filename_label = None
        self.start_entry = None
        self.end_entry = None
        self.range_info_label = None

        # Enable grid resizing
        self.master.rowconfigure(999, weight=1)
        self.master.columnconfigure(0, weight=1)

        self.create_widgets()

    def create_widgets(self):
        self.load_frame = tk.Frame(self.master)
        self.load_frame.grid(row=0, column=0, sticky='w')

        self.load_button = tk.Button(self.load_frame, text="Open CSV File", command=self.load_csv)
        self.load_button.pack(side=tk.LEFT)

        self.filename_label = tk.Label(self.load_frame, text="No file selected")
        self.filename_label.pack(side=tk.LEFT)

        self.column_listbox = tk.Listbox(self.master, selectmode=tk.EXTENDED)
        self.column_listbox.grid(row=1, column=0, sticky='ew')

        self.info_button = tk.Button(self.master, text="Show Description", command=self.show_info)
        self.info_button.grid(row=2, column=0, sticky='ew')

        self.add_button = tk.Button(self.master, text="Add to Graph", command=self.add_column)
        self.add_button.grid(row=3, column=0, sticky='ew')

        self.remove_button = tk.Button(self.master, text="Remove from Graph", command=self.remove_column)
        self.remove_button.grid(row=4, column=0, sticky='ew')

        self.selected_label = tk.Label(self.master, text="Currently Displayed Columns:")
        self.selected_label.grid(row=5, column=0, sticky='w')

        self.selected_listbox = tk.Listbox(self.master, selectmode=tk.EXTENDED)
        self.selected_listbox.grid(row=6, column=0, sticky='ew')

        self.range_label = tk.Label(self.master, text="Simulation Time Range (seconds):")
        self.range_label.grid(row=7, column=0, sticky='w')

        self.range_frame = tk.Frame(self.master)
        self.range_frame.grid(row=8, column=0, sticky='ew')

        self.start_entry = tk.Entry(self.range_frame)
        self.start_entry.pack(side=tk.LEFT)

        self.end_entry = tk.Entry(self.range_frame)
        self.end_entry.pack(side=tk.LEFT)

        self.range_info_label = tk.Label(self.master, text="")
        self.range_info_label.grid(row=9, column=0, sticky='w')

        self.plot_button = tk.Button(self.master, text="Plot Graph", command=self.plot_graph)
        self.plot_button.grid(row=10, column=0, sticky='ew')

        self.quit_button = tk.Button(self.master, text="Quit", command=self.quit_app)
        self.quit_button.grid(row=11, column=0, sticky='ew')

        self.fig, self.ax = plt.subplots()
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.master)
        self.canvas.get_tk_widget().grid(row=999, column=0, sticky='nsew')

    def load_csv(self):
        filepath = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if not filepath:
            return

        try:
            raw = pd.read_csv(filepath, skiprows=[1])
            self.columns_info = {col: "" for col in raw.columns if col != 'Time'}

            raw['Time'] = pd.to_numeric(raw['Time'], errors='coerce')
            raw = raw[raw['Time'].notna()]
            raw.set_index('Time', inplace=True)
            self.data = raw

            self.column_listbox.delete(0, tk.END)
            for col in self.columns_info:
                self.column_listbox.insert(tk.END, col)

            self.filename_label.config(text=f"Selected: {filepath.split('/')[-1]}")

            if not self.data.empty:
                start = self.data.index.min()
                end = self.data.index.max()
                self.start_entry.delete(0, tk.END)
                self.start_entry.insert(0, str(start))
                self.end_entry.delete(0, tk.END)
                self.end_entry.insert(0, str(end))
                self.range_info_label.config(text=f"Simulation time range: {start} sec to {end} sec")
            else:
                self.range_info_label.config(text="No valid simulation time data.")
                messagebox.showwarning("Time Error", "No valid numeric time values found.")

            messagebox.showinfo("Success", f"Loaded {filepath} successfully.")

        except Exception as e:
            messagebox.showerror("Error", str(e))

    def show_info(self):
        sel = self.column_listbox.curselection()
        if sel:
            col_name = self.column_listbox.get(sel[0])
            if col_name in self.columns_info:
                messagebox.showinfo("Description", f"{col_name}: {self.columns_info[col_name]}")

    def add_column(self):
        selections = self.column_listbox.curselection()
        for i in selections:
            col = self.column_listbox.get(i)
            if col and col not in self.selected_columns:
                self.selected_columns.append(col)
                self.selected_listbox.insert(tk.END, col)

    def remove_column(self):
        selections = list(self.selected_listbox.curselection())[::-1]  # reverse to remove safely
        for i in selections:
            col = self.selected_listbox.get(i)
            if col in self.selected_columns:
                self.selected_columns.remove(col)
                self.selected_listbox.delete(i)

    def plot_graph(self):
        if not self.selected_columns:
            messagebox.showwarning("Warning", "Please select columns to display.")
            return

        self.ax.clear()
        try:
            start_time = float(self.start_entry.get())
            end_time = float(self.end_entry.get())
            if start_time >= end_time:
                messagebox.showwarning("Warning", "Start time must be less than end time.")
                return

            df = self.data.loc[start_time:end_time, self.selected_columns]
            df = df.apply(pd.to_numeric, errors='coerce')

            if df.dropna().empty:
                messagebox.showerror("Error", "No numeric data to plot.")
                return

            df.plot(ax=self.ax)
            self.ax.set_title("Graph of Selected Columns")
            self.ax.set_xlabel("Simulation Time (s)")
            self.ax.set_ylabel("Value")
            self.canvas.draw()

        except Exception as e:
            messagebox.showerror("Error", str(e))

    def quit_app(self):
        self.master.quit()
        self.master.destroy()
        sys.exit(0)

def signal_handler(sig, frame):
    print("Exiting...")
    sys.exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    root = tk.Tk()
    app = CSVPlotter(root)
    root.mainloop()
