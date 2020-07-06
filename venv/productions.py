import requests
from bs4 import BeautifulSoup
import mariadb
import sys
import datetime
import re
from connect_db import *
from urllib.parse import urljoin

conn, cursor = connect_to_db()

venue_titles = []

def empty_table(table_name):
    try:
        cursor.execute(f"DELETE FROM {table_name};")
    except mariadb.Error as e:
        print(f"Error: {e}")


def scrap_by_production(url):
    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')

    try:
        title = soup.find(id='playTitle').getText().lstrip()
    except AttributeError as error:
        title = ''

    try:
        description = soup.find("div", itemprop="description").getText()
    except AttributeError as error:
        description = ''

    try:
        media_url = urljoin(url, soup.find('div', class_='eventImageContainer').find('img')['src'])
    except AttributeError as error:
        media_url = ''

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
        scrap_by_production(play_url)# fill production table
        venue_scrap(play_url)# scrap venue title

    fill_venue(venue_titles)


# End of begin_productions_scraping function

def fill_venue(lvenue_titles):
    venue_title_set = set(lvenue_titles)
    lvenue_titles = list(venue_title_set)

    empty_table('venue')

    for each_title in lvenue_titles:
        try:
            cursor.execute(
            "INSERT INTO venue (Title) VALUES (?)", (each_title,))
        except mariadb.Error as e:
            print(f"Database Error: {e}")


def venue_scrap(url):
    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')
    try:
        venue_titles.append(soup.find("a", id="PageContent_PlayDetails_ButtonMap_VenueMapLink").getText().strip())
    except AttributeError as error:
        return




def events(url):
    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')
    # for each_event in soup.find("div", class_="booking-panel-wrap__events-container").find_all("div", class_="events-container__item"):
    #     print (each_event)

    date = each_event.find(class_='events-container__item-date').getText()
    unformatted_date = re.findall("\d+/\d+", date)
    formatted_date = ''.join(map(str, unformatted_date)).split("/")
    hour = each_event.find(class_="events-container__item-time").getText()
    now = datetime.datetime.now()
    full_date = f"{now.year}-{formatted_date[1]}-{formatted_date[0]} {hour}"

    #
    # try:
    #     cursor.execute(
    #         "INSERT INTO events (ProductionID,VenueID,DateEvent) VALUES (?, ?, ?)", (792, 33, now2))
    # except mariadb.Error as e:
    #     print(f"Database Error: {e}")

