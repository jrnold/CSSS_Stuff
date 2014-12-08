# -*- coding: utf-8 -*-
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
    x = re.sub(r"[“”]", '"', x)
    x = re.sub("(Assessment of model fit based on incomplete data)",
               '"\1"', x)
    x = re.sub("(Models of Social and Biological Contagion: are Puma shoes some kind of virus\?)",
               '"\1"', x)
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
        else:
            soup = BeautifulSoup(html)
        abstract = '\n\n'.join(x.get_text().strip() for x in soup.find_all('p') if is_abstract(x))
        return abstract        

def parse_talks(x):
    REGEX = re.compile(''.join((r"(?P<dow>%s)" % '|'.join(WEEKDAYS),
                                r"\s*,?\s*(?P<month>%s)" % '|'.join(MONTHS),
                                r"\s*(?P<dom>[0-9]+)",
                                r"\s*,?\s*(?P<year>[0-9]{4})",
                                r"\s*(?P<speakers>.*?)\s*\"(?P<title>.*?)\""
                                )))
    m = REGEX.match(x)
    if m:    
        month = m.group('month')
        day = m.group('dom')
        year = m.group('year')
        date = datetime.datetime.strptime('%s %s %s' % (month, day, year), "%B %d %Y").\
               strftime("%Y-%m-%d")
        return {
                'date': date,
                'speakers': m.group('speakers'),
                'title': m.group('title')
                }
                

# The html is so inconsistent on these pages, its easier just to rip out the text chunks and regex it
# Do the same thing as with the csss papers
def parse_seminar_page(url, year, term):
    print("Geting '%s'" % url)
    r = requests.get(url)
    html = r.text
    html = html.replace('<DT><STRONG><DT><STRONG>', '<DT><STRONG>')
    html = re.sub('<DL CLASS="indent">[\n\r]+<STRONG>Wednesday, April 16, 2014</STRONG>', 
               '<DT><STRONG>Wednesday, April 16, 2014</STRONG></DT>',
                html,
                flags = re.M + re.I + re.DOTALL)
    soup = BeautifulSoup(html, 'html5lib')
    alltalks = []
    talk = ''
    talk_url = ''
    i = 0
    #print(soup.find('dl', class_='indent'))
    for el in soup.find("dl", class_="indent").children:
        if isinstance(el, Tag):
           if el.name == "dt":
               if i > 0:
                   if is_a_seminar(talk):
                       talk = clean_talk(talk)
                       print(talk)
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
    
def winter2001_links():
    url = "http://www.csss.washington.edu/Seminars/archive/2001/winter/"
    print("getting %s" % url)
    r = requests.get(url)
    soup = BeautifulSoup(r.text)
    return [urljoin(url, x.a['href']) for x in soup.ul.find_all("li")]
        
        
def parse_winter2001_page(url):
    print(url)
    r = requests.get(url)
    soup = BeautifulSoup(r.text)
    datestr = soup.h1.string
    m = re.match("Seminar (%s) ([0-9]+)(?:th|rd|st|nd)?\s+([0-9]{4})" % '|'.join(MONTHS),
                 datestr, re.I)
    month = m.group(1)
    day = m.group(2)
    #year = m.groups(3)
    h3 = soup('h3')
    date = datetime.datetime.strptime("%s %s 2001" % (month, day), "%B %d %Y").\
        strftime("%Y-%m-%d")
    speakers = h3[0].get_text()
    title = h3[1].get_text()
    abstract = get_abstract(url)
    return {'date': date, 'year': 2001, 'term': 'winter', 
            'url': url, 'speakers': speakers, 'title': title,
            'abstract': abstract}
            
def get_all_winter2001_talks():
    return [parse_winter2001_page(url) for url in winter2001_links()]

def get_all_talks():
    alltalks = []
    for i in itertools.product((i for i in range(1999, 2015)),
                               ("fall", "winter", "spring")):
        if i not in ((1999, 'winter'),          
                     (1999, 'spring'),
                     (2001, 'winter'),
                     (2014, 'fall')
                     ):
            year = i[0]
            term = i[1]
            url = seminar_archive_url(year, term)
            talks = parse_seminar_page(url, year, term)
            alltalks += talks
    alltalks += parse_seminar_page('http://www.csss.washington.edu/Seminars/', 2014, 'fall')
    alltalks += get_all_winter2001_talks()
    alltalks += parse_seminar_page('http://www.csss.washington.edu/Seminars/archive/2014/spring', 2014, 'fall')
    return alltalks

def main():
    data = get_all_talks()
    dst = "seminars.csv"
    print("Writing to file '%s'" % dst)
    with open(dst, 'w') as f:
        writer = csv.DictWriter(f, ('year', 'term', 'url', 'date', 'speakers', 'title', 'talk', 'abstract'))
        writer.writeheader()
        writer.writerows(data)
    
if __name__ == "__main__":
    main()
    
