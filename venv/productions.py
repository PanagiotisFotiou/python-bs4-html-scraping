import requests
from bs4 import BeautifulSoup
import mariadb
import sys
import datetime
import time
import re
from connect_db import *
from urllib.parse import urljoin
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager

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


    organizer_id = scrap_orginizer(url)
    if(organizer_id != 0):
        try:
            cursor.execute("INSERT INTO production (OrganizerID,Title,Description,URL,Production,MediaURL) VALUES (?, ?, ?, ?, ?, ?)",(organizer_id, title, description, url, production_name, media_url))
        except mariadb.Error as e:
            print(f"Database Error: {e}")
    else:
        try:
            cursor.execute("INSERT INTO production (Title,Description,URL,Production,MediaURL) VALUES (?, ?, ?, ?, ?)", (title, description, url, production_name, media_url))
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
        scrap_events(play_url)#scrap events

    fill_venue(venue_titles)

# End of begin_productions_scraping function

def fill_venue(lvenue_titles):
    venue_title_set = set(lvenue_titles)
    lvenue_titles = list(venue_title_set)

    for each_title in lvenue_titles:
        try:
            cursor.execute(
            "INSERT INTO venue (Title) VALUES (?)", (each_title,))
        except mariadb.Error as e:
            print(f"Database Error: {e}")

# End of fill_venue function

def venue_scrap(url):
    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')
    try:
        venue_titles.append(soup.find("a", id="PageContent_PlayDetails_ButtonMap_VenueMapLink").getText().strip())
    except AttributeError as error:
        return

# End of venue_scrap function


def scrap_events(url):
    options = webdriver.ChromeOptions()
    options.add_argument("headless")
    driver = webdriver.Chrome(ChromeDriverManager().install(), chrome_options=options)
    driver.get(url)
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')

    for each_event in soup.find("div", class_="booking-panel-wrap__events-container").find_all("div", class_="events-container__item"):

        date = each_event.find(class_='events-container__item-date').getText()
        unformatted_date = re.findall("\d+/\d+", date)
        formatted_date = ''.join(map(str, unformatted_date)).split("/")
        hour = each_event.find(class_="events-container__item-time").getText()
        now = datetime.datetime.now()
        full_date = f"{now.year}-{formatted_date[1]}-{formatted_date[0]} {hour}"

        price_range = each_event.find("div", class_="events-container__item-prices").getText().strip()

        vanue_full = each_event.find("span", class_="events-container__item-venue").getText().strip()
        vanue_full_list = vanue_full.split("-")
        vanue_title =  vanue_full_list[0].strip()
        vanue_address = vanue_full_list[1].strip()

        cursor.execute(
            "SELECT DISTINCT ID FROM venue WHERE Title=?",
            (vanue_title,))
        row  = cursor.fetchone()

        try:
            venue_id= row[0]
        except TypeError:
            try:
                cursor.execute(
                    "INSERT INTO venue (Title,Address) VALUES (?, ?)", (vanue_title,vanue_address))
                cursor.execute(
                    "SELECT DISTINCT ID FROM venue WHERE Title=?",
                    (vanue_title,))
                row1 = cursor.fetchone()
                venue_id = row1[0]
            except mariadb.Error as e:
                print(f"Database Error: {e}")

        try:
            cursor.execute(
                "SELECT ID FROM production WHERE URL=?",
                (url,))
            row2 = cursor.fetchone()
            production_id = row2[0]
        except mariadb.Error as e:
            print(f"Database Error: {e}")

        try:
            cursor.execute(
                "INSERT INTO events (ProductionID,VenueID,DateEvent,PriceRange) VALUES (?, ?, ?, ?)", (production_id, venue_id, full_date, price_range))
        except mariadb.Error as e:
            print(f"Database Error: {e}")

# End of scrap_events function


def scrap_orginizer(url):
    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')
    try:
        for organizer_desc in soup.find("dt", id="organizer").find_next_siblings('dd'):
            name = organizer_desc.select(".playDetailsContainer > h4")[0].getText()
            address = organizer_desc.find(id="PageContent_PlayDetails_rep_producer_lbl_txtAddress_0").find_next_siblings(class_="field")[0].getText().strip()
            town = organizer_desc.find(id="PageContent_PlayDetails_rep_producer_lbl_txtCity_0").find_next_siblings(class_="field")[0].getText().strip()
            postcode = organizer_desc.find(id="PageContent_PlayDetails_rep_producer_lbl_txtpostCode_0").find_next_siblings(
                class_="field")[0].getText().strip()
            phone = organizer_desc.find(id="PageContent_PlayDetails_rep_producer_lbl_txtphone_0").find_next_siblings(
                class_="field")[0].getText().strip()
            email = organizer_desc.find(id="PageContent_PlayDetails_rep_producer_lbl_txtemail_0").find_next_siblings(
                class_="field")[0].getText().strip()
            doy = organizer_desc.find(id="PageContent_PlayDetails_rep_producer_lbl_txtdoy_0").find_next_siblings(
                class_="field")[0].getText().strip()
            afm = organizer_desc.find(id="PageContent_PlayDetails_rep_producer_lbl_txtvat_0").find_next_siblings(
                class_="field")[0].getText().strip()

            try:
                cursor.execute(
                    "SELECT ID FROM organizer WHERE Afm=?",
                    (afm,))
                row = cursor.fetchone()
                try:
                    id = row[0]
                    return id
                except TypeError:
                    try:
                        cursor.execute(
                            "INSERT INTO organizer (Name,Address,Town,postcode,Phone,Email,Doy,Afm) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (name, address, town, postcode, phone, email, doy, afm))
                        cursor.execute(
                            "SELECT ID FROM organizer WHERE Afm=?",
                            (afm,))
                        row = cursor.fetchone()
                        id = row[0]
                        return id
                    except mariadb.Error as e:
                        print(f"Database Error: {e}")
            except mariadb.Error as e:
                print(f"Database Error: {e}")
    except AttributeError as error:
        return 0

def scrap_persons(url):
    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')
    person_id, production_id, role_id = '','',''


    try:
        search = text=re.compile('Συντελεστές$')
        syntelestes = soup.find("dt", string=search)
        syntelestes_text = syntelestes.findNext('dd').getText()
        # print (syntelestes.findNext('dd').getText())
        for each in re.findall("(.*:){0,} ([A-Za-zΑ-Ωα-ωίϊΐόάέύϋΰήώ]{3,} [A-Za-zΑ-Ωα-ωίϊΐόάέύϋΰήώ]{3,}){1,}", syntelestes_text):
            print (each)
            job = each[0].replace(':', '').strip()
            full_name = each[1].split();
            print(job)
            print(full_name[0])
            print(full_name[1])

            try:
                if job:
                    try:
                        cursor.execute(
                            "INSERT INTO roles (Role) VALUES (?)",
                            (job,))
                        cursor.execute(
                            "SELECT ID FROM roles WHERE Role=?",
                            (job,))
                        row = cursor.fetchone()
                        role_id = row[0]
                    except mariadb.Error as e:
                        print(f"Database Error: {e}")

            except mariadb.Error as e:
                print(f"Database Error: {e}")


            try:
                cursor.execute(
                    "INSERT INTO persons (Firstname,Lastname) VALUES (?, ?)",
                    (full_name[0], full_name[1]))
                cursor.execute(
                    "SELECT ID FROM persons WHERE Firstname=? AND Lastname=?",
                    (full_name[0], full_name[1]))
                row = cursor.fetchone()
                person_id = row[0]
            except mariadb.Error as e:
                print(f"Database Error: {e}")

            try:
                cursor.execute(
                    "SELECT ID FROM production WHERE URL=?",
                    (url,))
                row = cursor.fetchone()
                production_id = row[0]
            except mariadb.Error as e:
                print(f"Database Error: {e}")


            try:
                cursor.execute(
                    "INSERT INTO contributions (PeopleID,ProductionID,RoleID) VALUES (?, ?, ?)",
                    (person_id, production_id, role_id))
            except mariadb.Error as e:
                print(f"Database Error: {e}")

    except AttributeError as error:
        return 0
