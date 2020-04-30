from bs4 import BeautifulSoup
import requests_html


def get_ticker_price(ticker):

    price_code = 'span[data-reactid="32"]'
    name_code = 'h1[data-reactid="7"]'
    close_code = 'span[data-reactid="35"]'

    url = 'https://in.finance.yahoo.com/quote/' + ticker
    session = requests_html.HTMLSession()
    r = session.get(url)
    soup = BeautifulSoup(r.content, 'lxml')
    price_location = soup.find("div", {"id":"Lead-3-QuoteHeader-Proxy"})

    close = price_location.select(close_code)[0].text
    name = price_location.select(name_code)[0].text
    curr_price = float(price_location.select(price_code)[0].text)

    return close,name,curr_price