import tkinter as tk


class Menu(tk.Menu):
    root: PLC


class PLC(tk.Tk):
    menu = Menu