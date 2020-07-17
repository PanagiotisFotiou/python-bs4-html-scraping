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
# empty_table('organizer')
empty_table('persons')
# begin_productions_scraping()
#begin_actors_scraping()

#scrap_events('https://www.viva.gr/tickets/theater/pollaploi-choroi/den-akouw-de-vlepw-de-milaw')
#scrap_by_production('https://www.viva.gr/tickets/theater/anoigei-avlaia/oloi-mazi-mporoume')

#scrap_persons('https://www.viva.gr/tickets/show/alsos/takis-zaxaratos-zo-gia-sena-summer-edition')
scrap_persons('https://www.viva.gr/tickets/theater/periodeia/art-kalokairini-periodeia')

conn.close()
