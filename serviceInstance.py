import time
import random
from pathlib import Path
from productions import begin_productions_scraping
from service import SMWinservice

class PythonCornerExample(SMWinservice):
    _svc_name_ = "HTMLScraperService"
    _svc_display_name_ = "HTML Scraper Service"
    _svc_description_ = "A function that scraps html from viva.gr"

    def start(self):
        self.isrunning = True

    def stop(self):
        self.isrunning = False

    def main(self):
        begin_productions_scraping()

if __name__ == '__main__':
    PythonCornerExample.parse_command_line()

