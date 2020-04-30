import pandas as pd
import csv
import sys
import concurrent.futures

sys.path.append('..')
from utils.html_utils import finalize_html_report, ColorDFRows
from utils.email_utils import Emailer
from utils.log_utils import get_logger
from utils.config_utils import get_yaml_params
from utils.bs4_utils import get_ticker_price
from utils.requests_utils import download_hist_prices


params = get_yaml_params()
logger = get_logger(params)

EMAIL_ENABLED = params['email']['enabled']
ATTACHMENTS_ENABLED = params['email']['attachments']
to = params['email']['to']
subject = params['email']['subject']


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
    total_dict  = {'Total':
                        {'orig_total': 0,
                        'new_total': 0,
                        'close': '',
                        'percent': 0,
                        'pnl': 0}
                        }           

    def calc_percent(new,old):
        percent = round(((new-old)/old)*100,2)
        return percent

    def float_to_money(value):
        money = '${:,.2f}'.format(value)
        return money

    def vwap_edit(ticker):
        close,name, curr_price = get_ticker_price(ticker)
        raw_data[ticker]['curr_price'] = curr_price
        raw_data[ticker]['name'] = name
        raw_data[ticker]['orig_total'] = raw_data[ticker]['total']* raw_data[ticker]['vwap']
        raw_data[ticker]['new_total'] = raw_data[ticker]['total']* raw_data[ticker]['curr_price']  
        raw_data[ticker]['percent'] = calc_percent(raw_data[ticker]['new_total'], raw_data[ticker]['orig_total'])
        
        total_dict['Total']['orig_total'] += raw_data[ticker]['orig_total']
        total_dict['Total']['new_total'] += raw_data[ticker]['new_total']
        total_dict['Total']['close'] = close    
        logger.info('Getting Stock data for: {}'.format(ticker))

        # moving_average20d,moving_average50d,moving_average100d = download_hist_prices(ticker)
        # print(moving_average20d,moving_average50d,moving_average100d)

        

    with concurrent.futures.ThreadPoolExecutor() as executor:
            [executor.submit(vwap_edit,ticker) for ticker in ticker_list]

    columns = ['Stock','Qty','Purchase Price','Curr Price','Purchase Value','Curr Value','% Chg']
    df = pd.DataFrame.from_dict(raw_data, orient='index')
    df = df.drop(['price','qty'],axis =1)

    #GET RID OF THE EMPTY SPACE WHEN RESETTING INDEX 
    df = df.set_index(['name'])
    df.reset_index(inplace=True)
    df.columns = columns
    # df =df.rename_axis('Stock',axis="columns")
    # df.index.name = None

    df['Purchase Price'] = df['Purchase Price'].map(float_to_money)
    df['Curr Price'] = df['Curr Price'].map(float_to_money)
    df['Purchase Value'] = df['Purchase Value'].map(float_to_money)
    df['Curr Value'] = df['Curr Value'].map(float_to_money)

    total_dict['Total']['pnl'] = total_dict['Total']['new_total'] - total_dict['Total']['orig_total']
    total_dict['Total']['percent'] = calc_percent(total_dict['Total']['new_total'],total_dict['Total']['orig_total'])
    total_dict['Total']['new_total'] = float_to_money(total_dict['Total']['new_total'])
    total_dict['Total']['orig_total'] = float_to_money(total_dict['Total']['orig_total'])
    # total_dict['Total']['pnl'] = float_to_money(total_dict['Total']['pnl'])

    return total_dict,df



if __name__ in '__main__':


    purchases = convert_to_dict('stocks.csv')
    vwap_purchases = get_vwap(purchases)
    totals, final_info = get_current_price(vwap_purchases)
    df_html = ColorDFRows(final_info).getColor()

    if totals['Total']['pnl'] > 0:
        verb = 'Profit'
        sign = '+'
    else:
        verb = 'Loss'
        sign = '-'
    
    pnl_money = '${:,.2f}'.format(totals['Total']['pnl'])
    price_diff_str = verb + ' : ' + pnl_money + ' (' + sign + str(totals['Total']['percent']) + '% ) as of {}'.format(totals['Total']['close'].split('  ')[1])

    # df_html = df.to_html(index=False)
    title = price_diff_str
    html = finalize_html_report(title, df_html)

    if EMAIL_ENABLED:
        logger.info('Email is enabled - preparing to send.')
        if ATTACHMENTS_ENABLED:
            attachment = params['email']['attachment']
            logger.info('Email is sent with attachments - preparing attachment.')
            Emailer().sendmail(html,to,subject,attachment=attachment)
        else:
            Emailer().sendmail(html,to,subject)
            logger.info('Email successfully sent to: {}'.format(to))
    else:
        logger.info('Email is not enabled.')
