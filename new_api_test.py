#!/usr/bin/env python3
# Source: https://pypi.org/project/COVID19Py/

import COVID19Py

for source in ["jhu", "csbs", "nyt"]:
    print(source)
    locations = []
    try:
        covid19 = COVID19Py.COVID19(data_source=source)
        locations = covid19.getLocations()
    except:
        print("Houston, we have a problem.")
    # print(locations)
    last_country = ""
    # print(locations[0])
    for item in locations:
        country = item["country"]
        if country != last_country:
            print(country)
            last_country = country
        if item["province"]:
            print("\t" + item["province"])
