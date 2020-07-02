import requests
from bs4 import BeautifulSoup
import mariadb
import sys
from connect_db import *

conn, cursor = connect_to_db()

def test():
    print ('123')