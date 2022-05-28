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
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from tkinter import *
from threading import *
from tkinter import messagebox as mb

conn, cursor = connect_to_db()
venue_titles = []
system_id = ''


class GUI(object):
    def __init__(self, master):
        self.master = master
        self.master.title("Python HTML Scraping")
        # self.master.geometry('900x400')
        self.master.resizable(0, 0)
        self.Console = Text(master, height=15, width=100)
        self.scroll = Scrollbar(master, borderwidth=50)
        self.scroll.config(command=self.Console.yview)
        self.Console.grid(column=0, row=1, columnspan=2, rowspan=5, padx=(10, 0))
        self.scroll.grid(column=1, row=1, sticky=N + S + E, rowspan=5)
        self.Console.config(state=DISABLED)

    def quit(self):
        self.master.destroy()

    def write(self, *message, end="\n", sep=" "):
        self.Console.config(state=NORMAL)
        text = ""
        for item in message:
            text += "{}".format(item)
            text += sep
        text += end
        self.Console.insert(INSERT, text)
        self.Console.see("end")
        self.Console.config(state=DISABLED)

    def clearConsole(self):
        self.Console.config(state=NORMAL)
        self.Console.delete('1.0', END)
        self.Console.config(state=DISABLED)


root = Tk()
app = GUI(root)
var = IntVar()


def ExitApplication():
    res = mb.askquestion('Κλείσιμο εφαρμογής', 'Είστε σίγουροι;')
    if res == 'yes':
        root.destroy()


def deleteTablesConfirm():
    res = mb.askquestion('Διαγραφή πινάκων', 'Είστε σίγουροι;')
    if res == 'yes':
        empty_all_tables()


sec = -1
run = False
minute = 0
hours = 0


def var_name(timerLabel):
    def value():
        if run:
            global sec
            global minute
            global hours
            if sec == -1:
                show = ""
            else:
                show = str(' %d : %d : %d ' % (hours, minute, sec))
            timerLabel['text'] = show
            timerLabel.after(1000, value)
            sec += 1
            if (sec == 60):
                sec = 0
                minute += 1
            if (minute == 60):
                minute = 0
                hour += 1;

    value()


# While Running

def Start(timerLabel):
    global run
    run = True
    var_name(timerLabel)


# While stopped
def Stop():
    global run
    run = False


# For Reset
def Reset(label):
    global count
    count = -1


def threading():
    t1 = Thread(target=begin_productions_scraping)
    t1.start()


pause_status = 0


def getPauseStatus():
    global pause_status
    return pause_status


def setPauseStatus(num):
    global pause_status
    pause_status = num


def pauseScraping():
    GUI.write(app, "Έχει σταλεί αίτημα για πάυση της λειτουργίας scraping")
    setPauseStatus(1)
    btn11['state'] = DISABLED


def resumeScraping():
    btn11['state'] = NORMAL
    var.set(1)
    Start(timerLabel)


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


def empty_all_tables():
    empty_table('contributions')
    empty_table('events')
    empty_table('production')
    empty_table('organizer')
    empty_table('persons')
    empty_table('roles')
    empty_table('venue')
    empty_table('changeLog')
    GUI.write(app, "Όλοι οι πίνακες έχουν καθαριστεί!")


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
    btn['state'] = DISABLED
    btn4['state'] = DISABLED
    btn11['state'] = NORMAL
    Start(timerLabel)
    url = 'https://www.viva.gr/tickets/theatre/'
    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')
    all_results = soup.find("div", id="play_results").select("article.theater #ItemLink")
    all_results_names_soup = soup.find("div", id="play_results").select("article #ItemLink .playinfo .playinfo__title")
    all_results_names = []
    GUI.write(app, "Σύνολο έργων: " + str(len(all_results)))

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
            existed += 1
        else:
            new += 1

    GUI.write(app, "Νέα έργα: " + str(new) + "\nΥπάρχοντα έργα: " + str(existed))
    idx = 0
    for each_play in all_results:
        if getPauseStatus() == 1:
            GUI.write(app, "Η λειτουργία scraping βρίσκεται σε παυσή.")
            btn1['state'] = NORMAL
            btn4['state'] = NORMAL
            Stop()
            btn1.wait_variable(var)
            GUI.write(app, "Συνέχεια λειτουργίας...")
            setPauseStatus(0)
            btn1['state'] = DISABLED
            btn4['state'] = DISABLED
            btn11['state'] = NORMAL
        GUI.write(app, str(idx + 1) + "/" + str(len(all_results)) + " --> " + all_results_names[idx])
        idx += 1
        play_url = urljoin(url, each_play['href'])
        print("scraping url: " + play_url)
        scrap_by_production(play_url)  # fill production table
        venue_scrap(play_url)  # scrap venue title
        scrap_events(play_url)  # scrap events and venues
        scrap_persons(play_url)  # scrap person including roles and contributions

    fill_venue(venue_titles)
    btn['state'] = NORMAL
    Stop()
    getSums()
    GUI.write(app, "Η διαδικασία ολοκληρώθηκε!")


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
    options = FirefoxOptions()
    options.add_argument("--headless")
    driver = webdriver.Firefox(executable_path=r'C:\geckodriver.exe', options=options)
    driver.get(url)
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')

    try:
        for each_event in soup.find("div", class_="booking-panel-wrap__events-container").find_all("div",
                                                                                                   class_="events-container__item"):
            date = each_event.find(class_='events-container__item-date').getText()
            unformatted_date = re.findall("\d+/\d+", date)
            formatted_date = ''.join(map(str, unformatted_date)).split("/")
            hour = each_event.find(class_="events-container__item-time").getText().strip()
            now = datetime.datetime.now()
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
                    print("existed event id")
                    cursor.execute(
                        "UPDATE events SET  ProductionID=?, VenueID=?, DateEvent=?, PriceRange=?, SystemID=? WHERE ID=?",
                        (production_id, venue_id, full_date, price_range, system_id, existed_event_id))
                else:
                    cursor.execute(
                        "INSERT INTO events (ProductionID,VenueID,DateEvent,PriceRange, SystemID) VALUES (?, ?, ?, ?, ?)",
                        (production_id, venue_id, full_date, price_range, system_id))
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
    soup = BeautifulSoup(page.content, 'html.parser')
    person_id, production_id, role_id, subrole = '', '', '', ''
    subrole_flag = 0

    try:
        search = text = re.compile('Συντελεστές$')
        syntelestes = soup.find("dt", string=search)
        syntelestes_text = syntelestes.findNext('dd').getText().strip().replace(u"\xa0", " ")
        for each in syntelestes_text.split('\n'):
            if len(each) > 0 and len(each) < 150:
                print("len(each): ", len(each))
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
                            print("len(names)", len(names))
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


def getSums():
    entryvar1.set(getGetCountFromDB("production"))
    entryvar2.set(getGetCountFromDB("organizer"))
    entryvar3.set(getGetCountFromDB("events"))
    entryvar4.set(getGetActorsFromDB())
    entryvar5.set(getGetCountFromDB("venue"))


f0 = Frame(root)
f1 = Frame(root)
timerLabelText = Label(f0, text="Χρόνος :")
timerLabel = Label(f0, text="")
btn = Button(f0, text="Ξεκίνα το  Scraping", command=lambda: threading())
btn1 = Button(f1, text="Συνέχεια", command=lambda: resumeScraping())
btn1['state'] = DISABLED
btn11 = Button(f1, text="Πάυση", command=pauseScraping)
btn11['state'] = DISABLED
btn111 = Button(f1, text="Κλείσιμο", command=ExitApplication, bg='brown', fg='white')
btn2 = Button(root, text="Άδειασμα Πινάκων", command=deleteTablesConfirm)
btn3 = Button(root, text="Καθαρισμός", command=lambda: GUI.clearConsole(app))
btn4 = Button(root, text="Ανανέωση Συνόλων", command=lambda: getSums())
f0.grid(column=0, row=0, pady=(10, 10))
btn.pack(side="left", padx=6)
timerLabel.pack(side="right", padx=3)
timerLabelText.pack(side="right")
f1.grid(column=1, row=0, pady=(10, 10))
btn1.pack(side="left")
btn111.pack(side="right")
btn11.pack(side="right")
btn2.grid(column=1, row=6, sticky=E, pady=(10, 10))
btn3.grid(column=0, row=6, sticky=W, padx=(10, 0), pady=(10, 10))
btn4.grid(column=2, row=6, columnspan=2, pady=(10, 10))

label = Label(root, text="ΣΥΝΟΛΑ", font='Helvetica 16 bold')
label.grid(column=2, row=0, columnspan=2)
label2 = Label(root, text="Έργα:")
label3 = Label(root, text="Διοργανωτές:")
label4 = Label(root, text="Παραστάσεις:")
label5 = Label(root, text="Ηθοποιοί:")
label6 = Label(root, text="Θεατρικοί χώροι:")
label2.grid(column=2, row=1, sticky=W, padx=(10, 10))
label3.grid(column=2, row=2, sticky=W, padx=(10, 10))
label4.grid(column=2, row=3, sticky=W, padx=(10, 10))
label5.grid(column=2, row=4, sticky=W, padx=(10, 10))
label6.grid(column=2, row=5, sticky=W, padx=(10, 10))

entryvar1, entryvar2, entryvar3, entryvar4, entryvar5 = StringVar(), StringVar(), StringVar(), StringVar(), StringVar()
entry, entry2, entry3, entry4, entry5 = Label(root, textvariable=entryvar1), Label(root, textvariable=entryvar2), Label(
    root, textvariable=entryvar3), Label(root, textvariable=entryvar4), Label(root, textvariable=entryvar5)

entry.grid(column=3, row=1, padx=(0, 10))
entry2.grid(column=3, row=2, padx=(0, 10))
entry3.grid(column=3, row=3, padx=(0, 10))
entry4.grid(column=3, row=4, padx=(0, 10))
entry5.grid(column=3, row=5, padx=(0, 10))
getSums()

root.mainloop()
