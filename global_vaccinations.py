#!/usr/bin/env python3
import csv
import pandas as pd
import prettytable as pt
import wget
from matplotlib import pyplot as plt
from matplotlib import ticker as pltticker

countryVaccineImage = "country_vaccine.png"


def loadDataset() -> pd.DataFrame:
    dataSetURL = "https://covid.ourworldindata.org/data/"
    covid_data_file = "owid-covid-data.csv"
    # wget.download(dataSetURL+covid_data_file)
    covid_data = pd.read_csv(covid_data_file)
    selection = covid_data[
        [
            "location",
            "date",
            "new_vaccinations",
            "new_vaccinations_smoothed",
            "people_vaccinated",
            "people_vaccinated_per_hundred",
            "people_fully_vaccinated",
            "people_fully_vaccinated_per_hundred",
        ]
    ]
    return selection


def getCountryData(country: str = "Canada") -> pd.DataFrame:
    covid_df = loadDataset()
    country_df = covid_df.loc[covid_df["location"] == country].set_index("date")
    del country_df["location"]
    return country_df


def getCountryString(input_country: str) -> str:
    country = input_country.title()
    countryRemap = {
        "USA": "United States",
        "US": "United States",
        "UK": "United Kingdom",
        "UAE": "United Arab Emirates",
    }
    if country.upper() in countryRemap:
        country = countryRemap[country.upper()]

    return country


def getCountrySummary(country: str = "Canada") -> str:
    country = getCountryString(country)
    country_df = getCountryData(country)
    currentIndex = country_df.last_valid_index()
    if currentIndex == None:
        raise IndexError()
    most_recent = country_df.loc[currentIndex]
    date = most_recent.name

    table = pt.PrettyTable(["Vaccinated", "Count"])
    table.align["Vaccinated"] = "l"
    table.align["Count"] = "r"
    isTotal = False
    second_title_added = False
    table.add_row(["1-shot", ""])
    title_mapping = {
        "new_vaccinations": "Today",
        "people_vaccinated": "Total",
        "people_vaccinated_per_hundred": "Vax %",
        "people_fully_vaccinated": "Total",
        "people_fully_vaccinated_per_hundred": "Vax %",
    }
    for cName, cData in most_recent.iteritems():
        if cName.find("smoothed") >= 0:
            continue
        isPercent = cName.find("per_hundred") >= 0
        isTotal = isTotal or (cName.find("fully") >= 0)
        if isTotal and not second_title_added:
            table.add_row(["2-shot", ""])
            second_title_added = True
        cName = title_mapping[cName]
        cName = "- " + cName
        if isPercent:
            table.add_row([cName, "{:.2f}".format(cData) + " %"])
        else:
            table.add_row([cName, format(int(cData), ",d")])
    outputString = (
        "<b>Summary for " + country + "</b>\n<i>(as of " + str(date) + ")</i>\n"
    )
    outputString += f"<pre>{table}</pre>"

    return outputString


def plotCountryVaccinations(country: str = "United States"):
    country_df = getCountryData(getCountryString(country))
    title_mapping = {
        "new_vaccinations_smoothed": "New Vaccinations",
        "people_vaccinated_per_hundred": "1-shot %",
        "people_fully_vaccinated_per_hundred": "2-shot %",
    }
    set = [
        "people_vaccinated_per_hundred",
        "people_fully_vaccinated_per_hundred",
        "new_vaccinations_smoothed",
    ]
    current_df = country_df[set].copy()

    fig, ax = plt.subplots()
    ax.set_title("Vaccinations for " + country)
    current_df.rename(columns=title_mapping, inplace=True)
    current_df.plot(
        kind="line",
        color="c",
        figsize=(10, 6),
        rot=30,
        ax=ax,
        y="1-shot %",
    )
    current_df.plot(
        kind="line",
        color="m",
        figsize=(10, 6),
        rot=30,
        ax=ax,
        y="2-shot %",
    )
    ax2 = current_df.plot(
        kind="line",
        color="b",
        figsize=(10, 6),
        rot=30,
        ax=ax,
        y="New Vaccinations",
        secondary_y=True,
    )

    ax.set_xlabel("")
    ax.set_ylabel("Total Vaccinations")
    ax2.set_ylabel("New Vaccinations")
    ax2.get_yaxis().set_major_formatter(
        pltticker.FuncFormatter(lambda x, p: format(int(x), ","))
    )

    fig.tight_layout()
    fig.savefig(countryVaccineImage, format="png", dpi=300, bbox_inches="tight")
    plt.close()


def main() -> None:
    plotCountryVaccinations()
    print(getCountrySummary("US"))
    print(getCountrySummary("UK"))
    print(getCountrySummary("Canada"))
    print(getCountrySummary("India"))


if __name__ == "__main__":
    main()
