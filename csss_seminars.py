"""
Download list of all CSSS Seminars

The HTML over time is irreglar. This still contains errors and does not download abstracts.
"""
import itertools
import csv
import re
import datetime
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from bs4.element import Tag

SEMINAR_ARCHIVE_URL = "http://www.csss.washington.edu/Seminars/archive/{year}/{term}"

WEEKDAYS = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday")
MONTHS = ("January", "February", "March",
          "April", "May", "June",
          "July", "August", "September",
          "October", "November", "December")

def seminar_archive_url(year, term):
    return SEMINAR_ARCHIVE_URL.format(year = year, term = term)


def is_a_seminar(x):
    if re.search("no\s+seminar", x, re.I):
        return False
    elif re.search("TBA", x, re.I):
        return False
    elif re.search("Course Overview", x, re.I):
        return False
    else:
        return True

def is_abstract(x):
    x = x.get_text()
    if re.search(r"request\s*disability\s*accommodations", x, re.I):
        return False
    elif re.search(r"Padelford", x, re.I):
        return False
    else:
        return True

def clean_talk(x):
    x = re.sub('\s+', ' ', re.sub('\n', ' ', x.strip()))
    x = re.sub("(Janurary|Januray)", "January", x)
    x = re.sub(",March", ", March", x)
    x = re.sub(r"\b(Novermber|Nov)\b", "November", x)
    x = re.sub(r"\b(Dec)\b", "December", x)
    x = re.sub(r"(\d)(th|rd|st)", r"\1", x)
    return x

def get_abstract(url):
    r = requests.get(url)
    if r.status_code == 200:
        html = r.text
        m = re.search(r"<!--\s*main\s*content\s*begins\s*-->(.*)" + 
                             r"<!--\s*main\s*content\s*ends\s*-->", html,
                             re.I + re.S + re.M)
        if m:
            soup = BeautifulSoup(m.group(1))
            abstract = '\n\n'.join(x.get_text() for x in soup.find_all('p') if is_abstract(x))
            return abstract
        else:
            soup = BeautifulSoup(html)
            abstract = '\n\n'.join(x.get_text() for x in soup.find_all('p') if is_abstract(x))
            return abstract
        

def parse_talks(x):
    REGEX = re.compile(''.join((r"(?P<dow>%s)" % '|'.join(WEEKDAYS),
                                r"\s*,?\s*(?P<month>%s)" % '|'.join(MONTHS),
                                r"\s*(?P<dom>[0-9]+)",
                                r"\s*,?\s*(?P<year>[0-9]{4})",
                                r"\s*(?P<authors>.*?)\s*\"(?P<title>.*?)\""
                                )))

    m = REGEX.match(x)
    if m:
        return {'weekday': m.group('dow'),
                'month': m.group('month'),
                'day': m.group('dom'),
                'authors': m.group('authors'),
                'title': m.group('title')
                }

# The html is so inconsistent on these pages, its easier just to rip out the text chunks and regex it
# Do the same thing as with the csss papers
def parse_seminar_page(year, term):
    url = seminar_archive_url(year, term)
    print("Geting '%s'" % url)
    r = requests.get(url)
    html = r.text
    html = html.replace('<DT><STRONG><DT><STRONG>', '<DT><STRONG>')
    soup = BeautifulSoup(html, 'html5lib')
    alltalks = []
    talk = ''
    talk_url = ''
    i = 0
    for el in soup.find("dl", class_="indent").children:
        if isinstance(el, Tag):
           if el.name == "dt":
               if i > 0:
                   if is_a_seminar(talk):
                       talk = clean_talk(talk)
                       d = parse_talks(talk)
                       if not d: d = {}
                       d.update({'year': year, 'term': term, 
                                 'talk': talk,
                                 'url': talk_url})
                       if talk_url != '':
                          d['abstract'] = get_abstract(talk_url) 
                       alltalks += [d]
                   talk = ''
                   talk_url = ''
               i += 1
               talk += ' '.join(el.stripped_strings)
           elif el.name == "dd":
               if el.find('a'):
                   talk_url = el.find('a')['href']
                   if re.search(r"s?html?$", talk_url):
                       talk_url = urljoin(url, talk_url)
                   else:
                       talk_url = ''
               talk += ' ' + ' '.join(el.stripped_strings)
    if is_a_seminar(talk):
       talk = clean_talk(talk)
       d = parse_talks(talk)
       if not d: d = {}
       d.update({'year': year, 'term': term, 
                 'talk': talk,
                 'url': talk_url})
       if talk_url != '':
           d['abstract'] = get_abstract(talk_url)       
       alltalks += [d]
    return alltalks

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
    data = get_all_talks()
    dst = "seminars.csv"
    print("Writing to file '%s'" % dst)
    with open(dst, 'w') as f:
        writer = csv.DictWriter(f, ('year', 'term', 'url', 'month', 'day', 'weekday', 'authors', 'title', 'talk', 'abstract'))
        writer.writeheader()
        writer.writerows(data)
    
if __name__ == "__main__":
    main()
    
