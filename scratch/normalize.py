import argparse
import csv


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

    # Finger prints taken
    elif "Show Fingerprints Were Taken" in status:
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

    # Interview complete
    elif "Interview Was Completed And My Case Must Be Reviewed" in status:
        return 80

    # Approved
    elif "Card Was Mailed To Me" in status:
        return 90
    elif "Case Was Approved" in status:
        return 90
    elif "Interview Cancelled And Notice Ordered" in status:
        return 90
    elif "Notice Explaining USCIS Actions Was Mailed" in status:
        return 90
    elif "Case Closed Benefit Received By Other Means" in status:
        return 90
    elif "Card Was Returned To USCIS" in status:
        return 90
    elif "New Card Is Being Produced" in status:
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

    elif "Card Was Picked Up By The United States Postal Service" in status:
        return 120
    elif "New Card Is Being Produced" in status:
        return 120
    elif "Card Was Delivered To Me By The Post Office" in status:
        return 120
    # everything else
    else:
        return 130


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('--infile', help="Input CSV file")
    parser.add_argument('--outfile', help="Ouput CSV file")
    args = parser.parse_args()

    with open(args.infile, newline='') as inputcsvfile, open(args.outfile, 'w', newline='') as outcsvfile:
        inreader = csv.reader(inputcsvfile, delimiter=',')
        outwriter = csv.writer(outcsvfile, delimiter=',',
                               quotechar='"', quoting=csv.QUOTE_MINIMAL)
        for row in inreader:
            row[4] = findCategory(row[2])
            outwriter.writerow(row)
