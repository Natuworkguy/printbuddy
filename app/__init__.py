import os
import sys

import serial
import threading
import tkinter as tk
import tkinter.messagebox

from tkinter import ttk
from colorama import Fore, Style, init as colorama_init
from _tkinter import TclError
from typing import Optional

from .resource_path import resource_path

colorama_init(autoreset=False)

class App:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("PrintBuddy")
        self.root.geometry("1280x720")

        try:
            self.root.iconphoto(True, tk.PhotoImage(file=os.path.join(resource_path("data"), "icon.png")))
        except TclError as e:
            tkinter.messagebox.showwarning("Warning", "Could not load icon. Continuing without.")

        self.run_loop = True
        self.connected = False

        self.log_window = None
        self.commands_list = None
        self.command = None
        self.ser = None

        self.connection_section = ttk.LabelFrame(self.root, text="Connection")
        self.connection_section.pack(padx=5, pady=5)

        self.serial_port_label = ttk.Label(self.connection_section, text="Not connected", foreground="red")
        self.serial_port_label.pack(padx=10, pady=5)

        self.connection_section_separator = ttk.Separator(self.connection_section)
        self.connection_section_separator.pack(padx=5, pady=5, expand=True, fill="both")

        self.connection_input = ttk.Entry(self.connection_section)
        self.connection_input.pack(padx=5, pady=5)

        self.connection_submit = ttk.Button(self.connection_section, text="Connect", command=lambda: self.open_connection(self.connection_input.get()))
        self.connection_submit.pack(padx=5, pady=5)

        self.console_section = ttk.LabelFrame(self.root, text="Console")
        self.console_section.pack(padx=5, pady=5)

        self.command_input = ttk.Entry(self.console_section, state="disabled")
        self.command_input.bind("<Return>", self.send_command)
        self.command_input.bind("<Left>", self.restore_command)
        self.command_input.pack(padx=5, pady=5)

        self.send_command_button = ttk.Button(self.console_section, text="Send", command=self.send_command, state="disabled")
        self.send_command_button.pack(padx=5, pady=5)

        self.console_section_separator = ttk.Separator(self.console_section)
        self.console_section_separator.pack(padx=5, pady=7, expand=True, fill="both")

        self.log_button = ttk.Button(self.console_section, text="Show Log", command=self.show_log, state="disabled")
        self.log_button.pack(padx=5, pady=5)

    def open_connection(self, port: str) -> None:
        try:
            self.ser = serial.Serial(port, 115200, timeout=1)  
        except serial.SerialException as e:
            tkinter.messagebox.showerror("Error", f"Could not open serial port: {e}")
            return

        self.connection_input.config(state="disabled")
        self.connection_submit.config(state="disabled")

        self.command_input.config(state="normal")
        self.send_command_button.config(state="normal")
        self.log_button.config(state="normal")

        self.serial_port_label.config(text=f"Connected to: PORT.{port}")
        self.serial_port_label.config(foreground="green")

    def show_log(self) -> None:
        self.log_window = tk.Toplevel(self.root)
        self.log_window.wm_title("PrintBuddy Log")
        self.log_window.wm_resizable(True, True)
        self.log_window.attributes('-topmost', True)

        self.commands_list = tk.Listbox(self.log_window, height=5, selectmode=tk.SINGLE)
        self.commands_list.pack(padx=5, pady=5, expand=True, fill="both")

        def copy_log() -> None:
            if self.commands_list is None:
                return

            log = str()

            for item in self.commands_list.get(0, tk.END):
                log += item + '\n'

            try:
                self.root.clipboard_clear()
                self.root.clipboard_append(log)
            except Exception as e:
                tkinter.messagebox.showerror("Error", f"Failed to copy: {e}")
                return

            tkinter.messagebox.showinfo("Success", "Log copied!")

        self.copy_button = ttk.Button(self.log_window, text="Copy Log", command=copy_log)
        self.copy_button.pack(padx=5, pady=7)

    def restore_command(self, event = None) -> None:
        if self.command is None:
            return

        self.command_input.delete(0, tk.END)
        self.command_input.insert(0, self.command)

    def write_to_cl(self, data: str) -> None:
        if self.commands_list is not None:
            try:
                self.commands_list.insert(tk.END, data) 
                self.commands_list.yview('scroll', 1, 'units')
            except TclError:
                pass

    def send_command(self, event = None) -> None:
        self.command = self.command_input.get()
        self.send_command_raw(self.command)

    def send_command_raw(self, command: Optional[str]) -> None:
        if command is None:
            return

        if self.ser is None:
            return

        self.command_input.delete(0, tk.END)

        try:
            self.ser.write(bytes(command + '\n', 'utf-8'))
        except serial.SerialException as e:
            tkinter.messagebox.showerror("Error", f"Unable to write to serial: {e}")

            self.serial_port_label.config(text="Unable to write")
            self.serial_port_label.config(foreground="red")
            self.command_input.config(state="disabled")
            self.send_command_button.config(state="disabled")

            return

        self.write_to_cl(f"> {self.command}")

    def loop(self) -> None:
        while self.run_loop:
            if self.ser is None:
                continue

            try:
                data = self.ser.readline().decode('utf-8').strip()
            except serial.SerialException as e:  
                tkinter.messagebox.showerror("Error", f"ERROR: Serial communication error. {e}")
                self.run_loop = False

                break
            except UnicodeDecodeError as e:
                print(f"{Fore.YELLOW}Error when reading serial: \"{e}\"\nContinuing.{Style.RESET_ALL}")
                continue

            if data != '':
                self.write_to_cl(data)

    def on_exit(self) -> None:
        self.run_loop = False

        self.send_command("M84")
        print("Sent M84")

        if self.ser is not None:
            try:
                self.ser.close()
            except serial.SerialException as e:
                print(f"{Fore.RED}ERROR: Could not close serial port. {e}{Style.RESET_ALL}")

        self.root.quit()
        sys.exit()

    def run(self) -> None:
        self.loop_thread = threading.Thread(target=self.loop)  
        self.loop_thread.start() 
        self.root.protocol("WM_DELETE_WINDOW", self.on_exit)

        self.root.mainloop()
