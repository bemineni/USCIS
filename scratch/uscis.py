import requests
import csv
from bs4 import BeautifulSoup
import re
import random
import time

random.seed()


def requestPost(data):
    try:
        r = requests.post(
            "https://egov.uscis.gov/casestatus/mycasestatus.do", data=data)
        return r
    except:
        return None


day = 907
number = 1

sleepCount = random.randint(1, 200)

with open('reciepts.csv', 'w+', newline='') as file:
    writer = csv.writer(file, delimiter='|')

    for i in range(1, 8580):
        if sleepCount == 0:
            print("Sleeping for random time")
            time.sleep(random.randint(1, 10))
            sleepCount = random.randint(1, 100)
        else:
            sleepCount = sleepCount - 1

        number = number + 1
        numstring = str(number)
        if len(numstring) < 5:
            numstring = '0'*(5-len(numstring)) + numstring
        receiptNumber = "MSC21" + str(day) + str(numstring)

        data = {'changeLocale': None,
                'completedActionsCurrentPage': 0,
                'upcomingActionsCurrentPage': 0,
                'appReceiptNum': receiptNumber,
                'caseStatusSearchBtn': 'CHECK+STATUS'}
        retry = 10
        r = requestPost(data)

        while r == None and retry > 0:
            r = requestPost(data)
            time.sleep(random.randint(1, 30))
            retry = retry - 1

        if retry == 0:
            print("Failed to get status for " + receiptNumber)

        soup = BeautifulSoup(r.text, "html.parser")

        soupdiv = soup.find('div', class_="appointment-sec")
        if soupdiv:
            status_p = soupdiv.find('div', class_="rows").find('p')
            if status_p and len(status_p) > 0:
                status = status_p.contents[0]
                match = re.search(".*(I\-\d+).*", status)
                caseType = "None"
                if match:
                    caseType = match.group(1)

                print(receiptNumber + "  " + caseType)

                if caseType == "I-485":
                    writer.writerow([receiptNumber,
                                     caseType,
                                     soupdiv.find('div', class_="rows").find(
                                         'h1').contents[0],
                                     status])
