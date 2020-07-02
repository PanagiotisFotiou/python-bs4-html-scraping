import requests
from bs4 import BeautifulSoup
import mariadb
import sys
from actors import *
from productions import *
from connect_db import *

# scrap_by_letter()

conn, cursor = connect_to_db()

conn.close()
