# OM Ganesha
# Srikanth Bemineni
# srikanth.bemineni@gmail.com

import requests
import argparse
import xml.etree.ElementTree as ET
import random
import threading
import concurrent.futures
import csv
import uuid
import json
import re
import sys
from datetime import datetime


random.seed()
thread_dict = {}
thread_dict_lock = threading.Lock()

foDict = {}

zipToFOzipDict = {}

USPS_userid = ''

monthtoNum = {"january": 1,
              "february": 2,
              "march": 3,
              "april": 4,
              "may": 5,
              "june": 6,
              "july": 7,
              "august": 8,
              "september": 9,
              "october": 10,
              "november": 11,
              "december": 12}


def getFO(zip):
    try:
        response = requests.get(
            "https://api.uscis.gov/field-officelocator-api/{zip}?apikey=6O7RG2xrwAtjCCzrJaGYJGkvad9zqDBb".format(zip=zip))
        # print(response)
        response.raise_for_status()
        # print(response.content)  # Return the raw bytes of the data payload
        # print(response.text)  # Return a string representation of the data payload

        return response.json()

    except requests.exceptions.HTTPError as errh:
        print(errh)
    except requests.exceptions.ConnectionError as errc:
        print(errc)
    except requests.exceptions.Timeout as errt:
        print(errt)
    except requests.exceptions.RequestException as err:
        print(err)

    return None


def getFieldOffice(zip):
    if zip in zipToFOzipDict:
        if zipToFOzipDict[zip] in foDict:
            FO = foDict[zipToFOzipDict[zip]]
            return FO['localName'] + " " + FO['state'] + " " + FO['zipCode']

    # Lets find the FO for this zip from USCIS
    fojson = getFO(zip)
    if fojson:
        if fojson['localOfficeInfo']['zipCode'] in foDict:
            # Field office information is already in the DB, only the zip to Field office reference is missing
            zipToFOzipDict[zip] = fojson['localOfficeInfo']['zipCode']
        else:
            foDict[fojson['localOfficeInfo']['zipCode']
                   ] = fojson['localOfficeInfo'].copy()
            zipToFOzipDict[zip] = fojson['localOfficeInfo']['zipCode']

        FO = fojson['localOfficeInfo']
        return FO['localName'] + " " + FO['state'] + " " + FO['zipCode']

    return "No zip in DB"


def justCheckandPrint(trackid):
    xml = '<TrackRequest USERID="{user_id}">'.format(user_id=USPS_userid)
    xml = xml + '<TrackID ID="{track}"></TrackID>'.format(track=trackid)
    xml = xml + '</TrackRequest>'

    try:
        response = requests.get(
            "https://secure.shippingapis.com/ShippingAPI.dll?API=TrackV2&XML={trackrequest}".format(trackrequest=xml))
        response.raise_for_status()
        # print(response.content)

        root = ET.fromstring(response.content)
        ET.indent(root)
        print(ET.tostring(root, encoding='unicode'))

    except requests.exceptions.HTTPError as errh:
        print(errh)
    except requests.exceptions.ConnectionError as errc:
        print(errc)
    except requests.exceptions.Timeout as errt:
        print(errt)
    except requests.exceptions.RequestException as err:
        print(err)


def getTrackingdetails(uspsids):
    xml = '<TrackRequest USERID="{user_id}">'.format(user_id=USPS_userid)
    for key in uspsids:
        xml = xml + '<TrackID ID="{track}"></TrackID>'.format(track=key)
    xml = xml + '</TrackRequest>'
    try:
        response = requests.get(
            "https://secure.shippingapis.com/ShippingAPI.dll?API=TrackV2&XML={trackrequest}".format(trackrequest=xml))
        response.raise_for_status()

        root = ET.fromstring(response.content)
        for trackinfo in root.findall('TrackInfo'):
            # print(trackinfo.attrib['ID'])
            ts = trackinfo.find('TrackSummary')
            if ts is not None:
                match = re.search(".*, (\w\w) (\d*).", ts.text)
                if match:
                    # fill up the row with the FO details
                    uspsids[trackinfo.attrib['ID']
                            ][6] = getFieldOffice(match.group(2))
                else:
                    uspsids[trackinfo.attrib['ID']
                            ][6] = "Still getting delivered OR No tracking details found"

        # return response.json()

    except requests.exceptions.HTTPError as errh:
        print(errh)
    except requests.exceptions.ConnectionError as errc:
        print(errc)
    except requests.exceptions.Timeout as errt:
        print(errt)
    except requests.exceptions.RequestException as err:
        print(err)

    return None


def checkUSPSZipforFO(rows, uuidstr, semap, writer):
    uspsids = {}
    for row in rows:
        match = re.search(
            ".*On (\w*) (\d+), (\d\d\d\d).* Receipt Number (\w*).* assigned is (\w*).", row[3])
        if match:
            row[5] = match.group(1) + " " + \
                match.group(2) + " " + match.group(3)
            row[6] = ""
            # remove older approved cases we will not find information for these tracking number in USPS
            # cannot retrive tracking details more than 120  days from USPS
            dateString = match.group(
                2) + "-" + str(monthtoNum[match.group(1).lower()]) + "-" + match.group(3)
            d1 = datetime.strptime(dateString, "%d-%m-%Y")
            if abs(datetime.today() - d1).days <= 120:
                uspsids[match.group(5)] = row
            else:
                row[6] = "FO unavailable out of tracking date"
        else:
            print("Regular expression failed for " + row[0])

    getTrackingdetails(uspsids)

    return (rows, uuidstr, semap, writer)


def thread_complete(ft):
    res = ft.result()
    writer = res[3]
    with thread_dict_lock:
        for row in res[0]:
            writer.writerow(row)

        # remove the thread id from the dict
        del thread_dict[res[1]]
        # release the semaphore
        res[2].release()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Fill up FO info", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--num_threads", type=int,
                        help="Number of threads to start")
    parser.add_argument('--num_trackids_to_check', type=int,
                        help="Number of USPS trackids to check at a time")
    parser.add_argument('--infile', help="Input CSV file")
    parser.add_argument("--fieldFOtoZipJSON",
                        help="Field office to zip code mapping file")
    parser.add_argument(
        '--USPS_userid', default='', help="USPS user id. Go to USPS(https://www.usps.com/business/web-tools-apis/) to create an account and get this id")

    parser.add_argument(
        "--trackid", default="", help="Just check this Tracking id in usps")

    parser.add_argument(
        "--filename", help="CSV file name to save the data")
    args = parser.parse_args()

    if args.USPS_userid == '':
        print('Need USPS user id to get status of a tracking number. Go to https://www.usps.com/business/web-tools-apis/')
        sys.exit(1)
    else:
        USPS_userid = args.USPS_userid

    if len(args.trackid) == 0:
        with open(args.fieldFOtoZipJSON, 'r', encoding="utf-8") as f:
            data = json.load(f)
            foDict = data['fieldOffice']
            zipToFOzipDict = data['zipToFOzip']

        semap = threading.BoundedSemaphore(value=args.num_threads)
        with open(args.infile, newline='') as inputcsvfile, open(args.filename + ".csv", 'w', newline='') as outcsvfile:
            inreader = csv.reader(inputcsvfile, delimiter=',')
            outwriter = csv.writer(outcsvfile, delimiter=',',
                                   quotechar='"', quoting=csv.QUOTE_MINIMAL)
            trackIds = []
            with concurrent.futures.ThreadPoolExecutor(max_workers=args.num_threads) as executor:
                for row in inreader:
                    if len(row) == 5:
                        row.append("")
                        row.append("")

                    if row[4] == "120" and (len(row[6]) == 0 or row[6] == "Still getting delivered OR No tracking details found"):
                        # Pull USPS status in batches
                        if len(trackIds) == args.num_trackids_to_check:
                            if(semap.acquire()):
                                uuidstr = str(uuid.uuid4())
                                # print("starting thread for receipt number " + receiptNumber)
                                future = executor.submit(
                                    checkUSPSZipforFO, trackIds.copy(), uuidstr, semap, outwriter)
                                with thread_dict_lock:
                                    thread_dict[uuidstr] = future
                                future.add_done_callback(thread_complete)
                                trackIds.clear()

                        trackIds.append(row)
                    else:
                        with thread_dict_lock:
                            outwriter.writerow(row)

                # process what is left over
                if len(trackIds) != 0:
                    if(semap.acquire()):
                        uuidstr = str(uuid.uuid4())
                        # print("starting thread for receipt number " + receiptNumber)
                        future = executor.submit(
                            checkUSPSZipforFO, trackIds.copy(), uuidstr, semap, outwriter)
                        with thread_dict_lock:
                            thread_dict[uuidstr] = future
                        future.add_done_callback(thread_complete)
                        trackIds.clear()

                thread_status = concurrent.futures.wait(thread_dict.values())

        # Lets dump the updated FO DB back
        outdict = {'fieldOffice': foDict, 'zipToFOzip': zipToFOzipDict}
        with open('FOtozip.json', 'w', encoding='utf-8') as f:
            json.dump(outdict, f, ensure_ascii=False, indent=4)

    else:
        justCheckandPrint(args.trackid)
