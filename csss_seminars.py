"""
Download list of all CSSS Seminars

The HTML over time is irreglar. This still contains errors and does not download abstracts.
"""
import itertools
import csv
import re
import datetime

import requests
from bs4 import BeautifulSoup

SEMINAR_ARCHIVE_URL = "http://www.csss.washington.edu/Seminars/archive/{year}/{term}"

def seminar_archive_url(year, term):
    return SEMINAR_ARCHIVE_URL.format(year = year, term = term)

def get_seminar_page(year, term):
    url = seminar_archive_url(year, term)
    print(url)
    r = requests.get(url)
    return r.text

def parse_seminar_page(year, term):
    html = get_seminar_page(year, term)
    html = re.sub("<DT><STRONG><DT><STRONG>", "<DT><STRONG>", html)
    soup = BeautifulSoup(html)
    talks = []
    for dt in soup.find("dl", class_="indent").findAll("dt"):
        datestr = dt.get_text().strip()
        datestr = re.sub("(Janurary|Januray)", "January", datestr)
        datestr = re.sub(",March", ", March", datestr)
        datestr = re.sub(r"\b(Novermber|Nov)\b", "November", datestr)
        datestr = re.sub(r"\b(Dec)\b", "December", datestr)
        datestr = re.sub(r"(\d)(th|rd|st)", r"\1", datestr)
        print(datestr)
        talkdate = datetime.datetime.strptime(datestr,
                                              "%A, %B %d, %Y")
        dd = dt.find_next_siblings("dd")
        person = dd[0].contents[0]
        try:
            person = person.get_text()
        except AttributeError:
            pass
        hastitle = dd[0].find("a")
        if hastitle:
            title = hastitle.get_text()
            url = hastitle['href']
        else:
            title = ""
            url = ""
        talk = {'date': talkdate.strftime("%Y-%m-%d"),
                'person': person,
                'title': title,
                'url': url,
                'year': year,
                'term': term}
        talks.append(talk)
    return talks

def get_all_talks():
    alltalks = []
    for i in itertools.product((i for i in range(1999, 2015)),
                               ("fall", "winter", "spring")):
        if i not in ((2014, 'fall'),
                     (1999, 'winter'),
                     (1999, 'spring'),
                     (2001, 'winter') #
                     ):
            talks = parse_seminar_page(*i)
            alltalks += talks
    return alltalks

def main():
    dst = "seminars.csv"
    with open(dst, "w") as f:
        print("writing to file '%s'" % dst)
        writer = csv.DictWriter(f, ("year", "term", "date",
                                    "person", "title", "url"))
        writer.writeheader()
        writer.writerows(alltalks)
    
if __name__ == "__main__":
    main()
    
