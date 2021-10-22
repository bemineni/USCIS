# OM Ganesha
# Srikanth Bemineni
# srikanth.bemineni@gmail.com
# I 485 data retriever

import requests
import csv
from bs4 import BeautifulSoup
import re
import random
import time
from datetime import date
import threading
import concurrent.futures
import argparse
import uuid
from argparse import RawTextHelpFormatter


random.seed()
thread_dict = {}
thread_dict_lock = threading.Lock()
mode = "new"

change = {}

category_sum = {}

printOrder = [1, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120, 130, 140]


def requestPost(data):
    try:
        r = requests.post(
            "https://egov.uscis.gov/casestatus/mycasestatus.do", data=data)
        return r
    except:
        return None


def add_to_current_category_sum(category):
    if str(category) not in category_sum:
        category_sum[str(category)] = 1
    else:
        category_sum[str(category)] = category_sum[str(category)] + 1


def category_to_name(category):
    category = int(category)
    if category == 1:
        return "Received"
    elif category == 20:
        return "Expedite"
    elif category == 30:
        return "Finger print received"
    elif category == 40:
        return "Request for evidence was sent"
    elif category == 50:
        return "Response Request for evidence was received"
    elif category == 60:
        return "Case was transfered"
    elif category == 70:
        return "Interview scheduled or rescheduled"
    elif category == 80:
        return "Interview was complete and under review"
    elif category == 90:
        return "Approved"
    elif category == 100:
        return "Denied"
    elif category == 110:
        return "Rejected"
    elif category == 120:
        return "Card was sent may be I485 or EAD"
    elif category == 140:
        return "New category yet to decide"
    else:
        return "Something failed will check tomorrow"


def findCategory(status):
    # Received state
    if "Fingerprint Fee Was Received" in status:
        return 1
    elif "Expedite Request Denied" in status:
        return 1
    elif "Case Was Received" in status:
        return 1
    elif "Case Was Reopened" in status:
        return 1
    elif "Duplicate Notice Was Mailed" in status:
        return 1
    elif "Fees Were Waived" in status:
        return 1
    elif "Fee Refund Was Mailed" in status:
        return 1
    elif "Date of Birth Was Updated" in status:
        return 1
    elif "Name Was Updated" in status:
        return 1
    elif "Fee Will Be Refunded" in status:
        return 1
    elif "Notice Was Returned To USCIS Because The Post Office Could Not Deliver It" in status:
        return 1

    # Expedite request
    elif "Expedite Request Received" in status:
        return 20
    elif "Expedite Request Approved" in status:
        return 20

    # Finger prints taken
    elif "Show Fingerprints Were Taken" in status:
        return 30
    elif "Case Was Updated To Show Fingerprints Were Taken" in status:
        return 30

    # RFE
    elif "Request for Initial Evidence Was Sent" in status:
        return 40
    elif "Request for Additional Evidence Was Sent" in status:
        return 40

    # RFE received
    elif "Response To USCIS' Request For Evidence Was Received" in status:
        return 50
    elif "Request For Evidence Was Received" in status:
        return 50
    elif "Correspondence Was Received And USCIS Is Reviewing It" in status:
        return 50

    # transerfed
    elif "Case Transferred To Another Office" in status:
        return 60
    elif "Case Was Transferred And A New Office Has Jurisdiction" in status:
        return 60

    # Interview
    elif "Request To Reschedule My Appointment Was Received" in status:
        return 70
    elif "Ready to Be Scheduled for An Interview" in status:
        return 70
    elif "Interview Was Rescheduled" in status:
        return 70
    elif "Interview Was Scheduled" in status:
        return 70
    elif "Case Was Updated To Show That No One Appeared for In-Person Processing" in status:
        return 70
    elif "Continuation Notice Was Mailed" in status:
        return 70

    # Interview complete
    elif "Interview Was Completed And My Case Must Be Reviewed" in status:
        return 80

    # Approved
    elif "Card Was Mailed To Me" in status:
        return 90
    elif "Case Was Approved" in status:
        return 90
    elif "New Card Is Being Produced" in status:
        return 90
    elif "Interview Cancelled And Notice Ordered" in status:
        return 90
    elif "Notice Explaining USCIS Actions Was Mailed" in status:
        return 90
    elif "Case Closed Benefit Received By Other Means" in status:
        return 90
    elif "Card Was Returned To USCIS" in status:
        return 90
    elif "Case Approval Was Certified By USCIS" in status:
        return 90

    # Denied
    elif "Case Was Denied" in status:
        return 100
    elif "Petition/Application Was Rejected For Insufficient Funds" in status:
        return 100
    elif "Withdrawal Acknowledgement Notice Was Sent" in status:
        return 100

    # Rejected
    elif "Case Rejected" in status:
        return 110
    elif "Case Was Rejected" in status:
        return 110

    # I 485 cards sent
    elif "Card Was Picked Up By The United States Postal Service" in status:
        return 120
    elif "Card Was Delivered To Me By The Post Office" in status:
        return 120
    elif "Card Is Being Returned to USCIS by Post Office" in status:
        return 120

    # Unknown new category still need to decide where this belongs
    # We will check the next day
    # The description will lose the I 485 applicant type for some time, but
    # will return to one of the statuses above later
    elif "Document Was Mailed To Me" in status:
        return 140
    elif "Biometrics Appointment Was Scheduled" in status:
        return 140
    # everything else
    else:
        return 130


def checkOnceBeforeProcessing(r):
    '''
        Some time the request status is 200, but the data comes as junk, which is not
        parseable.
    '''
    soup = BeautifulSoup(r.text, "html.parser")

    soupdiv = soup.find('div', class_="appointment-sec")
    if soupdiv:
        status_p = soupdiv.find('div', class_="rows").find('p')
        if status_p and len(status_p) > 0:
            return True

    return False


def checkCaseandReport(receiptNumber, id, semap, writer, previousStatus, ignoreApprovedCases=False):

    data = {'changeLocale': None,
            'completedActionsCurrentPage': 0,
            'upcomingActionsCurrentPage': 0,
            'appReceiptNum': receiptNumber,
            'caseStatusSearchBtn': 'CHECK+STATUS'}

    # if mode != 'new' and len(previousStatus) == 5:
    #     # can be removed, this was added at one state to include date and field office
    #     # modification to include field office
    #     # date
    #     previousStatus.append("")
    #     # field office
    #     previousStatus.append("")

    if ignoreApprovedCases and int(previousStatus[4]) == 120:
        return (receiptNumber, id, semap, writer, previousStatus, previousStatus)

    try:
        retry = 5
        r = requestPost(data)

        if checkOnceBeforeProcessing(r) == False:
            # Lets reset to get the data again
            r = None

        while r == None and retry > 0:
            r = requestPost(data)
            if checkOnceBeforeProcessing(r) == False:
                # Lets reset to get the data again
                r = None
            time.sleep(random.randint(1, 30))
            retry = retry - 1

        if retry <= 0:
            print("Failed to get status for " + receiptNumber)
            return (receiptNumber, id, semap, writer, [receiptNumber,
                                                       "None",
                                                       "Unknown Case",
                                                       "Dont know reached retry limit",
                                                       130, "", ""], previousStatus)

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

                # print(receiptNumber + "  " + caseType)
                status_heading = soupdiv.find(
                    'div', class_="rows").find('h1').contents[0]
                category = findCategory(status_heading)

                if mode == 'new' and caseType == "None" and category == 120:
                    # mostly approved cases may be I 485, I 131 or anything move to this state.
                    # we include them to be tracked for how many have been approved
                    return (receiptNumber, id, semap, writer, [receiptNumber,
                                                               caseType,
                                                               status_heading,
                                                               status,
                                                               category, "", ""], previousStatus)
                elif mode == 'new' and caseType != "I-485":
                    return (receiptNumber, id, semap, writer, None, None)

                # Below will be executed for 'compare' actions and for 'new' action only if the caseType was 'I-485'

                if caseType == "I-485" or category != 120 or category != 140:
                    return (receiptNumber, id, semap, writer, [receiptNumber,
                                                               caseType,
                                                               status_heading,
                                                               status,
                                                               category, "", ""], previousStatus)
                elif category == 120:
                    return (receiptNumber, id, semap, writer, [receiptNumber,
                                                               caseType,
                                                               status_heading,
                                                               status,
                                                               category, date.today().strftime("%m/%d/%Y"), ""], previousStatus)
                elif category == 140:
                    return (receiptNumber, id, semap, writer, [receiptNumber,
                                                               caseType,
                                                               status_heading,
                                                               status,
                                                               category, "", ""], previousStatus)
                else:
                    print("Unknown category " + receiptNumber +
                          " status restoring to previous data")
                    return (receiptNumber, id, semap, writer, previousStatus, previousStatus)

            else:
                return (receiptNumber, id, semap, writer, [receiptNumber,
                                                           "None",
                                                           "Unknown Case",
                                                           "Dont know what response we got but failed to parse",
                                                           130, "", ""], previousStatus)

        else:
            return (receiptNumber, id, semap, writer, [receiptNumber,
                                                       "None",
                                                       "Unknown Case",
                                                       "Dont know what happened try again tomorrow",
                                                       130, "", ""], previousStatus)
    except:
        return (receiptNumber, id, semap, writer, [receiptNumber,
                                                   "None",
                                                   "Unknown Case",
                                                   "Exception processing this receipt Number",
                                                   130, "", ""], previousStatus)


def sleep_thread(receiptNumber, id, semap, writer):
    print(id + " thread started")
    time.sleep(10)
    return (receiptNumber, id, semap, writer, [])


def thread_complete(ft):
    res = ft.result()
    # print(res[1] + " thread completed")
    # print(res)
    with thread_dict_lock:
        if res and len(res[4]) > 0:
            writer = res[3]
            writer.writerow(res[4])
            previousStatus = res[5]
            # accumulate change in each category to calculate the percentage change from category - to category
            if mode == "compare" and previousStatus != None:
                prevCategory = previousStatus[4]
                add_to_current_category_sum(prevCategory)
                currCategory = res[4][4]
                if str(prevCategory) not in change:
                    change[str(prevCategory)] = {str(currCategory): 1}
                else:
                    if str(currCategory) not in change[str(prevCategory)]:
                        change[str(prevCategory)][str(currCategory)] = 1
                    else:
                        change[str(prevCategory)][str(currCategory)] = change[str(
                            prevCategory)][str(currCategory)]+1
        del thread_dict[res[1]]
        res[2].release()


def new_thread_complete(ft):
    res = ft.result()
    with thread_dict_lock:
        if res and res[4]:
            writer = res[3]
            writer.writerow(res[4])

        del thread_dict[res[1]]
        res[2].release()


def analyze(currentStatus, previousStatus):
    if len(currentStatus) > 0:
        # accumulate change in each category to calculate the percentage change from category - to category
        prevCategory = previousStatus[4]
        add_to_current_category_sum(prevCategory)
        currCategory = currentStatus[4]
        # if int(prevCategory) == 90 and int(currCategory) == 70:
        #     print("Debug")
        if str(prevCategory) not in change:
            change[str(prevCategory)] = {str(currCategory): 1}
        else:
            if str(currCategory) not in change[str(prevCategory)]:
                change[str(prevCategory)][str(currCategory)] = 1
            else:
                change[str(prevCategory)][str(currCategory)
                                          ] = change[str(prevCategory)][str(currCategory)]+1


def printCompareData():
    # print the precentage change
    card_sent_postoffice = 0
    for category_int in printOrder:
        category = str(category_int)
        previous_category_sum = 0
        if category in category_sum:
            previous_category_sum = category_sum[category]
        print(category_to_name(category) +
              " - (" + str(previous_category_sum) + ")")
        print("========================")
        if category in change:
            for num_category_change in change[category]:
                if num_category_change != category:
                    print("--Moved--> " + category_to_name(num_category_change) + " : " + str(change[category][num_category_change]) + "/" + str(category_sum[category]) + " : " +
                          str(round((change[category][num_category_change] / category_sum[category])*100, 2)) + "%")
                    if int(num_category_change) == 120 and int(category) != 120:
                        card_sent_postoffice = card_sent_postoffice + \
                            change[category][num_category_change]
        print("========================")

    print("Guaranteed I-485 card sent to the applicant from previous compared date : " +
          str(card_sent_postoffice))


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="I-485 status retriever Srikanth Bemineni", formatter_class=RawTextHelpFormatter)
    parser.add_argument('--centerYear', help="Center + year")
    parser.add_argument('--workday', help="workday")
    parser.add_argument(
        '--startCase', help='Starting case number', type=int, default=0)
    parser.add_argument('--endCase', help='Ending case number',
                        type=int, default=99999)
    parser.add_argument("--num_threads", type=int,
                        help="Number of threads to start")
    parser.add_argument('--infile', help="Input CSV file")
    parser.add_argument('--infile2', help="Second Input CSV file")
    parser.add_argument(
        "--filename", help="CSV file name to save the data, date will appened by default")
    parser.add_argument("--ignoreApprovedCases", action="store_true",
                        help="Dont check none cases")
    parser.add_argument("--append", action="store_true",
                        help="Append to existing CSV file")
    parser.add_argument(
        "action", help="\
             new - Retrieve all case statuses freshly for the range specified\n\
             Ex., python I485.py --centerYear MSC21 --workday 907 --startCase 1 --endCase 99999 --num_threads 200 --filename \"MSC21907\" new\n\n\
             compare - Collect current data and compare with previous data set. Need to provide the old csv file.\n\
             Ex., python I485.py --num_threads 200 --infile \"MSC21907_06_18_2021.csv\" --filename \"MSC21907\" --ignoreApprovedCases compare\n\n\
             count - Get the count of the each status category in a collected csv file\n\
             Ex., python I485.py --infile MSC21907_06_25_2021.csv count\n\n\
             comparefiles - Compare data between two csv files\n\
             Ex., python I485.py --infile MSC21907_06_18_2021.csv --infile2 MSC21907_06_25_2021.csv comparefiles")
    args = parser.parse_args()

    datestring = date.today().strftime("%m_%d_%Y")
    # print("Action " + args.action)
    start = time.time()

    if args.action == "new":
        semap = threading.BoundedSemaphore(value=args.num_threads)
        with open(args.filename + "_" + datestring + '.csv', 'w', newline='') as file:
            writer = csv.writer(file, delimiter=',',
                                quotechar='"', quoting=csv.QUOTE_MINIMAL)

            with concurrent.futures.ThreadPoolExecutor(max_workers=args.num_threads) as executor:
                for i in range(args.startCase, args.endCase):
                    numstring = str(i)
                    if len(numstring) < 5:
                        numstring = '0'*(5-len(numstring)) + numstring
                    receiptNumber = args.centerYear + \
                        args.workday + str(numstring)
                    uuidstr = str(uuid.uuid4())
                    if(semap.acquire()):
                        # print("starting thread for receipt number " + receiptNumber)
                        future = executor.submit(
                            checkCaseandReport, receiptNumber, uuidstr, semap, writer, None, False)
                        future.add_done_callback(new_thread_complete)
                        with thread_dict_lock:
                            thread_dict[uuidstr] = future

                thread_status = concurrent.futures.wait(thread_dict.values())

    elif args.action == "compare":
        mode = "compare"
        semap = threading.BoundedSemaphore(value=args.num_threads)
        fileopenMode = 'w'
        if args.append:
            fileopenMode = 'w+'
        with open(args.infile, newline='') as inputcsvfile, open(args.filename + "_" + datestring + ".csv", fileopenMode, newline='') as outcsvfile:
            inreader = csv.reader(inputcsvfile, delimiter=',')
            outwriter = csv.writer(outcsvfile, delimiter=',',
                                   quotechar='"', quoting=csv.QUOTE_MINIMAL)
            with concurrent.futures.ThreadPoolExecutor(max_workers=args.num_threads) as executor:
                for row in inreader:
                    uuidstr = str(uuid.uuid4())
                    if(semap.acquire()):
                        # print("starting thread for receipt number " + receiptNumber)
                        future = executor.submit(
                            checkCaseandReport, row[0], uuidstr, semap, outwriter, row, args.ignoreApprovedCases)
                        with thread_dict_lock:
                            thread_dict[uuidstr] = future
                        future.add_done_callback(thread_complete)

                thread_status = concurrent.futures.wait(thread_dict.values())

            printCompareData()

    elif args.action == "count":
        mode = "count"
        with open(args.infile, newline='') as inputcsvfile:
            inreader = csv.reader(inputcsvfile, delimiter=',')
            for row in inreader:
                add_to_current_category_sum(row[4])

        total = 0
        for category in printOrder:
            if str(category) in category_sum:
                print(category_to_name(category) +
                      ":" + str(category_sum[str(category)]))
                total = total + category_sum[str(category)]
        print("------------------------------------------------------------")
        print("Total : " + str(total))
    elif args.action == "comparefiles":
        dict1 = {}
        dict2 = {}
        with open(args.infile, newline='') as inputcsvfile1:
            inreader = csv.reader(inputcsvfile1, delimiter=",")
            for row in inreader:
                dict1[row[0]] = row

        with open(args.infile2, newline='') as inputcsvfile2:
            inreader = csv.reader(inputcsvfile2, delimiter=",")
            for row in inreader:
                dict2[row[0]] = row

        for key in dict1:
            if key in dict2:
                analyze(dict2[key], dict1[key])
            else:
                print("Key missing : " + key)

        printCompareData()

    else:
        print("Unknown action")

    end = time.time()
    # print(f"Runtime of the program is {end - start}")
