import requests
from bs4 import BeautifulSoup
import mariadb
import sys
from connect_db import *
from urllib.parse import urljoin

conn, cursor = connect_to_db()

def empty_production_table():
    try:
        cursor.execute("DELETE FROM production;")
    except mariadb.Error as e:
        print(f"Error: {e}")

def scrap_by_production(url):
    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')

    title = soup.find(id='playTitle').getText().lstrip()

    try:
        description = soup.find("div", itemprop="description").getText()
    except AttributeError as error:
        description = ''

    media_url = urljoin(url, soup.find('div', class_='eventImageContainer').find('img')['src'])
    production_name = ''
    containers = soup.find_all("div", class_="playDetailsContainer")
    for container in containers:
        if container.find("h4") is not None:
            production_name = container.find("h4").getText()
    try:
        cursor.execute(
        "INSERT INTO production (Title,Description,URL,Production,MediaURL) VALUES (?, ?, ?, ?, ?)", (title, description, url, production_name, media_url))
    except mariadb.Error as e:
        print(f"Database Error: {e}")

# End of scrap_by_production function


def begin_productions_scraping():
    url = 'https://www.viva.gr/tickets/theatre/'
    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')

    all_results = soup.find("div", id="play_results").select("article #ItemLink")
    for each_play in all_results:
        play_url = urljoin(url,each_play['href'])
        scrap_by_production(play_url)

# End of begin_productions_scraping function

