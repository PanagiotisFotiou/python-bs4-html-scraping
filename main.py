import requests
from bs4 import BeautifulSoup
import mariadb
import sys
from actors import *
from productions import *
from connect_db import *
from tkinter import *

conn, cursor = connect_to_db()

# empty_table('contributions')
# empty_table('events')
# empty_table('production')
# empty_table('organizer')
# empty_table('persons')
# empty_table('roles')
# empty_table('venue')
# empty_table('changeLog')

#begin_productions_scraping()
#scrap_by_production('https://www.viva.gr/tickets/theatre/pallas/trito-stefani')
#scrap_events('https://www.viva.gr/tickets/theater/multiple-locations/i-porni-apo-panw')

window = Tk()
window.title("Python HTML Scraping")
window.geometry('650x400')
btn = Button(window, text="Begin Scraping", command = begin_productions_scraping)
btn.grid(column=1, row=0)
window.mainloop()

conn.close()
