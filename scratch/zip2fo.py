# OM Ganesha
# Srikanth Bemineni
# srikanth.bemineni@gmail.com

import requests
import argparse
import json
from uszipcode import SearchEngine
states = ["Alabama",
          "Alaska",
          "Arizona",
          "Arkansas",
          "California",
          "Colorado",
          "Connecticut",
          "Delaware",
          "Florida",
          "Georgia",
          "Hawaii",
          "Idaho",
          "Illinois",
          "Indiana",
          "Iowa",
          "Kansas",
          "Kentucky",
          "Louisiana",
          "Maine",
          "Maryland",
          "Massachusetts",
          "Michigan",
          "Minnesota",
          "Mississippi",
          "Missouri",
          "Montana",
          "Nebraska",
          "Nevada",
          "New Hampshire",
          "New Jersey",
          "New Mexico",
          "New York",
          "North Carolina",
          "North Dakota",
          "Ohio",
          "Oklahoma",
          "Oregon",
          "Pennsylvania",
          "Rhode Island",
          "South Carolina",
          "South Dakota",
          "Tennessee",
          "Texas",
          "Utah",
          "Vermont",
          "Virginia",
          "Washington",
          "West Virginia",
          "Wisconsin",
          "Wyoming"]


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


foDict = {'fieldOffice': {}, 'zipToFOzip': {}}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Zipcode and Field office locator", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--combine", action="store_true",
                        help=" State to pull FO to zipcode")
    parser.add_argument("state", help=" State to pull FO to zipcode")
    args = parser.parse_args()
    if not args.combine:
        with SearchEngine() as search:
            res = search.by_state(args.state, returns=10000)
            for item in res:
                fojson = getFO(item.zipcode)
                if fojson and "Found" in fojson['localOfficemessage']:
                    print("-------{zip}--------".format(zip=item.zipcode))
                    print(fojson['localOfficeInfo']['localName'])
                    print(fojson['localOfficeInfo']['address'])
                    print(fojson['localOfficeInfo']['city'])
                    print(fojson['localOfficeInfo']['zipCode'])
                    print("--------------------")

                    fozip = fojson['localOfficeInfo']['zipCode']

                    if fozip not in foDict['fieldOffice']:
                        foDict['fieldOffice'][fozip] = fojson['localOfficeInfo'].copy()
                        foDict['zipToFOzip'][item.zipcode] = fozip
                    else:
                        foDict['zipToFOzip'][item.zipcode] = fozip

            with open(args.state+'.json', 'w', encoding='utf-8') as f:
                json.dump(foDict, f, ensure_ascii=False, indent=4)
    else:

        for state in states:
            with open(state+'.json', 'r', encoding="utf-8") as f:
                data = json.load(f)
                foDict['fieldOffice'] = {
                    **foDict['fieldOffice'], **data['fieldOffice']}
                foDict['zipToFOzip'] = {
                    **foDict['zipToFOzip'], **data['zipToFOzip']}

        with open('FOtozip.json', 'w', encoding='utf-8') as f:
            json.dump(foDict, f, ensure_ascii=False, indent=4)
