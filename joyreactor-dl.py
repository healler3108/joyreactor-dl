import requests
import bs4
import os
import re
import urllib
import argparse
import pathlib
import humanize

argparser = argparse.ArgumentParser(description="Download full, hires images from JoyReactor")
argparser.add_argument("--url", "-u", type=str, metavar="URL", default="http://joyreactor.cc", help="URL of the JoyReactor's board")
argparser.add_argument("--output", "-o", type=str, metavar="PATH", default="{}/Downloads".format(pathlib.Path.home()), help="Path to save images")
args = argparser.parse_args()

url = args.url
savepath = args.output

if not os.path.isdir(savepath):
    try:
        os.makedirs(savepath)
    except:
        print("Invalid otput path! Exiting...")

referer = "http://joyreactor.cc/"
useragent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36"

maxskipped = 10
maxerrors = 5

skipped = 0
errors = 0
pages = 0

session = requests.Session()
session.headers.update({"User-Agent": useragent})

response = session.get(url)

if response.status_code != 200:
    print("Error on fetching page! Exiting...")
    exit()

html = bs4.BeautifulSoup(response.content, "html5lib")

currnetpage = html.find_all("span", class_="current")

for pagenumber in currnetpage:
    try:
        pages = int(pagenumber.string)
    except:
        continue

session.headers.update({"Referer": referer})

url = url.replace("/{}".format(pages), "")

for page in range(pages, 1, -1):
    response = session.get(url + "/{}".format(page))

    if response.status_code != 200:   
        print("Error on opening page! Exiting...")
        exit()
    
    html = bs4.BeautifulSoup(response.content, "html5lib")

    divs = html.find_all("div", class_="image")

    imglist = []

    for div in divs:
        for tag in div.contents:
            if tag.name == "img":
                img = tag['src']
                imglist.append(img)

            if tag.name == "a":
                img = tag['href']
                imglist.append(img)

            if tag.name == "span":
                for tag in tag.contents:
                    if tag.name == "a":                                                
                        img = tag['href']
                        imglist.append(img)

    for img in imglist:
        if skipped >= maxskipped:
            print("Too much skipped files, perhaps all files has been downloaded. Exiting...")
            exit()
        if errors >= maxerrors:
            print("Too much errors. Exiting...")
            exit()

        imgunquoted = urllib.parse.unquote(img)
        imgfilename = imgunquoted.split("/")[-1]

        imgfilename = re.sub('[^A-Za-zА-Яа-я0-9-.()]+', "", imgfilename)
        imgfilename = imgfilename.replace("()", "")
        imgfilename = re.sub('-{2,}', "-", imgfilename)
        imgfilename = imgfilename.replace('-.', '.')
        if imgfilename[0] == "-":
            imgfilename = imgfilename[1:]

        print("{} - ".format(imgfilename), end="")

        if os.path.isfile("{}/{}".format(savepath, imgfilename)):
            print("SKIPPED")
            skipped += 1
            continue

        try:
            imgfile = session.get(img)
        except:
            print("ERROR")
            errors += 1
            continue
        
        if imgfile.status_code == 200:            
            try:
                open("{}/{}".format(savepath, imgfilename), "wb").write(imgfile.content)
            except:
                print("ERROR")
                errors += 1
                continue
            
            imgfilesize = humanize.naturalsize(imgfile.headers['content-length'])
            print(imgfilesize)

            if skipped != 0:
                skipped = 0
        else:
            print("ERROR")
            errors += 1
            continue