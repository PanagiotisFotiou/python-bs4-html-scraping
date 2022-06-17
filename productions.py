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
from tkinter import ttk as ttk
from tkinter import *
from threading import *
from tkinter import messagebox as mb
from textwrap import wrap

conn, cursor = connect_to_db()
conn2, cursor2 = connect_to_db()
venue_titles = []
system_id = ''


class GUI(object):
    def __init__(self, master):
        self.master = master
        # width = master.winfo_screenwidth()
        # height = master.winfo_screenheight()
        # self.master.geometry("%dx%d" % (width, height))
        self.master.title("Python HTML Scraping")
        # p1 = PhotoImage(file='info.png')
        self.master.iconphoto(False, PhotoImage(file='icons\pngwing.png'))
        self.master.configure(bg='#32c1d5')
        # self.master.resizable(0, 0)
        self.Console = Text(master, height=15, width=120)
        self.scroll = Scrollbar(master, borderwidth=50)
        self.scroll.config(command=self.Console.yview)
        self.Console.grid(column=1, row=1, columnspan=2, rowspan=5, padx=(10, 0), sticky=W)
        self.scroll.grid(column=1, row=1, columnspan=2, rowspan=5, sticky=E + N + S)
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

    def dataGridFill(self, tableName):
        try:
            for widget in f2.winfo_children():
                widget.destroy()
            conn2, cursor2 = connect_to_db()
            cursor2.execute("SELECT * FROM " + tableName + " ORDER BY timestamp DESC limit 0,50")
            i = 0
            col = 0
            for row in cursor2.description:
                e = Label(f2, width=15, text=row[0], relief='flat', anchor="w", font='Helvetica 12 bold')
                e.grid(row=i, column=col)
                col = col + 1
            i = i + 1

            for row in cursor2:
                for j in range(len(row)):
                    cellText = row[j]
                    cellTextLimited = str(cellText)[0:25]
                    if len(cellTextLimited) > 24:
                        cellTextLimited += "..."
                    e = Button(f2, width=22, height=2, text=cellTextLimited, borderwidth=2, relief='ridge', anchor="w",
                               bg="white", command=lambda cellText=cellText: clickTableCell(cellText))
                    e.grid(row=i, column=j)
                i = i + 1
        except mariadb.Error as e:
            print(f"Database Error: {e}")


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


def clickTableCell(text):
    toplevel = Toplevel()
    # root.eval(f'tk::PlaceWindow {str(toplevel)} center')
    toplevel.title("Τιμή πεδίόυ")
    toplevel.iconphoto(False, PhotoImage(file='icons\pngwing.png'))
    label1 = Label(toplevel, text=text, bg="white")
    label1.pack(padx=130, pady=30)
    Button(toplevel, text="OK", font=("Helvetica", 10, "bold"), command=lambda: closePopup(toplevel)).pack(pady=20)
    toplevel.update()
    width = label1.winfo_width()
    if width > 600:
        char_width = width / len(text)
        wrapped_text = '\n'.join(wrap(text, 120))
        label1['text'] = wrapped_text
    toplevel.mainloop()


def closePopup(toplevel):
   toplevel.destroy()


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
                hours += 1;

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


def step(num):
    root.update_idletasks()
    pb1['value'] += num


def threading():
    Thread(target=begin_productions_scraping).start()


def threading2(el):
    if el:
        Thread(target=GUI.dataGridFill(app, el.get())).start()


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
                    GUI.write(app,"Εντοπίστηκαν διαφορές στην σελίδα του θεατρικού και εγίναν οι κατάλληλες ενημέρωσεις τιμών")
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
                    GUI.write(app,
                              "Εντοπίστηκαν διαφορές στην σελίδα του θεατρικού και εγίναν οι κατάλληλες ενημέρωσεις τιμών")
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
    conn, cursor = connect_to_db()

    Start(timerLabel)
    url = 'https://www.viva.gr/tickets/theatre/'
    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')
    all_results = soup.find("div", id="play_results").select("article.theater #ItemLink")
    all_results_names_soup = soup.find("div", id="play_results").select("article #ItemLink .playinfo .playinfo__title")
    all_results_names = []
    productionStatus = []
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
            productionStatus.append("Υπάρχον")
            existed += 1
        else:
            productionStatus.append("Νέο")
            new += 1

    GUI.write(app, "Νέα έργα: " + str(new) + "\nΥπάρχοντα έργα: " + str(existed))
    idx = 0
    percentage = 100 / float(len(all_results))

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
        GUI.write(app, str(idx + 1) + "/" + str(len(all_results)) + " --> " + all_results_names[idx] + " (" +
                  productionStatus[idx] + ")")
        play_url = urljoin(url, each_play['href'])
        print("scraping url: " + play_url)
        scrap_by_production(play_url)  # fill production table
        venue_scrap(play_url)  # scrap venue title
        scrap_events(play_url, productionStatus[idx])  # scrap events and venues
        scrap_persons(play_url)  # scrap person including roles and contributions
        getSums()
        step(percentage)
        idx += 1

    conn, cursor = connect_to_db()
    try:
        cursor.execute("UPDATE system SET date=? WHERE ID=?", (datetime.datetime.now(), 2))
    except mariadb.Error as e:
        print(f"Database Error: {e}")
    getLastRun()
    fill_venue(venue_titles)
    btn['state'] = NORMAL
    Stop()
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
        if status == 'Υπάρχον' and new_events > 0:
            GUI.write(app, "Εγίνε προσθήκη " + str(new_events) + " νέων παραστάσεων")
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
                            print("subrole: " + re.sub('\W+',' ', ''.join(subrole)))
                            print("each_name: " + str(each_name))
                            if all(x.isalpha() or x.isspace() for x in each_name) and (len(each_name) == 2) and len(each_name[0]) > 1 and len(each_name[1]) > 1:
                                if (each_name[0][0].isupper()) and (each_name[1][0].isupper()) and (each_name[0][1].islower()) and (each_name[1][1].islower()):
                                    name = ' '.join(each_name)
                                    person_id = insertPersonToDB(name)
                                    insertContributionToDB(url, person_id, role_id, re.sub('\W+',' ', ''.join(subrole)))

                    elif all(x.isalpha() or x.isspace() for x in full_name.split()[:2]) and (len(full_name.split()[:2]) == 2) and len(str(names)) == 1 :  # if full name is 2 words and alphabetical and first letter is Capital
                        if full_name.split()[:2][0][0].isupper() and full_name.split()[:2][1][0].isupper() and full_name.split()[:2][0][1].islower() and full_name.split()[:2][1][0].islower():
                            name = ' '.join(full_name)
                            print("name: " + name)
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
                    print("skipped line: " + line[0])
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


def getSums():
    entryvar1.set(getGetCountFromDB("production"))
    entryvar2.set(getGetCountFromDB("organizer"))
    entryvar3.set(getGetCountFromDB("events"))
    entryvar4.set(getGetActorsFromDB())
    entryvar5.set(getGetCountFromDB("venue"))


def getLastRun():
    try:
        cursor.execute("SELECT date FROM `system` WHERE name='Python'")
        row = cursor.fetchone()
        date = row[0]
    except mariadb.Error as e:
        print(f"Database Error: {e}")
    lastRunFrameLabelText.config(text=date)



titleLabel = Label(root, text="ΣΥΣΤΗΜΑ HTML SCRAPING VIVA.GR", font='Helvetica 16 bold')
titleLabel.grid(column=0, row=0, columnspan=5, pady=(0, 10), sticky=W + E + N + S)
f0 = Frame(root)
f1 = Frame(root)
timerLabelText = Label(f0, text="Χρόνος :")
timerLabel = Label(f0, text="")
btn = Button(f0, text="Ξεκίνα το  Scraping", font='Helvetica 11 bold', command=lambda: threading())
btn1 = Button(f1, text="Συνέχεια", command=lambda: resumeScraping(), font='Helvetica 11 bold')
btn1['state'] = DISABLED
btn11 = Button(f1, text="Πάυση", command=pauseScraping, font='Helvetica 11 bold')
btn11['state'] = DISABLED
btn111 = Button(f1, text="Κλείσιμο", command=ExitApplication, bg='brown', fg='white', font='Helvetica 11 bold')
btn2 = Button(root, text="Άδειασμα Πινάκων", command=deleteTablesConfirm, font='Helvetica 10 bold')
btn3 = Button(root, text="Καθαρισμός", command=lambda: GUI.clearConsole(app))
btn4 = Button(root, text="Ανανέωση Συνόλων", font='Helvetica 11 bold', command=lambda: getSums())
f0.grid(column=0, row=1, pady=(10, 10), padx=(10, 0))
btn.pack(side="left", padx=(0, 6))
timerLabel.pack(side="right", padx=3)
timerLabelText.pack(side="right")
f1.grid(column=0, row=2, pady=(10, 10), padx=(10, 0))
btn1.pack(side="left")
btn111.pack(side="right")
btn11.pack(side="right")
btn2.grid(column=3, row=5, columnspan=2, sticky=W + E + N + S, padx=(10, 10))
btn3.grid(column=2, row=5, sticky=E, padx=(0, 20), pady=(0, 0))
btn4.grid(column=3, row=15, columnspan=2, sticky=W + E + N + S, pady=(10, 10), padx=(10, 10))

detailsFrame = Frame(root, bg="#FFFF99")
lastRunFrameLabelText = Label(detailsFrame, font='Helvetica 10 bold', bg="#FFFF99")
lastRunFrameLabel = Label(detailsFrame, text='Τελευταία επιτυχημένη ολοκλήρωση :', font='Helvetica 10 bold',
                          bg="#FFFF99")
detailsFrame.grid(column=3, row=1, sticky=W + E + N + S, padx=(10, 10), pady=(0, 10))
lastRunFrameLabel.grid(column=3, row=2, sticky=W + E + N + S, padx=(10, 0), pady=(0, 10))
lastRunFrameLabelText.grid(column=4, row=2, sticky=W + E + N + S, padx=(0, 10), pady=(0, 10))

systemLabelHeader = Label(detailsFrame, text='Πληροφορίες συστήματος', font='Helvetica 12 bold underline', bg="#FFFF99")
systemLabelHeader.grid(column=3, row=1, columnspan=2, sticky=W, padx=(10, 10), pady=(10, 10))
systemLabel = Label(detailsFrame, text='System ID : 2', font='Helvetica 10 bold', bg="#FFFF99")
systemLabel.grid(column=3, row=3, columnspan=2, sticky=W, padx=(10, 10), pady=(0, 10))
systemLabel2 = Label(detailsFrame, text='System Name : Python', font='Helvetica 10 bold', bg="#FFFF99")
systemLabel2.grid(column=3, row=4, columnspan=2, sticky=W, padx=(10, 10), pady=(0, 10))

f5 = Frame(root, bg="white")
label = Label(root, text="ΔΕΔΟΜΕΝΑ", font='Helvetica 16 bold')
label.grid(column=0, row=7, columnspan=5, sticky=W + E + N + S, padx=(0, 0), pady=(0, 10))
label2 = Label(f5, text=" Έργα:", bg="white", font='Helvetica 11 bold')
img2 = PhotoImage(file="icons/erga.png")
label2["compound"] = LEFT
label2["image"] = img2
label3 = Label(f5, text=" Διοργανωτές:", bg="white", font='Helvetica 11 bold')
img3 = PhotoImage(file="icons/organizer.png")
label3["compound"] = LEFT
label3["image"] = img3
label4 = Label(f5, text=" Παραστάσεις:", bg="white", font='Helvetica 11 bold')
img4 = PhotoImage(file="icons/tickets.png")
label4["compound"] = LEFT
label4["image"] = img4
label5 = Label(f5, text=" Ηθοποιοί:", bg="white", font='Helvetica 11 bold')
img5 = PhotoImage(file="icons/actor.png")
label5["compound"] = LEFT
label5["image"] = img5
label6 = Label(f5, text=" Θεατρικοί χώροι:", bg="white", font='Helvetica 11 bold')
img6 = PhotoImage(file="icons/venue.png")
label6["compound"] = LEFT
label6["image"] = img6
label7 = Label(f5, text="Σύνολα εγγραφών", font='Helvetica 14 bold underline', bg="white")
label2.grid(column=3, row=10, sticky=W, padx=(10, 10), pady=(0, 10))
label3.grid(column=3, row=11, sticky=W, padx=(10, 10), pady=(0, 10))
label4.grid(column=3, row=12, sticky=W, padx=(10, 10), pady=(0, 10))
label5.grid(column=3, row=13, sticky=W, padx=(10, 10), pady=(0, 10))
label6.grid(column=3, row=14, sticky=W, padx=(10, 10), pady=(0, 10))
label7.grid(column=3, row=9, sticky=W + E + N + S, columnspan=2, padx=(100, 100), pady=(10, 10))
f5.grid(column=3, row=9, sticky=W + E + N + S, padx=(10, 10), pady=(10, 0))

entryvar1, entryvar2, entryvar3, entryvar4, entryvar5 = StringVar(), StringVar(), StringVar(), StringVar(), StringVar()
entry, entry2, entry3, entry4, entry5 = Label(f5, textvariable=entryvar1, font='Helvetica 11 bold', bg="white"), Label(
    f5, textvariable=entryvar2, font='Helvetica 11 bold', bg="white"), Label(
    f5, textvariable=entryvar3, font='Helvetica 11 bold', bg="white"), Label(f5, textvariable=entryvar4,
                                                                             font='Helvetica 11 bold',
                                                                             bg="white"), Label(f5,
                                                                                                textvariable=entryvar5,
                                                                                                font='Helvetica 11 bold',
                                                                                                bg="white")

entry.grid(column=4, row=10, padx=(0, 10), pady=(0, 10))
entry2.grid(column=4, row=11, padx=(0, 10), pady=(0, 10))
entry3.grid(column=4, row=12, padx=(0, 10), pady=(0, 10))
entry4.grid(column=4, row=13, padx=(0, 10), pady=(0, 10))
entry5.grid(column=4, row=14, padx=(0, 10), pady=(0, 10))

f3 = Frame(root)
labelTable = Label(f3, text="Επιλογή Πίνακα :", font='Helvetica 10 bold')
labelTable.pack(side="left", padx=6)
# labelTable.grid(column=0, row=8, sticky=W, padx=(10, 10))
databaseList = ["production", "organizer", "venue", "events", "persons", "roles", "contributions", "changeLog"]
combo = ttk.Combobox(f3, state="readonly", values=databaseList, font=("TkDefaultFont", 14))
combo.current(0)
# combo.grid(column=1, row=8, padx=(10, 10))
formBtn = Button(f3, text="Εμφάνιση", font='Helvetica 10 bold', command=lambda: threading2(combo))
formBtn.pack(side="right")
combo.pack(side="right")
# formBtn.grid(column=2, row=8, padx=(10, 10))

f3.grid(column=0, row=8, sticky=W, padx=(10, 10))
text_area = Canvas(root, width=1250, height=400)
text_area.grid(row=9, column=0, sticky=N + S + E + W, columnspan=3, rowspan=7, padx=(10, 10), pady=(10, 10))

sbVerticalScrollBar = Scrollbar(root, orient=VERTICAL, command=text_area.yview)
sbVerticalScrollBar.grid(column=0, row=9, sticky=N + S + E, columnspan=3, rowspan=7, pady=(10, 23))
sbHorizontalScrollBar = Scrollbar(root, orient=HORIZONTAL, command=text_area.xview)
sbHorizontalScrollBar.grid(column=0, row=9, sticky=S + W + E, columnspan=3, rowspan=7, padx=(10, 0), pady=(0, 10))

text_area.configure(yscrollcommand=sbVerticalScrollBar)
text_area.configure(xscrollcommand=sbHorizontalScrollBar)
text_area.bind('<Configure>', lambda e: text_area.configure(scrollregion=text_area.bbox("all")))
f2 = Frame(text_area)
text_area.create_window((0, 0), window=f2, anchor="nw")
pb1 = ttk.Progressbar(root, orient=HORIZONTAL, length=950, mode='determinate')
pb1.grid(column=1, row=6, columnspan=2, padx=(10, 0) ,pady=(0, 10), sticky=W)

getLastRun()
getSums()
GUI.dataGridFill(app, "production")
root.mainloop()
