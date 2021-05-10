#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Apr 10 17:47:25 2021

This program connects to the covid19tracker.ca API to pull in information on COVID cases and vaccines
And sends an automated response to a Telegram group via the Telegram Bot wheresmyfuckingvaccine

@author: Anirudh & Ajay
"""
import urllib.request
import json
from matplotlib import pyplot as plt
from matplotlib import ticker as pltticker
import pandas as pd
import prettytable as pt

stateVaccineImage = "state_vaccines.png"
canadaVaccineImage = "canada_vaccines.png"
urlProvince = "https://api.covid19tracker.ca/reports/province/"
urlCanada = "https://api.covid19tracker.ca/reports"
urlSuffix = {
    "Alberta": "AB",
    "British Columbia": "BC",
    "Manitoba": "MB",
    "New Brunswick": "NB",
    "Newfoundland and Labrador": "NL",
    "Northwest Territories": "NT",
    "Nova Scotia": "NS",
    "Nunavut": "NU",
    "Ontario": "ON",
    "Prince Edward Island": "PE",
    "Quebec": "QC",
    "Saskatchewan": "SK",
    "Yukon": "YT",
    "AB": "AB",
    "BC": "BC",
    "MB": "MB",
    "NB": "NB",
    "NL": "NL",
    "NT": "NT",
    "NS": "NS",
    "NU": "NU",
    "ON": "ON",
    "PE": "PE",
    "PEI": "PE",
    "QC": "QC",
    "SK": "SK",
    "YT": "YT",
}


def plotVaccinationsForURL(url, title="Vaccinations", outputImage="vaccinations.png"):
    jsonData = json.loads(urllib.request.urlopen(url).read().decode())
    dates = []
    total_vaccinations = []
    total_vaccines_distributed = []
    new_vaccinations = []
    windowSize = 7
    movingWindow = 7 * [0]
    index = 0
    last = 0

    for day_data in jsonData["data"]:
        date = pd.to_datetime(day_data["date"])
        if date > pd.Timestamp(2020, 12, 15):
            dates.append(date)
            total_vaccinations.append(day_data["total_vaccinations"])
            total_vaccines_distributed.append(day_data["total_vaccines_distributed"])
            movingWindow[index] = day_data["change_vaccinations"]
            new_vaccinations.append(sum(movingWindow) / len(movingWindow))
            last = index
            index = 0 if (index == (windowSize - 1)) else (index + 1)

    fig, ax = plt.subplots()
    ax.set_title(title)
    ln1 = ax.plot(dates, total_vaccinations, label="Total Vaccinations")
    ln2 = ax.plot(dates, total_vaccines_distributed, "r", label="Vaccines Distributed")
    ax.get_yaxis().set_major_formatter(
        pltticker.FuncFormatter(lambda x, p: format(int(x), ","))
    )
    ax.set_ylabel("Total Vaccinations")
    plt.xticks(rotation=45)
    ax2 = ax.twinx()
    ln3 = ax2.plot(dates, new_vaccinations, "b", label="New Vaccintations (7-day avg)")
    ax2.get_yaxis().set_major_formatter(
        pltticker.FuncFormatter(lambda x, p: format(int(x), ","))
    )
    ax2.set_ylabel("New Vaccinations")
    lns = ln1 + ln2 + ln3
    labs = [l.get_label() for l in lns]
    ax.legend(lns, labs, loc=0)
    fig.savefig(outputImage, format="png", dpi=300, bbox_inches="tight")
    plt.close()


def plotCanadaVaccinations():
    plotVaccinationsForURL(urlCanada, "Vaccinations for Canada", canadaVaccineImage)


def plotVaccinations(province="Ontario") -> bool:
    province = province.title()
    if province not in urlSuffix:
        print("FML")
        return False
    else:
        plotVaccinationsForURL(
            urlProvince + urlSuffix[province],
            "Vaccinations for " + province.title(),
            stateVaccineImage,
        )
        return True


def getSummaryData(url, title):
    summary = {}
    jsonData = json.loads(urllib.request.urlopen(url).read().decode())
    outputString = (
        "<b>" + title + "</b>\n<i>(As of " + jsonData["data"][-1]["date"] + ")</i>\n"
    )
    summary["Today"] = jsonData["data"][-1]["change_vaccinations"]
    summary["Total"] = jsonData["data"][-1]["total_vaccinations"]

    table = pt.PrettyTable(["Vaccinated", "Count"])
    table.align["Vaccinated"] = "l"
    table.align["Count"] = "r"
    for key, value in summary.items():
        outputNum = format(value, ",d")
        table.add_row([str(key), outputNum])
    outputString += f"<pre>{table}</pre>"
    outputString += "\n"

    return outputString


def getCanadaSummary() -> str:
    return getSummaryData(urlCanada, "Canada Vaccinations").title()


def getSummary(province="Ontario"):
    province = province.title()
    provinceString = ""
    if province in urlSuffix:
        provinceString = getSummaryData(
            urlProvince + urlSuffix[province], province.title() + " Vaccinations"
        )
    return provinceString.title()


def main() -> None:
    for (key, item) in urlSuffix.items():
        print(getSummaryData(urlProvince + item, key + " Vaccinations"))


if __name__ == "__main__":
    main()
