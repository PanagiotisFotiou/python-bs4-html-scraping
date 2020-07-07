import requests
from bs4 import BeautifulSoup
import mariadb
import sys
from actors import *
from productions import *
from connect_db import *

# begin_actors_scraping()

conn, cursor = connect_to_db()


# empty_table('events')
# empty_table('production')
# empty_table('venue')
# begin_productions_scraping()
#begin_actors_scraping()

#events('https://www.viva.gr/tickets/theater/pollaploi-choroi/den-akouw-de-vlepw-de-milaw')

conn.close()
