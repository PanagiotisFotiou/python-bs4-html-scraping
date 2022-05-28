import requests
import time
import sys
import productions
from tkinter import *

class GUI(object):
    def __init__(self, master):
        self.master = master
        self.Console = Text(master)
        self.master.title("Python HTML Scraping")
        self.master.geometry('650x400')
        self.btn = Button(master, text="Begin Scraping", command=productions.begin_productions_scraping)
        self.btn2 = Button(master, text="Empty All DB Tables", command=productions.empty_all_tables)
        self.btn.grid(column=0, row=0)
        self.btn2.grid(column=0, row=1)
        self.Console.grid(column=0, row=2)

    def quit(self):
        self.master.destroy()

    def write(self, *message, end="\n", sep=" "):
        text = ""
        for item in message:
            text += "{}".format(item)
            text += sep
        text += end
        self.Console.insert(INSERT, text)


