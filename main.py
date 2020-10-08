import requests
from bs4 import BeautifulSoup
import mariadb
import sys
from actors import *
from productions import *
from connect_db import *

# begin_actors_scraping()

conn, cursor = connect_to_db()

empty_table('events')
empty_table('venue')
empty_table('production')
empty_table('organizer')
empty_table('contributions')
empty_table('persons')
empty_table('roles')


begin_productions_scraping()
#begin_actors_scraping()

#scrap_persons('https://www.viva.gr/tickets/theatre/pallas/trito-stefani')
#scrap_persons('https://www.viva.gr/tickets/theater/theatro-attis/nora')

#scrap_by_production('https://www.viva.gr/tickets/theater/multiple-locations/i-porni-apo-panw')
#scrap_events('https://www.viva.gr/tickets/theater/multiple-locations/i-porni-apo-panw')

conn.close()
