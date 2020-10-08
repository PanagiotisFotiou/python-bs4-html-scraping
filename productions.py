import string
import requests
from bs4 import BeautifulSoup
import mariadb
import sys
import datetime
import time
import re
import unidecode
from connect_db import *
from urllib.parse import urljoin
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager

conn, cursor = connect_to_db()

venue_titles = []
system_id = ''


def getSystemId(system_id):
    try:
        cursor.execute("SELECT ID FROM `system` WHERE name='Python'")
        row = cursor.fetchone()
        system_id = row[0]
    except mariadb.Error as e:
        print(f"Database Error: {e}")
    return system_id


system_id = getSystemId(system_id)


def empty_table(table_name):
    try:
        cursor.execute(f"DELETE FROM {table_name};")
    except mariadb.Error as e:
        print(f"Error: {e}")


def scrap_by_production(url):
    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')

    try:
        title = soup.find(id='playTitle').getText().strip()
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
    try:
        duration = soup.find(id='PageContent_PlayDetails_UIDuration').getText().replace("Διάρκεια", "").strip()
    except AttributeError as error:
        duration = ''

    production_name = ''
    containers = soup.find_all("div", class_="playDetailsContainer")
    for container in containers:
        if container.find("h4") is not None:
            production_name = container.find("h4").getText()

    try:
        cursor.execute(
            "SELECT ID FROM production WHERE URL=?",
            (url,))
        row = cursor.fetchone()
        try:
            existed_production_id = row[0]
        except TypeError:
            existed_production_id = None
    except mariadb.Error as e:
        print(f"Database Error: {e}")

    organizer_id = scrap_orginizer(url)
    if organizer_id != 0:
        try:
            if existed_production_id is not None:
                print("existed production id")
                cursor.execute(
                    "UPDATE production SET OrganizerID=?, Title=?, Description=?, URL=?, Producer=?, MediaURL=?, Duration=?, SystemID=? WHERE ID=?",
                    (organizer_id, title, description, url, production_name, media_url, duration, system_id, existed_production_id))
            else:
                cursor.execute(
                    "INSERT INTO production (OrganizerID,Title,Description,URL,Producer,MediaURL, Duration,SystemID) VALUES (?, ?, ?, ?, ?, ? ,?,?)",
                    (organizer_id, title, description, url, production_name, media_url, duration, system_id))
        except mariadb.Error as e:
            print(f"Database Error: {e}")
    else:
        try:
            if existed_production_id:
                cursor.execute(
                    "UPDATE production SET  Title=?, Description=?, URL=?, Producer=?, MediaURL=?, Duration=?, SystemID=? WHERE ID=?",
                    (title, description, url, production_name, media_url, duration, system_id, existed_production_id))
            else:
                cursor.execute(
                    "INSERT INTO production (Title,Description,URL,Producer,MediaURL,Duration,SystemID) VALUES (?, ?, ?, ?, ?, ? ,?)",
                    (title, description, url, production_name, media_url, duration, system_id))
        except mariadb.Error as e:
            print(f"Database Error: {e}")


# End of scrap_by_production function


def begin_productions_scraping():
    url = 'https://www.viva.gr/tickets/theatre/'
    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')

    all_results = soup.find("div", id="play_results").select("article #ItemLink")
    for each_play in all_results:
        play_url = urljoin(url, each_play['href'])
        print("scraping url: " + play_url)
        scrap_by_production(play_url)  # fill production table
        #venue_scrap(play_url)  # scrap venue title
        scrap_events(play_url)  # scrap events and venues
        scrap_persons(play_url)  # scrap person including roles and contributions

    #fill_venue(venue_titles)


# End of begin_productions_scraping function

def fill_venue(lvenue_titles):
    venue_title_set = set(lvenue_titles)
    lvenue_titles = list(venue_title_set)

    for each_title in lvenue_titles:
        try:
            cursor.execute(
                "INSERT INTO venue (Title, SystemID) VALUES (?, ?)", (each_title, system_id))
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
    options.add_argument("log-level=3")
    driver = webdriver.Chrome(ChromeDriverManager().install(), chrome_options=options)
    driver.get(url)
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')

    for each_event in soup.find("div", class_="booking-panel-wrap__events-container").find_all("div",
                                                                                               class_="events-container__item"):

        date = each_event.find(class_='events-container__item-date').getText()
        unformatted_date = re.findall("\d+/\d+", date)
        formatted_date = ''.join(map(str, unformatted_date)).split("/")
        hour = each_event.find(class_="events-container__item-time").getText()
        now = datetime.datetime.now()
        full_date = f"{now.year}-{formatted_date[1]}-{formatted_date[0]} {hour}"

        price_range = each_event.find("div", class_="events-container__item-prices").getText().strip()

        vanue_full = each_event.find("span", class_="events-container__item-venue").getText().strip()
        vanue_full_list = vanue_full.split("-")
        vanue_title = vanue_full_list[0].strip()
        vanue_address = vanue_full_list[1].strip()

        cursor.execute(
            "SELECT DISTINCT ID FROM venue WHERE Title=?",
            (vanue_title,))
        row = cursor.fetchone()

        try:
            venue_id = row[0]
        except TypeError:
            try:
                cursor.execute(
                    "INSERT INTO venue (Title,Address, SystemID) VALUES (?, ?, ?)",
                    (vanue_title, vanue_address, system_id))
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
                "SELECT ID FROM events WHERE ProductionID=? AND VenueID=? AND DateEvent=?",
                (production_id, venue_id, full_date))
            row3 = cursor.fetchone()

            try:
                existed_event_id = row3[0]
            except TypeError:
                existed_event_id = None
        except mariadb.Error as e:
            print(f"Database Error: {e}")

        try:
            if existed_event_id is not None:
                print("existed event id")
                cursor.execute(
                    "UPDATE events SET  ProductionID=?, VenueID=?, DateEvent=?, PriceRange=?, SystemID=? WHERE ID=?",
                    (production_id, venue_id, full_date, price_range, system_id, existed_event_id))
            else:
                cursor.execute("INSERT INTO events (ProductionID,VenueID,DateEvent,PriceRange, SystemID) VALUES (?, ?, ?, ?, ?)",
                    (production_id, venue_id, full_date, price_range, system_id))
        except mariadb.Error as e:
            print(f"Database Error: {e}")


# End of scrap_events function


def scrap_orginizer(url):
    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')
    try:
        for organizer_desc in soup.find("dt", id="organizer").find_next_siblings('dd'):
            name = organizer_desc.select(".playDetailsContainer > h4")[0].getText()
            address = \
                organizer_desc.find(id="PageContent_PlayDetails_rep_producer_lbl_txtAddress_0").find_next_siblings(
                    class_="field")[0].getText().strip()
            town = organizer_desc.find(id="PageContent_PlayDetails_rep_producer_lbl_txtCity_0").find_next_siblings(
                class_="field")[0].getText().strip()
            postcode = \
                organizer_desc.find(id="PageContent_PlayDetails_rep_producer_lbl_txtpostCode_0").find_next_siblings(
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
                            "INSERT INTO organizer (Name,Address,Town,postcode,Phone,Email,Doy,Afm, SystemID) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                            (name, address, town, postcode, phone, email, doy, afm, system_id))
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
    person_id, production_id, role_id, subrole = '', '', '', ''
    subrole_flag = 0

    try:
        search = text = re.compile('Συντελεστές$')
        syntelestes = soup.find("dt", string=search)
        syntelestes_text = syntelestes.findNext('dd').getText().strip().replace(u"\xa0", " ")
        # print (syntelestes_text)
        for each in syntelestes_text.split('\n'):
            if len(each) > 0:
                line = each.split(":")
                length = len(line)
                if (length > 1) and (len(line[1]) > 0):
                    job = line[0]
                    full_name = line[1]
                    names = re.split(', |- ', full_name)

                    if (subrole_flag == 1):
                        subrole = line[0]
                        role_id = insertRoletoDb('Ηθοποιός')
                    else:
                        role_id = insertRoletoDb(job)

                    print("job: " + job)

                    if len(names) > 1:
                        for each_name in names:
                            name = each_name.strip()  # .replace(u"\xa0"," ")
                            print("List names: " + name)
                            person_id = insertPersonToDB(name)
                            insertContributionToDB(url, person_id, role_id, subrole)

                    else:
                        name = full_name.strip()  # .replace(u"\xa0", " ")
                        print("name: " + full_name.strip())
                        person_id = insertPersonToDB(name)
                        insertContributionToDB(url, person_id, role_id, subrole)

                elif length == 1 and (len(line[0].split(" ")) < 4):

                    names = re.split(', |- ', line[0])
                    for each_name in names:
                        name = each_name.strip()  # .replace(u"\xa0", " ")
                        if len(name.split(" ")) < 2:
                            subrole_flag = 1
                            continue
                        print("ηθοποιος: " + subrole + " onoma: " + name)
                        role_id = insertRoletoDb('Ηθοποιός')
                        person_id = insertPersonToDB(name)
                        insertContributionToDB(url, person_id, role_id, subrole)
                else:
                    print("skipped line: " + line[0])
    except AttributeError as error:
        return 0


def insertRoletoDb(role):
    cursor.execute(
        "SELECT DISTINCT ID FROM roles WHERE Role=?",
        (role,))
    row = cursor.fetchone()
    try:
        role_id = row[0]
    except TypeError:
        try:
            cursor.execute(
                "INSERT INTO roles (Role, SystemID) VALUES (?, ?)",
                (role, system_id))
            cursor.execute(
                "SELECT DISTINCT ID FROM roles WHERE Role=?",
                (role,))
            row1 = cursor.fetchone()
            role_id = row1[0]
        except mariadb.Error as e:
            print(f"Database Error: {e}")

    return role_id


def insertPersonToDB(fullname):
    cursor.execute(
        "SELECT DISTINCT ID FROM persons WHERE Fullname=?",
        (fullname,))
    row = cursor.fetchone()
    try:
        person_id = row[0]
    except TypeError:
        try:
            cursor.execute(
                "INSERT INTO persons (Fullname,SystemID) VALUES (?, ?)", (fullname, system_id))
            cursor.execute(
                "SELECT ID FROM persons WHERE Fullname=?",
                (fullname,))
            row1 = cursor.fetchone()
            person_id = row1[0]
        except mariadb.Error as e:
            print(f"Database Error: {e}")
    return person_id


def insertContributionToDB(url, person_id, role_id, subrole):
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
            "INSERT INTO contributions (PeopleID,ProductionID,RoleID,subRole,SystemID) VALUES (?, ?, ?, ?, ?)",
            (person_id, production_id, role_id, subrole, system_id))
    except mariadb.Error as e:
        print(f"Database Error: {e}")
