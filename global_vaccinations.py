#!/usr/bin/env python3
import csv
import pandas as pd
import prettytable as pt
import wget

covid_data = None


def loadDataset() -> pd.DataFrame:
    dataSetURL = "https://covid.ourworldindata.org/data/"
    covid_data_file = "owid-covid-data.csv"
    # wget.download(dataSetURL+covid_data_file)
    covid_data = pd.read_csv(covid_data_file)
    selection = covid_data[
        [
            "location",
            "date",
            "total_cases",
            "new_cases",
            "new_cases_smoothed",
            "total_deaths",
            "new_deaths",
            "new_deaths_smoothed",
            "total_cases_per_million",
            "new_cases_per_million",
            "new_cases_smoothed_per_million",
            "total_deaths_per_million",
            "new_deaths_per_million",
            "new_deaths_smoothed_per_million",
            "positive_rate",
            "total_vaccinations",
            "people_vaccinated",
            "people_fully_vaccinated",
            "new_vaccinations",
            "new_vaccinations_smoothed",
            "total_vaccinations_per_hundred",
            "people_vaccinated_per_hundred",
            "people_fully_vaccinated_per_hundred",
            "new_vaccinations_smoothed_per_million",
            "population",
        ]
    ]
    return selection


def getCountryData(country: str = "Canada") -> pd.DataFrame:
    covid_df = loadDataset()
    country_df = covid_df.loc[covid_df["location"] == country].set_index("date")
    return country_df


def getCountrySummary(country: str = "Canada") -> str:
    country = country.title()
    countryRemap = {
        "USA": "United States",
        "US": "United States",
        "UK": "United Kingdom",
        "UAE": "United Arab Emirates",
    }
    if country.upper() in countryRemap:
        country = countryRemap[country.upper()]
    country_df = getCountryData(country)
    country_df = country_df[
        [
            "new_vaccinations",
            "people_vaccinated",
            "people_vaccinated_per_hundred",
            "people_fully_vaccinated",
            "people_fully_vaccinated_per_hundred",
        ]
    ]
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


def main() -> None:
    print(getCountrySummary("US"))
    print(getCountrySummary("UK"))
    print(getCountrySummary("Canada"))
    print(getCountrySummary("India"))


if __name__ == "__main__":
    main()
