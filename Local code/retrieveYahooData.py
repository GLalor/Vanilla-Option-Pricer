import json
import datetime
import urllib
from urllib.request import urlopen


def main(ticker):
    try:
        if "." in ticker:  # some tickers in list have "." when not needed
            ticker = ticker.replace(".", "")  # Removing "."
        url = createYahooUrlWithDate(ticker)
        if url:
            data = urlopen(url)
            data = json.loads(data.read().decode())
            return data
        return False  # false if url is false
    except urllib.error.HTTPError as err:
        if err.code == 404:
            return False
        else:
            return False
    except urllib.error.URLError as err:
        return False


def createYahooUrlWithDate(optionTicker):
    url = "https://query2.finance.yahoo.com/v7/finance/options/" + optionTicker
    data = urlopen(url)
    data = json.loads(data.read().decode())
    expirationDates = data['optionChain']['result'][0]['expirationDates']
    expDate = 0
    if expirationDates:
        for item in expirationDates:
            dt = datetime.datetime.fromtimestamp(
                item) - datetime.datetime.now()
            if dt.days > 0:  # should run the day before but is seen as 0 days and number of hours
                expDate = item
                break
        return url + "?date=" + str(expDate)
    return False  # false if no expiration dates hence no options


# Stops code being run on import
if __name__ == "__main__":
    main()
