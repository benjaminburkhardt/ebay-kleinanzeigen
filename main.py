import datetime
import os
import re
import sys
import argparse

import requests
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.background import BackgroundScheduler
from bs4 import BeautifulSoup
from telegram import Update, Message
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from enum import Enum

import utils

# jobstores = {
#     'default': SQLAlchemyJobStore(url='sqlite:///jobs.sqlite')
# }
# TODO: re-enable SQLite storage for persistency
# scheduler = BackgroundScheduler(jobstores=jobstores)
scheduler = BackgroundScheduler()
scheduler.start()

last_items_kleinanzeigen = {}
last_items_mobile = {}
tag = ""
INTERVAL_MINS = 10

logger = utils.get_logger()
parser = argparse.ArgumentParser(description='Telegram bot to notify about new articles')

class Item:
    def __init__(self, title, price, torg, url, date, image, tag):
        self.title = title
        self.price = price
        self.torg = torg
        self.url = 'https://www.ebay-kleinanzeigen.de' + url
        self.date = date
        self.image = image
        self.tag = tag

    def __repr__(self):
        return f'{self.title} \n {self.price}€ \n {self.date}'

    def __str__(self):
        result = f'{self.title} \n{self.price}.000€'
        if self.torg:
            result += ' VB'
        #result += f'\n{self.date}\n'
        result += f'\n{self.tag}\n'
        result += self.url
        result += '\n'
        return result

class Website(Enum):
    KLEINANZEIGEN = 1
    MOBILEDE = 2

def is_womo(item: Item):
    if "Wohnwagen" in item.title:
        return False
    return True

def get_items_per_url_kleinanzeigen(url):
    log = utils.get_logger()
    # Simulate browser headers
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36',
        'Host': 'www.ebay-kleinanzeigen.de',
        'Accept': '*/*',
    }

    res = requests.get(url, headers=headers)
    text = res.text

    articles = re.findall('<article(.*?)</article', text, re.S)
    log.info(f"Articles length {len(articles)}")
    items = []
    for item in articles:
        if 'ref="/pro/' in item:
            # This is ad block, skip
            continue

        # Checking if article is a "TOP" article/ad, currently evaluating, but probably identifying by price is enough
        #        try:
        #            test = re.findall('icon icon-smaller icon-feature-topad.*?</i>(.*?)</', item, re.S)[0].strip()
        #            log.info("werbung")
        #            continue
        #        except Exception as e:
        #            # regular entry, do nothing

        soup = BeautifulSoup(item, 'html.parser')

        # Name
        soup_result = soup.find_all("a", {"class": 'ellipsis'})
        if len(soup_result) > 0:
            url = soup_result[0]['href']
            name = soup_result[0].text
        else:
            continue

        #Price
        price_line = re.findall('aditem-main--middle--price.*?>(.*?)</p>', item, re.S)
        if len(price_line) > 0:
            price_line = price_line[0]
        else:
            price_line = "0"
        torg = 'VB' in price_line
        price = None
        if prices := re.findall(r'\d+', price_line, re.S):
            price = int(prices[0])

        # Date
        date = datetime.datetime.now()
        try:
            date = re.findall('icon icon-small icon-calendar-open.*?</i>(.*?)</', item, re.S)[0].strip()
            if '{' in date or '<' in date or 'Heute' in date:
                date = datetime.datetime.now()
            elif 'Gestern' in date:
                date = datetime.datetime.now() - datetime.timedelta(days=1)
        except Exception as e:
            # If there is no date - it's some highlighted/"top" item
            log.info("Skipped ad..")
            continue

        # Tag
        try:
            tag = re.findall('simpletag tag-small">(.*?)</', item, re.S)[0].strip()
        except Exception as e:
            log.info("Could not get tag...")

        # Image
        try:
            image = re.findall('imgsrc="(.*?)"', item, re.S)[0].strip()
        except Exception as e:
            logger.error(f'No image\n\t{item}')
            continue
        log.info("Found & added URL: " + url)
        items.append(Item(name, price, torg, url, date, image, tag))
    return items

def get_items_per_url_mobilede(url):
    # TODO: mobile.de blocks using CAPTCHAs :(
    log = utils.get_logger()
    # Simulate browser headers
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36',
        'Host': 'suchen.mobile.de',
        'Accept': '*/*',
    }

    res = requests.get(url, headers=headers)
    text = res.text
    print(text)

    articles = re.findall('link--muted no--text--decoration result-item(.*?)</a', text, re.S)
    #articles = re.findall('<article(.*?)</article', text, re.S)
    log.info(f"Articles length {len(articles)}")
    items = []
    for item in articles:
        print(item)
        break
        if 'ref="/pro/' in item:
            # This is ad block, skip
            continue

        # Checking if article is a "TOP" article/ad, currently evaluating, but probably identifying by price is enough
        #        try:
        #            test = re.findall('icon icon-smaller icon-feature-topad.*?</i>(.*?)</', item, re.S)[0].strip()
        #            log.info("werbung")
        #            continue
        #        except Exception as e:
        #            # regular entry, do nothing

        soup = BeautifulSoup(item, 'html.parser')

        # Name
        soup_result = soup.find_all("a", {"class": 'ellipsis'})
        if len(soup_result) > 0:
            url = soup_result[0]['href']
            name = soup_result[0].text
        else:
            continue

        #Price
        price_line = re.findall('aditem-main--middle--price.*?>(.*?)</p>', item, re.S)
        if len(price_line) > 0:
            price_line = price_line[0]
        else:
            price_line = "0"
        torg = 'VB' in price_line
        price = None
        if prices := re.findall(r'\d+', price_line, re.S):
            price = int(prices[0])

        # Date
        date = datetime.datetime.now()
        try:
            date = re.findall('icon icon-small icon-calendar-open.*?</i>(.*?)</', item, re.S)[0].strip()
            if '{' in date or '<' in date or 'Heute' in date:
                date = datetime.datetime.now()
            elif 'Gestern' in date:
                date = datetime.datetime.now() - datetime.timedelta(days=1)
        except Exception as e:
            # If there is no date - it's some highlighted/"top" item
            log.info("Skipped ad..")
            continue

        # Tag
        try:
            tag = re.findall('simpletag tag-small">(.*?)</', item, re.S)[0].strip()
        except Exception as e:
            log.info("Could not get tag...")

        # Image
        try:
            image = re.findall('imgsrc="(.*?)"', item, re.S)[0].strip()
        except Exception as e:
            logger.error(f'No image\n\t{item}')
            continue
        log.info("Found & added URL: " + url)
        items.append(Item(name, price, torg, url, date, image, tag))
    return items

def start(update, context):
    """Send a message when the command /start is issued."""
    log = utils.get_logger()
    log.info('Start')
    update.message.reply_text('Send me a search url, for example:')
    update.message.reply_text('https://www.ebay-kleinanzeigen.de/s-wohnwagen-mobile/anzeige:angebote/preis:15000:35000/c220+wohnwagen_mobile.ez_i:2005%2C')
    update.message.reply_text('https://suchen.mobile.de/fahrzeuge/search.html?cn=DE&isSearchRequest=true&od=down&p=15000%3A35000&s=Motorhome&sb=doc&vc=Motorhome')
def error(update, context):
    """Log Errors caused by Updates."""
    print('Update "%s" caused error "%s"', update, context.error)

def echo(update: Update, context):
    msg: Message = update.message

    log = utils.get_logger()
    log.info('Started echo')

    url = update.message.text
    chat_id = update.effective_chat.id

    if "ebay-kleinanzeigen" in url:
        site = Website.KLEINANZEIGEN
        last_items = last_items_kleinanzeigen
    elif "mobile.de" in url:
        site = Website.MOBILEDE
        last_items = last_items_mobile
    else:
        log.error("Invalid URL")
        msg.reply_text("Invalid URL")
        return
    log.info("last_items_kleinanzeigen: " + str(last_items_kleinanzeigen))
    log.info("last_items_mobile: " + str(last_items_mobile))

    if chat_id not in last_items:
        # Nothing here, schedule
        scheduler.add_job(echo, trigger='interval', args=(update, context), minutes=INTERVAL_MINS, id=str(chat_id))
        log.info('Scheduled job')
        last_items[chat_id] = {'last_item': None, 'url': url}

    if site == Website.KLEINANZEIGEN:
        items = get_items_per_url_kleinanzeigen(url)
    elif site == Website.MOBILEDE:
        items = get_items_per_url_mobilede(url)

    for item in items:
        if chat_id in last_items and item.url == last_items[chat_id]['last_item']:
            log.info('Found last item, breaking the loop...')
            break
        if is_womo(item):
            msg.reply_text(str(item))
            # update.message.reply_photo(item.image)
        else:
            log.info("Skipped non womo: " + item.title)
    last_items[chat_id] = {'last_item': items[0].url, 'search_url': url}
    log.info(last_items)

def main():
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True to use the new context based callbacks
    # Post version 12 this will no longer be necessary

    # Read arguments
    parser.add_argument('--token', type=ascii,
                        help='Telegram token for bot')
    parser.add_argument('--opt_minutes', type=int,
                        help='Check ebay each x minutes')
    args = parser.parse_args()

    BOT_TOKEN = str(args.token.strip('\''))
    global INTERVAL_MINS
    if args.opt_minutes:
        INTERVAL_MINS = args.opt_minutes

    print("Checking each " + str(INTERVAL_MINS) + " min")

    updater = Updater(bot=utils.get_bot(BOT_TOKEN), use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text, echo))

    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()
    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()

if __name__ == '__main__':
    main()
