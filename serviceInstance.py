import string
import requests
from bs4 import BeautifulSoup
import mariadb
import sys
import datetime
import time
import re
import unidecode
import uuid
from connect_db import *
from urllib.parse import urljoin
from selenium import webdriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from textwrap import wrap
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

conn, cursor = connect_to_db()
venue_titles = []
system_id = ''
global sess_id
sess_id = str(uuid.uuid1())

def getSystemId(system_id):
    try:
        cursor.execute("SELECT ID FROM `system` WHERE name='Python'")
        row = cursor.fetchone()
        system_id = row[0]
    except mariadb.Error as e:
        print(f"Database Error: {e}")
    return system_id


system_id = getSystemId(system_id)



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
            production_name = container.find("h4").getText().strip()

    try:
        cursor.execute(
            "SELECT * FROM production WHERE URL=?",
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
                if row[1] != organizer_id or row[2] != title or row[3] != description or row[5] != production_name or row[6] != media_url or row[7] != duration:
                    cursor.execute(
                        "UPDATE production SET OrganizerID=?, Title=?, Description=?, URL=?, Producer=?, MediaURL=?, Duration=?, SystemID=? WHERE ID=?",
                        (organizer_id, title, description, url, production_name, media_url, duration, system_id,
                         existed_production_id))
            else:
                cursor.execute(
                    "INSERT INTO production (OrganizerID,Title,Description,URL,Producer,MediaURL, Duration,SystemID) VALUES (?, ?, ?, ?, ?, ? ,?,?)",
                    (organizer_id, title, description, url, production_name, media_url, duration, system_id))
        except mariadb.Error as e:
            print(f"Database Error: {e}")
    else:
        try:
            if existed_production_id:
                if row[2] != title or row[3] != description or row[5] != production_name or row[6] != media_url or row[7] != duration:
                    cursor.execute(
                        "UPDATE production SET  Title=?, Description=?, URL=?, Producer=?, MediaURL=?, Duration=?, SystemID=? WHERE ID=?",
                        (title, description, url, production_name, media_url, duration, system_id,
                         existed_production_id))
            else:
                cursor.execute(
                    "INSERT INTO production (Title,Description,URL,Producer,MediaURL,Duration,SystemID) VALUES (?, ?, ?, ?, ?, ? ,?)",
                    (title, description, url, production_name, media_url, duration, system_id))
        except mariadb.Error as e:
            print(f"Database Error: {e}")


# End of scrap_by_production function


def begin_productions_scraping():
    conn, cursor = connect_to_db()
    url = 'https://www.viva.gr/tickets/theatre/'
    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')
    all_results = soup.find("div", id="play_results").select("article.theater #ItemLink")
    all_results_names_soup = soup.find("div", id="play_results").select("article #ItemLink .playinfo .playinfo__title")
    all_results_names = []
    productionStatus = []

    for val in all_results_names_soup:
        all_results_names.append(val.text)

    new = 0
    existed = 0
    for each_play in all_results:
        play_url = urljoin(url, each_play['href'])
        try:
            cursor.execute(
                "SELECT ID FROM production WHERE URL=?",
                (play_url,))
            row = cursor.fetchone()
            try:
                existed_production_id = row[0]
            except TypeError:
                existed_production_id = None
        except mariadb.Error as e:
            print(f"Database Error: {e}")
        if existed_production_id is not None:
            productionStatus.append("Υπάρχον")
            existed += 1
        else:
            productionStatus.append("Νέο")
            new += 1

    idx = 0
    percentage = 100 / float(len(all_results))
    conn, cursor = connect_to_db()
    try:
        cursor.execute(
            "INSERT INTO changeLog (EventType, Value) VALUES (?, ?)",
            ('Scraping started!', 'Session ID: ' + sess_id))
    except mariadb.Error as e:
        print(f"Database Error: {e}")

    for each_play in all_results:

        play_url = urljoin(url, each_play['href'])
        scrap_by_production(play_url)  # fill production table
        venue_scrap(play_url)  # scrap venue title
        scrap_events(play_url, productionStatus[idx])  # scrap events and venues
        scrap_persons(play_url)  # scrap person including roles and contributions
        idx += 1

    conn, cursor = connect_to_db()
    try:
        cursor.execute("UPDATE system SET date=? WHERE ID=?", (datetime.now(), 2))
        cursor.execute(
            "INSERT INTO changeLog (EventType, Value) VALUES (?, ?)",
            ('Scraping finished!', 'Session ID: ' + sess_id))
    except mariadb.Error as e:
        print(f"Database Error: {e}")
    fill_venue(venue_titles)

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


def scrap_events(url, status):
    options = FirefoxOptions()
    options.add_argument("--headless")
    driver = webdriver.Firefox(executable_path=r'C:\geckodriver.exe', options=options)
    driver.get(url)
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')

    try:
        new_events = 0
        for each_event in soup.find("div", class_="booking-panel-wrap__events-container").find_all("div",
                                                                                                   class_="events-container__item"):
            date = each_event.find(class_='events-container__item-date').getText()
            unformatted_date = re.findall("\d+/\d+", date)
            formatted_date = ''.join(map(str, unformatted_date)).split("/")
            hour = each_event.find(class_="events-container__item-time").getText().strip()
            now = datetime.now()
            try:
                full_date = f"{now.year}-{formatted_date[1]}-{formatted_date[0]} {hour}"
            except IndexError as error:
                full_date = None

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
                    cursor.execute(
                        "UPDATE events SET  ProductionID=?, VenueID=?, DateEvent=?, PriceRange=?, SystemID=? WHERE ID=?",
                        (production_id, venue_id, full_date, price_range, system_id, existed_event_id))
                else:
                    cursor.execute(
                        "INSERT INTO events (ProductionID,VenueID,DateEvent,PriceRange, SystemID) VALUES (?, ?, ?, ?, ?)",
                        (production_id, venue_id, full_date, price_range, system_id))
                    new_events += 1

            except mariadb.Error as e:
                print(f"Database Error: {e}")
    except AttributeError as error:
        print(f"Attribute Error: {error}")
    driver.close()
    driver.quit()


# End of scrap_events function


def scrap_orginizer(url):
    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')
    try:
        for organizer_desc in soup.find("dt", id="organizer").find_next_siblings('dd'):
            name = organizer_desc.select(".playDetailsContainer > h4")[0].getText().strip()
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
                    cursor.execute(
                        "UPDATE organizer SET Name=?, Address=?, Town=?, postcode=?, Phone=?, Email=?, Doy=?, SystemID=? WHERE ID=?",
                        (name, address, town, postcode, phone, email, doy, afm, system_id, id))
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
    except (AttributeError, IndexError) as error:
        return 0


def scrap_persons(url):
    page = requests.get(url)
    soup_alt = BeautifulSoup(page.content, 'html.parser')
    person_id, production_id, role_id, subrole = '', '', '', ''

    try:
        search = text = re.compile('Συντελεστές$')
        syntelestes = soup_alt.find("dt", string=search)

        for s in syntelestes.parent.select('#organizer, #openMedia, #openShare, h4, dd > dd'):
            s.extract()

        syntelestes_text = syntelestes.findNext('dd').getText().strip().replace(u"\xa0", " ")

        for each in syntelestes_text.split('\n'):
            if len(each) > 0 and len(each) < 150:
                print("len(each): ", len(each))
                each = each.replace('•', ':')
                each = each.replace('|', ':')
                line = each.split(":")
                length = len(line)

                if line[0].strip() == 'Ταυτότητα Παράστασης':
                    continue

                if (length > 1) and (len(line[1].strip()) > 0):#if row has "%:%"
                    job = line[0].strip()
                    full_name = line[1].strip()
                    names = re.split(',|-•&/', full_name)

                    if len(full_name.split()) > 2 and len(' '.join(full_name.split()[2:3])) > 3:
                        subrole = ' '.join(full_name.split()[2:3])

                    if job == 'Πρωταγωνιστούν':
                        role_id = insertRoletoDb('Ηθοποιός')
                    else:
                        role_id = insertRoletoDb(job.strip())
                        if all(x.isupper() or x.isspace() or x == "/" for x in job.strip()) or len(job.strip()) == 0 or all(x.islower() or x.isspace() for x in job.strip()):
                            continue

                    if len(str(names)) > 1:
                        for each_name in names:
                            subrole = each_name.strip().split()[2:3]
                            if re.sub('\W+',' ', ''.join(subrole)).isnumeric() or len(re.sub('\W+',' ', ''.join(subrole).strip())) < 4:
                                subrole = ''
                            each_name = each_name.strip().split()[:2]
                            if all(x.isalpha() or x.isspace() for x in each_name) and (len(each_name) == 2) and len(each_name[0]) > 1 and len(each_name[1]) > 1:
                                if (each_name[0][0].isupper()) and (each_name[1][0].isupper()) and (each_name[0][1].islower()) and (each_name[1][1].islower()):
                                    name = ' '.join(each_name)
                                    person_id = insertPersonToDB(name)
                                    insertContributionToDB(url, person_id, role_id, re.sub('\W+',' ', ''.join(subrole)))

                    elif all(x.isalpha() or x.isspace() for x in full_name.split()[:2]) and (len(full_name.split()[:2]) == 2) and len(str(names)) == 1 :  # if full name is 2 words and alphabetical and first letter is Capital
                        if full_name.split()[:2][0][0].isupper() and full_name.split()[:2][1][0].isupper() and full_name.split()[:2][0][1].islower() and full_name.split()[:2][1][0].islower():
                            name = ' '.join(full_name)
                            person_id = insertPersonToDB(name)
                            insertContributionToDB(url, person_id, role_id, re.sub('\W+',' ', ''.join(subrole)))

                elif length == 1: #and (len(line[0].split(" ")) < 4):
                    names = re.split(',|-•&/', line[0].strip())
                    for each_name in names:
                        subrole = ''
                        name = each_name.split()[:2]

                        if len(each_name.split()) > 2 and len(' '.join(each_name.split()[2:3])) > 3:
                            subrole = str(each_name.split()[2:3])

                        if all(x.isalpha() or x.isspace() for x in each_name.split()[:2]) and (len(name) == 2) and len(name[0]) > 1 and len(name[1]) > 1:
                            if (name[0][0].isupper()) and (name[1][0].isupper()) and (name[0][1].islower()) and (name[1][1].islower()):
                                print("sub role: " + ' '.join(subrole) + " onoma: " + ' '.join(name))
                                role_id = insertRoletoDb('Ηθοποιός')
                                person_id = insertPersonToDB(' '.join(name))
                                insertContributionToDB(url, person_id, role_id, re.sub('\W+',' ', ''.join(subrole)))
            else:
                print("skipped line too many chars")
    except AttributeError as error:
        return 0


def insertRoletoDb(role):
    if all(x.isupper() or x.isspace() or x == "/" for x in role) or len(role) == 0 or all(x.islower() or x.isspace() for x in role):
        return
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
        if row is not None:
            production_id = row[0]
        else:
            return;
    except mariadb.Error as e:
        print(f"Database Error: {e}")

    try:
        try:
            cursor.execute(
                "SELECT ID FROM contributions WHERE PeopleID=? AND ProductionID=? AND RoleID=?",
                (person_id, production_id, role_id))
            row2 = cursor.fetchone()
            try:
                existed_contribution_id = row2[0]
            except TypeError:
                existed_contribution_id = None
        except mariadb.Error as e:
            print(f"Database Error: {e}")

        try:
            if existed_contribution_id is not None:
                print("existed contribution id")
                # cursor.execute(
                #     "UPDATE contributions SET  subRole=?, SystemID WHERE ID=?",
                #     (subrole, system_id))
            else:
                cursor.execute(
                    "INSERT INTO contributions (PeopleID,ProductionID,RoleID,subRole,SystemID) VALUES (?, ?, ?, ?, ?)",
                    (person_id, production_id, role_id, subrole, system_id))
        except mariadb.Error as e:
            print(f"Database Error: {e}")
    except mariadb.Error as e:
        print(f"Database Error: {e}")


def getGetCountFromDB(table):
    try:
        cursor.execute(
            "SELECT COUNT(ID) FROM " + table + ";")
        result = cursor.fetchone()
    except mariadb.Error as e:
        print(f"Database Error: {e}")
    return result


def getGetActorsFromDB():
    try:
        cursor.execute(
            "SELECT DISTINCT COUNT(ID) FROM contributions WHERE RoleID IN (SELECT ID FROM roles WHERE Role='Ηθοποιός')")
        result = cursor.fetchone()
    except mariadb.Error as e:
        print(f"Database Error: {e}")
    return result


conn, cursor = connect_to_db()
try:
    cursor.execute("SELECT date FROM system WHERE ID=2")
    result = cursor.fetchone()
    now = datetime.now()
    last_date = result[0]
    diff = relativedelta(last_date, now)
    tdelta = now - last_date
    diff = tdelta.total_seconds()
    if diff < 86400:
        time.sleep(3600)
    else:
        begin_productions_scraping()
except mariadb.Error as e:
    print(f"Database Error: {e}")


