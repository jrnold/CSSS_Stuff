"""
Extract metadata for all CSSS and download all files

"""

from bs4 import BeautifulSoup
from bs4.element import Tag
import csv
import os
import os.path
import re
import requests

LOCAL_DIR = "./wp/pdf"

PAPERS_URL = "http://www.csss.washington.edu/Papers/"

Months = ("January", "February", "March",
          "April", "May", "June",
          "July", "August", "September",
          "October", "November", "December", "Feburary")

REGEX = re.compile(r"working paper no\.?\s+(?P<no>[0-9]+)\s+(\s*\(.*\))?(\s*\[.*\])?\s*\"(?P<title>.*)\"(?P<authors>.*)\.?\s+(?P<month>%s)\s*,?\s+(?P<year>[0-9]+)" % '|'.join(Months), re.I)

def parse_paper(x):
    x = re.sub('\s+', ' ', re.sub('\n', ' ', x)).strip()
    m = REGEX.match(x)
    if not m:
        print("ERROR Non match: %s" % x)
    data = {}
    for k in ('no', 'title', 'authors', 'month', 'year'):
        data[k] = m.group(k)
    if data['month'] == "Feburary":
        data['month'] = "February"
    data['url'] = "http://www.csss.washington.edu/Papers/wp%d.pdf" % int(data['no'])
    return data

def get_metadata():
   r = requests.get(PAPERS_URL)
   html = r.text
   soup = BeautifulSoup(html, 'html5lib')
   allpapers = []
   paper = ''
   data = {}
   i = 0
   for el in soup.find("dl", class_="indent").children:
       if isinstance(el, Tag):
          strings = ' '.join(el.stripped_strings)
          if el.name == "dt" and not re.match(r'\d{4}', strings) and not re.match('figure', strings, re.I):
              if i > 0:
                  allpapers.append(parse_paper(paper))
                  paper = ''
              i += 1
              paper += ' '.join(el.stripped_strings)
          elif el.name == "dd":
              paper += ' ' + ' '.join(el.stripped_strings)
   allpapers.append(parse_paper(paper))
   return allpapers

def write_csv(data, dst):
   # Write csv
   print("Writing to file '%s'" % dst)
   with open(dst, 'w') as f:
       writer = csv.DictWriter(f, ('no', 'title', 'authors', 'month', 'year', 'url'))
       writer.writeheader()
       for row in data:
           writer.writerow(row)

def download_papers(data, dst):
    if not os.path.exists(dst):
        print("creating directory '%s'" % dst)
        os.makedirs(dst)
    for paper in data:
        print("downloading %s" % paper['url'])
        r = requests.get(paper['url'])
        with open(os.path.join(dst, os.path.split(paper['url'])[1]), 'wb') as f:
            f.write(r.content)
              
def main():
    data = get_metadata()
    write_csv(data, "papers.csv")
    download_papers(data, "./papers/pdf")

if __name__ == "__main__":
    main()
            
