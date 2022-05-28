import requests
from bs4 import BeautifulSoup
import mariadb
import sys
from connect_db import *

conn, cursor = connect_to_db()

# Empty persons table
def empty_persons_table():
    try:
        cursor.execute("DELETE FROM persons;")
    except mariadb.Error as e:
        print(f"Error: {e}")

def scrap_by_pagination(url):
    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')

    # Fill persons table
    person_fullname = []
    for each_div in soup.find_all("h4", class_="people-item__name"):
        person_fullname = each_div.get_text().split()
        # print(person_fullname)

        if len(person_fullname) == 2:
            cursor.execute(
            "INSERT INTO persons (Firstname,Lastname) VALUES (?, ?)", (person_fullname[0], person_fullname[1]))

    # Find if there is next page in pagination
    next_page_li = soup.find_all("li", class_="page-item")[-1]
    if "disabled" in next_page_li['class']:
        print("Last page crawled end of function")
    else:
        next_page_a = next_page_li.find('a')
        next_page_url = next_page_a['href']
        scrap_by_pagination(next_page_url)

# End of scrap_by_pagination function


def begin_actors_scraping():
    greek_letters = ['%CE%91', '%CE%92', '%CE%93', '%CE%94', '%CE%95', '%CE%96', '%CE%97', '%CE%98', '%CE%99', '%CE%9A', '%CE%9B', '%CE%9C', '%CE%9D', '%CE%9E', '%CE%9F', '%CE%A0', '%CE%A1', '%CE%A3', '%CE%A4', '%CE%A5', '%CE%A6', '%CE%A7', '%CE%A8']
    for each_letter in greek_letters:
        scrap_by_pagination('https://www.unstage.gr/sintelestes?letter='+each_letter)

# End of begin_actors_scraping function