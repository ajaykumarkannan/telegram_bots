#!/usr/bin/env python3
from telegram import Update
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    CallbackContext,
)
from telegram import InputMediaPhoto, ParseMode, ChatAction
import time
import logging
from telegram_token_key import m_token
from covid.lib.errors import CountryNotFound
import covid_stats_plotter
import vaccinations
import global_vaccinations
import os
import datetime

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logger = logging.getLogger(__name__)

# Define a few command handlers. These usually take the two arguments update and
# context. Error handlers also receive the raised TelegramError object in error.
def help(update: Update, _: CallbackContext) -> None:
    update.message.reply_text(
        "Help Menu:\n"
        "/now [country] [state/province] - to get the data at this moment\n"
        "/repeat [hours] [country] [state/province] - to set a recurrence.\n"
        "/daily HH:MM [country] [state/province] - to set a daily schedule in UTC time\n"
        "/jobs - List the scheduled jobs\n"
        "/delete [N] - Delete Nth job\n"
        "/delete all - Delete all jobs\n"
        "/country [country] -  to print stats for a given country\n"
        "/country_list -  List all of the countries\n"
        "/region [region] -  print stats for a given region\n"
        "/region_list -  print a list of regions\n"
        "/help -  to print this menu\n"
        "/info -  to print the README"
    )


def info(update: Update, _: CallbackContext) -> None:
    readme = open("README.md", "r")
    outString = readme.read()
    update.message.reply_text(outString)
    readme.close()


def getGraphs(country="canada", state="ontario"):
    images = []
    if country != None:
        images.append(covid_stats_plotter.outputCountryImage)
        covid_stats_plotter.plotCountryCases(country)
    if state != None:
        images.append(covid_stats_plotter.outputStateImage)
        covid_stats_plotter.plotStateCases(state)

    if country == "canada":
        images.append(vaccinations.canadaVaccineImage)
        vaccinations.plotCanadaVaccinations()
    else:
        images.append(global_vaccinations.countryVaccineImage)
        global_vaccinations.plotCountryVaccinations(country)

    if state != None and vaccinations.plotVaccinations(state):
        images.append(vaccinations.stateVaccineImage)

    imageFiles = []
    for image in images:
        ImageFile = open(image, "rb")
        MediaImage = InputMediaPhoto(ImageFile)
        imageFiles.append(MediaImage)
        ImageFile.close()
        os.remove(image)

    return imageFiles


def getSummary(country=None, state=None) -> str:
    countrySummary = ""
    stateSummary = ""
    if country != None:
        country = country.lower()
        countrySummary = covid_stats_plotter.getCountrySummary(country)
    if state != None:
        state = state.lower()
        stateSummary = covid_stats_plotter.getRegionSummary(state)
        stateSummary += "\n" + vaccinations.getSummary(state)

    if country == "canada":
        countrySummary += "\n" + vaccinations.getCanadaSummary()
    else:
        countrySummary += "\n" + global_vaccinations.getCountrySummary(country)

    return countrySummary + stateSummary


def alarm(context: CallbackContext, country="canada", state="ontario") -> None:
    """Send the alarm message."""
    try:
        context.bot.send_chat_action(
            context.job.context, action=ChatAction.UPLOAD_PHOTO
        )
        context.bot.send_media_group(context.job.context, getGraphs(country, state))
        context.bot.send_message(
            context.job.context, text=getSummary(country, state), parse_mode="HTML"
        )
    except:
        context.bot.send_message(
            context.job.context, text="Sorry, encountered an error :("
        )


def list_jobs(update: Update, context: CallbackContext) -> None:
    current_jobs = context.job_queue.get_jobs_by_name(str(update.message.chat_id))
    outString = ""
    if not current_jobs:
        outString = "No scheduled jobs"
    else:
        count = 1
        for job in current_jobs:
            outString += str(count) + ": " + str(job.trigger) + "\n"
            count += 1
    update.message.reply_text(outString)


def delete_job(update: Update, context: CallbackContext) -> None:
    current_jobs = context.job_queue.get_jobs_by_name(str(update.message.chat_id))
    if not current_jobs:
        update.message.reply_text("No scheduled jobs")
        return
    else:
        try:
            jobs = []
            if str(context.args[0]) == "all":
                jobs = current_jobs
            else:
                jobs.append(current_jobs[int(context.args[0]) - 1])
            for job in jobs:
                update.message.reply_text("Deleting job: " + str(job.trigger))
                job.schedule_removal()
        except (IndexError, ValueError):
            update.message.reply_text("Job not found.")


def get_once(update: Update, context: CallbackContext) -> None:
    """Add a job to the queue."""
    country = "canada"
    state = "ontario"
    try:
        if len(context.args) >= 1:
            country = str(context.args[0]).lower()
            state = None
        if len(context.args) >= 2:
            state = str(" ".join(context.args[1:])).lower()
        update.message.reply_chat_action(action=ChatAction.UPLOAD_PHOTO)
        update.message.reply_media_group(getGraphs(country=country, state=state))
        update.message.reply_text(
            getSummary(country=country, state=state), parse_mode="HTML"
        )
    except (IndexError, ValueError):
        update.message.reply_text("Usage: /now [country] [region]")
    except:
        update.message.reply_text("Country or State not found")


def daily(update: Update, context: CallbackContext) -> None:
    """Add a job to the queue."""
    chat_id = update.message.chat_id
    try:
        # args[0] should contain the time of day
        time_format = "%H:%M"
        time = datetime.datetime.strptime(str(context.args[0]), time_format)

        country = "canada"
        state = "ontario"
        if len(context.args) >= 2:
            country = str(context.args[1]).lower()
            state = None
        if len(context.args) >= 3:
            state = str(" ".join(context.args[2:])).lower()
        getDataFunc = lambda context: alarm(
            context=context, country=country, state=state
        )
        context.job_queue.run_daily(
            getDataFunc, time.time(), context=chat_id, name=str(chat_id)
        )

        text = "Schedule successfully set!"
        update.message.reply_text(text)

    except (IndexError, ValueError):
        update.message.reply_text(
            "Usage: /daily <HH:MM Time in UTC> [Country] [Region]"
        )


def repeat_timer(update: Update, context: CallbackContext) -> None:
    """Add a job to the queue."""
    chat_id = update.message.chat_id
    try:
        # args[0] should contain the time for the timer in hours
        due = int(context.args[0]) * 3600
        if due < 0:
            update.message.reply_text("Sorry we can not go back to future!")
            return

        country = "canada"
        state = "ontario"
        if len(context.args) >= 2:
            country = str(context.args[1]).lower()
            state = None
        if len(context.args) >= 3:
            state = str(" ".join(context.args[2:])).lower()

        getDataFunc = lambda context: alarm(
            context=context, country=country, state=state
        )
        context.job_queue.run_repeating(
            getDataFunc, due, context=chat_id, name=str(chat_id)
        )

        text = "Recurrance successfully set!"
        update.message.reply_text(text)

    except (IndexError, ValueError):
        update.message.reply_text("Usage: /repeat [hours] [Country] [Region]")


def country_data(update: Update, context: CallbackContext) -> None:
    """Add a job to the queue."""
    chat_id = update.message.chat_id
    try:
        # args[0] should contain the country
        country = " ".join(context.args).title()
        update.message.reply_media_group(getGraphs(country=country, state=None))
        update.message.reply_text(getSummary(country=country), parse_mode="HTML")

    except:
        update.message.reply_text(
            "Usage: /country [country]\n"
            "Check the list of countries to see if your input is not valid"
        )


def country_list(update: Update, context: CallbackContext) -> None:
    """Add a job to the queue."""
    chat_id = update.message.chat_id
    update.message.reply_text(covid_stats_plotter.getListOfCountries())


def region_data(update: Update, context: CallbackContext) -> None:
    """Add a job to the queue."""
    chat_id = update.message.chat_id
    try:
        # args[0] should contain the region
        region = " ".join(context.args).title()

        chat_id = update.message.chat_id
        update.message.reply_media_group(getGraphs(state=region, country=None))
        update.message.reply_text(getSummary(state=region), parse_mode="HTML")

    except:
        update.message.reply_text(
            "Usage: /region [region]\n"
            "Check the list of regions to see if your input is not valid"
        )


def region_list(update: Update, context: CallbackContext) -> None:
    """Add a job to the queue."""
    chat_id = update.message.chat_id
    update.message.reply_text(covid_stats_plotter.getListOfRegions())


def main() -> None:
    """Run bot."""
    # Create the Updater and pass it your bot's token.
    updater = Updater(m_token)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # on different commands - answer in Telegram
    dispatcher.add_handler(CommandHandler("start", help))
    dispatcher.add_handler(CommandHandler("help", help))
    dispatcher.add_handler(CommandHandler("now", get_once))
    dispatcher.add_handler(CommandHandler("repeat", repeat_timer))
    dispatcher.add_handler(CommandHandler("daily", daily))
    dispatcher.add_handler(CommandHandler("country", country_data))
    dispatcher.add_handler(CommandHandler("country_list", country_list))
    dispatcher.add_handler(CommandHandler("region", region_data))
    dispatcher.add_handler(CommandHandler("region_list", region_list))
    dispatcher.add_handler(CommandHandler("info", info))
    dispatcher.add_handler(CommandHandler("jobs", list_jobs))
    dispatcher.add_handler(CommandHandler("delete", delete_job))

    # Start the Bot
    updater.start_polling()

    # Block until you press Ctrl-C or the process receives SIGINT, SIGTERM or
    # SIGABRT. This should be used most of the time, since start_polling() is
    # non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == "__main__":
    main()
