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

populationData = {
    "AB": 4428112,
    "BC": 5145851,
    "MB": 1379584,
    "NB": 781315,
    "NL": 520998,
    "NS": 979115,
    "NT": 45074,
    "NU": 39285,
    "ON": 14733119,
    "PE": 159713,
    "QC": 8575779,
    "SK": 1177884,
    "YT": 42176,
}

canadaPopulation = sum(populationData.values())


def plotVaccinationsForURL(
    url: str,
    title: str = "Vaccinations",
    outputImage: str = "vaccinations.png",
    population: str = None,
) -> None:
    jsonData = json.loads(urllib.request.urlopen(url).read().decode())
    dates = []
    total_vaccinations = []
    total_vaccinated = []
    total_boosters_1 = []
    new_vaccinations = []
    new_vaccinated = []
    new_boosters_1 = []
    windowSize = 7
    movingWindow = 7 * [0]
    movingWindow2 = 7 * [0]
    movingWindow3 = 7 * [0]
    index = 0
    last = 0

    if population == None:
        raise ValueError("Population data missing for plotting the vaccination data.")

    for day_data in jsonData["data"]:
        date = pd.to_datetime(day_data["date"])
        if date > pd.Timestamp(2020, 12, 15):
            dates.append(date)
            if day_data["total_vaccinations"] == None:
                total_vax = 0
            else:
                total_vax = day_data["total_vaccinations"] * 100.0 / population
            if day_data["total_vaccinated"] == None:
                total_full_vax = 0
            else:
                total_full_vax = day_data["total_vaccinated"] * 100.0 / population
            if day_data["total_boosters_1"] == None:
                total_boosters_1 = 0
            else:
                total_boosters_1 = day_data["total_boosters_1"] * 100.0 / population
            total_vaccinated.append(total_full_vax)
            total_vaccinations.append(total_vax - total_full_vax - total_boosters_1)
            movingWindow[index] = day_data["change_vaccinations"]
            if day_data["change_vaccinated"] != None:
                movingWindow2[index] = day_data["change_vaccinated"]
            else:
                movingWindow2[index] = 0
            if day_data["change_boosters_1"] == None:
                movingWindow3[index] = 0
            else:
                movingWindow3[index] = day_data["change_boosters_1"]
            new_vaccinations.append(sum(movingWindow) / len(movingWindow))
            new_vaccinated.append(sum(movingWindow2) / len(movingWindow2))
            new_boosters_1.append(sum(movingWindow3) / len(movingWindow3))
            last = index
            index = 0 if (index == (windowSize - 1)) else (index + 1)

    fig, ax = plt.subplots()
    ax.set_title(title)
    ln1 = ax.plot(dates, total_vaccinations, color="c", label="1-shot %")
    ln3 = ax.plot(dates, total_vaccinated, color="m", label="2-shot %")
    ax.set_ylabel("Total Vaccinations")
    plt.xticks(rotation=45)

    # Second axis
    ax2 = ax.twinx()
    ln4 = ax2.plot(
        dates,
        new_vaccinations,
        color="b",
        label="New Vaccintations (7-day avg)",
    )
    ln5 = ax2.plot(
        dates,
        new_vaccinated,
        color="k",
        label="New Fully Vaxxed (7-day avg)",
    )
    ax2.get_yaxis().set_major_formatter(
        pltticker.FuncFormatter(lambda x, p: format(int(x), ","))
    )
    ax2.set_ylabel("New Vaccinations")
    lns = ln1 + ln3 + ln4 + ln5
    labs = [l.get_label() for l in lns]
    ax.legend(lns, labs, loc=0)
    fig.savefig(outputImage, format="png", dpi=300, bbox_inches="tight")
    plt.close()


def plotCanadaVaccinations():
    plotVaccinationsForURL(
        urlCanada, "Vaccinations for Canada", canadaVaccineImage, canadaPopulation
    )


def plotVaccinations(province="Ontario") -> bool:
    province = province.title()
    if province not in urlSuffix:
        print("FML")
        return False
    else:
        plotVaccinationsForURL(
            urlProvince + urlSuffix[province],
            "Vaccinations for " + province,
            stateVaccineImage,
            populationData[urlSuffix[province]],
        )
        return True


def tableAddSection(title, summary, table, population) -> None:
    table.add_row([title, ""])
    for key, value in summary.items():
        outputNum = format(value, ",d")
        table.add_row([str(key), outputNum])
        if key == "- Total":
            vaxPercent = min(100, 100.0 * value / population)
            vaxPercentStr = "{:.2f}".format(vaxPercent) + "%"
            table.add_row(["- Vax %", vaxPercentStr])


def getSummaryData(url, title, population):
    summary = {}
    jsonData = json.loads(urllib.request.urlopen(url).read().decode())
    outputString = (
        "<b>" + title + "</b>\n<i>(As of " + jsonData["data"][-1]["date"] + ")</i>\n"
    )

    table = pt.PrettyTable(["Vaccinated", "Count"])
    table.align["Vaccinated"] = "l"
    table.align["Count"] = "r"

    summary["- Today"] = (
        jsonData["data"][-1]["change_vaccinations"]
        - jsonData["data"][-1]["change_vaccinated"]
        - jsonData["data"][-1]["change_boosters_1"]
    )
    summary["- Total"] = (
        jsonData["data"][-1]["total_vaccinations"]
        - jsonData["data"][-1]["total_vaccinated"]
        - jsonData["data"][-1]["total_boosters_1"]
    )
    tableAddSection("1-shot", summary, table, population)

    summary["- Today"] = jsonData["data"][-1]["change_vaccinated"]
    summary["- Total"] = jsonData["data"][-1]["total_vaccinated"]
    tableAddSection("2-shot", summary, table, population)

    summary["- Today"] = jsonData["data"][-1]["change_boosters_1"]
    summary["- Total"] = jsonData["data"][-1]["total_boosters_1"]
    tableAddSection("Booster 1", summary, table, population)

    outputString += f"<pre>{table}</pre>"
    outputString += "\n"

    return outputString


def getCanadaSummary() -> str:
    return getSummaryData(urlCanada, "Canada Vaccinations", canadaPopulation).title()


def getSummary(province="Ontario"):
    province = province.title()
    provinceString = ""
    if province in urlSuffix:
        provinceString = getSummaryData(
            urlProvince + urlSuffix[province],
            province.title() + " Vaccinations",
            populationData[urlSuffix[province]],
        )
    return provinceString.title()


def main() -> None:
    for (key, item) in urlSuffix.items():
        print(
            getSummaryData(
                urlProvince + item, key + " Vaccinations", populationData[item]
            )
        )

    print(getCanadaSummary())
    plotCanadaVaccinations()
    plotVaccinations("Ontario")


if __name__ == "__main__":
    main()
