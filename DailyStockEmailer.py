import requests
from bs4 import BeautifulSoup
import requests_html
import pandas as pd
import re
from html_utils import finalize_html_report, ColorDFRows
from email_utils import Emailer
from log_utils import get_logger
from config_utils import get_yaml_params
import csv
from datetime import datetime
from datetime import timedelta
import time


params = get_yaml_params()
logger = get_logger(params)

EMAIL_ENABLED = params['email']['enabled']
ATTACHMENTS_ENABLED = params['email']['attachments']
to = params['email']['to']
subject = params['email']['subject']

price_code = 'span[data-reactid="32"]'
name_code = 'h1[data-reactid="7"]'
close_code = 'span[data-reactid="35"]'

def convert_to_dict(stockscsv):
    raw_data = {}
    with open(stockscsv, 'r') as f:
        info = csv.reader(f)
        logger.info('Successfully opened and read data from {}'.format(stockscsv))
        for stock_purchase in info:
            vwap = 0
            stock = stock_purchase[0]; price = float(stock_purchase[1]); qty=int(stock_purchase[2])
            if stock not in raw_data.keys():
                logger.info('Adding Stock: {} to data dictionary.'.format(stock))
                raw_data[stock] = {'price': [price] ,
                                    'qty': [qty],
                                    'total': qty,
                                    'vwap' : vwap
                                    }
            else:
                logger.info('Stock: {} already exists in data dictionary, appending information accordingly.'.format(stock))
                raw_data[stock]['price'].append(price)
                raw_data[stock]['qty'].append(qty)
                raw_data[stock]['total'] += qty
    return raw_data
                
def get_vwap(raw_data):
    for stock in raw_data:
        sum_of_price = 0
        for i in range(len(raw_data[stock]['price'])):
            cost = raw_data[stock]['price'][i]*raw_data[stock]['qty'][i]
            sum_of_price += cost
        raw_data[stock]['vwap'] = sum_of_price/raw_data[stock]['total']
        logger.info('VWAP calculated successfully for Stock: {}'.format(stock))
    return raw_data

        
def get_current_price(raw_data):
    ticker_list  = raw_data.keys()
    info_list = [['Stock','Qty','Purchase Price','Curr Price','Puchase Value','Curr Value','% Chg']]
    price_orig_total = 0; price_new_total=0

    def calc_percent(new,old):
        percent = round(((new-old)/old)*100,2)
        return percent

    def float_to_money(value):
        money = '${:,.2f}'.format(value)
        return money

    for ticker in ticker_list:
        url = 'https://in.finance.yahoo.com/quote/' + ticker
        logger.info('Getting Stock data from URL: {}'.format(url))
        session = requests_html.HTMLSession()
        r = session.get(url)
        soup = BeautifulSoup(r.content, 'lxml')
        price_location = soup.find("div", {"id":"Lead-3-QuoteHeader-Proxy"})

        close = price_location.select(close_code)[0].text
        name = price_location.select(name_code)[0].text
        curr_price = float(price_location.select(price_code)[0].text)

        total_qty = raw_data[ticker]['total']
        purchase_price = raw_data[ticker]['vwap']
        new_total = total_qty*curr_price
        orig_total = total_qty*purchase_price
        percent = calc_percent(new_total,orig_total)
        price_orig_total += orig_total; price_new_total += new_total


        info_list.append([name,total_qty,float_to_money(purchase_price),float_to_money(curr_price),float_to_money(orig_total),float_to_money(new_total),percent])

    global price_diff_str
    price_diff = price_new_total - price_orig_total
    if price_diff > 0:
        verb = 'Profit'
    else:
        verb = 'Loss'
    price_diff_str = verb + ' : ' + float_to_money(price_diff) + ' as of {}'.format(close.split('  ')[1])

    price_percent = calc_percent(price_new_total,price_orig_total)
    info_list.append(['Total $','','','',float_to_money(price_orig_total), float_to_money(price_new_total),price_percent])
    return info_list



if __name__ in '__main__':


    purchases = convert_to_dict('stocks.csv')
    vwap_purchases = get_vwap(purchases)
    final_info = get_current_price(vwap_purchases)
    title = price_diff_str

    df = pd.DataFrame(final_info, columns = final_info.pop(0))
    df_html = ColorDFRows(df).getColor()

    # df_html = df.to_html(index=False)
    html = finalize_html_report(title, df_html)

    if EMAIL_ENABLED:
        logger.info('Email is enabled - preparing to send.')
        if ATTACHMENTS_ENABLED:
            attachment = params['email']['attachment']
            logger.info('Email is sent with attachments - preparing attachment.')
            Emailer().sendmail(html,to,subject,attachment=attachment)
        else:
            Emailer().sendmail(html,to,subject)
    else:
        logger.info('Email is not enabled.')
