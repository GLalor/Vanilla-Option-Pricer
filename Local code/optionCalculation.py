import json
import datetime
import random
import math
import time
import retrieveYahooData
import writeToHDFS

# Dictionaries for json output
option_prices = {}
results = {}
call_results = {}
put_results = {}


def main(ticker, riskFreeRates):
    option_type = "not set"
    strike_price = 0
    current_value = 0
    volatility = 0.0
    expires = 0
    risk_free_rate = riskFreeRates  # risk free rate from fed
    data = retrieveYahooData.main(ticker)
    option_prices['Ticker'] = ticker
    option_prices['Risk Free Rates'] = risk_free_rate
    # Test if is regularMarketPrice present will move to check if date is
    # present in experationDates when working with dates
    if "regularMarketPrice" in data['optionChain']['result'][0]['quote']:
        current_value = data['optionChain']['result'][0]['quote']['regularMarketPrice']
        data = data['optionChain']['result'][0]['options']
        for option in data:
            calls, puts = option['calls'], option['puts']
        # Assigning variables for calc and running sim
        for call in calls:
            option_type = "Call"
            strike_price = call['strike']           # S(T) price at maturity
            volatility = call['impliedVolatility']
            dt = datetime.datetime.fromtimestamp(
                call['expiration']) - datetime.datetime.now()
            expires = dt.days
            option_prices['ExpirationDate'] = datetime.datetime.fromtimestamp(
                call['expiration']).strftime('%Y-%m-%d')
            runSimulaion(option_type, strike_price, current_value,
                         volatility, risk_free_rate, expires, ticker)
            results[option_type] = call_results
        for put in puts:
            option_type = "Put"
            strike_price = put['strike']            # S(T) price at maturity
            volatility = put['impliedVolatility']
            runSimulaion(option_type, strike_price, current_value,
                         volatility, risk_free_rate, expires, ticker)
            results[option_type] = put_results
            option_prices['Prices'] = results
    else:
        call_results['NA'] = "MISSING DATA"
        put_results['NA'] = "MISSING DATA"
        results[option_type] = call_results
        results[option_type] = put_results
        option_prices['Prices'] = results

    with open('optionPrices.json', 'w') as outfile:
        json.dump(option_prices, outfile)
    writeToHDFS.writeResultHive()


def runSimulaion(
        option_type,
        strike_price,
        current_value,
        volatility,
        risk_free_rate,
        expires,
        ticker):
    start_date = datetime.date.today()
    num_simulations = 10000
    option_prices = []
    for x in range(0, 5):
        times = []
        # 1 .. expires inclusive
        for i in range(1, expires + 1):
            # results from each simulation step
            sim_results = []
            T = i / 365               # days in the future
            times.append(i)
            for rate in risk_free_rate:
                results['RiskFreeRate'] = rate
                for j in range(num_simulations):
                    sim_results.append(
                        sim_option_price(
                            time.time() + j,
                            current_value,
                            rate,
                            volatility,
                            T,
                            strike_price,
                            option_type))
                discount_factor = math.exp(-rate * T)
                option_prices.append(
                    discount_factor * (sum(sim_results) / float(num_simulations)))
                if option_type == "Call":
                    call_results[(
                        str(start_date + datetime.timedelta(days=i)))] = option_prices[i - 1]
                else:
                    put_results[(
                        str(start_date + datetime.timedelta(days=i)))] = option_prices[i - 1]


def call_payoff(asset_price, strike_price):
    return max(0.0, asset_price - strike_price)


def put_payoff(asset_price, strike_price):
    return max(0.0, strike_price - asset_price)


def sim_option_price(
        seed,
        current_value,
        risk_free_rate,
        volatility,
        T,
        strike_price,
        option_type):
    random.seed(seed)
    asset_price = current_value * \
        math.exp((risk_free_rate - .5 * volatility**2) * T +
                 volatility * math.sqrt(T) * random.gauss(0, 1.0))
    if option_type == "Call":
        return call_payoff(asset_price, strike_price)
    else:
        return put_payoff(asset_price, strike_price)


# Stops code being run on import
if __name__ == "__main__":
    main()
