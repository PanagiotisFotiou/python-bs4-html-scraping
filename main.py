import requests
from bs4 import BeautifulSoup
import mariadb
import time
import sys
from connect_db import *
#from productions import *


def main():
    conn, cursor = connect_to_db()

    # empty_all_tables()
    # begin_productions_scraping()
    # scrap_by_production('https://www.viva.gr/tickets/theater/pollaploi-horoi/oti-thymamai-hairomai')
    # scrap_events('https://www.viva.gr/tickets/theater/multiple-locations/i-porni-apo-panw')

    conn.close()


if __name__ == '__main__':
    main()



