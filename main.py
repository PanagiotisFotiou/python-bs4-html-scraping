import requests
from bs4 import BeautifulSoup
import mariadb
import sys
from actors import *
from productions import *
from connect_db import *

# begin_actors_scraping()

conn, cursor = connect_to_db()

#empty_table('production')
#begin_productions_scraping()
#begin_actors_scraping()
events('https://www.viva.gr/tickets/theater/theatro-ivi/opoios-thelei-na-horisei-na-sikosei-to-heri-tou/')


conn.close()
