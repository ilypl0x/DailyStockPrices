import requests
from datetime import datetime, timedelta
import pandas as pd
import io
import json
import os
import matplotlib.pyplot as plt


def download_hist_prices(ticker):


    today = datetime.now()
    today_str = today.strftime("%Y-%m-%d") + ' 09:31:47'
    period2 = int(datetime.timestamp(datetime.strptime(today_str, "%Y-%m-%d %H:%M:%S")))

    twenty_day = today - timedelta(weeks = 52)
    twenty_day_str = twenty_day.strftime("%Y-%m-%d") + ' 09:31:47'
    period1 = int(datetime.timestamp(datetime.strptime(twenty_day_str, "%Y-%m-%d %H:%M:%S")))

    def create_directory(self,dir):
        if not os.path.exists(dir):
            os.makedirs(dir)

    url_hist = "https://query1.finance.yahoo.com/v7/finance/download/{0}?period1={1}&period2={2}&interval=1d&events=history".format(ticker,period1,period2)
    # logger.info('Gathering the last 30 day historical values for ticker : {0} from URL = {1}'.format(ticker,url_hist))
    resp = requests.get(url_hist)
    if resp.status_code == 200:
        # output = open("test.csv",'wb')
        # output.write(resp.content)
        # output.close()
        resp_content = resp.content
        df = pd.read_csv(io.StringIO(resp_content.decode('utf-8')))
        del df['Open']; del df['High'];del df['Low']; del df['Close']; del df['Volume']

        df['20MA'] = df['Adj Close'].rolling(window=20).mean()
        df['50MA'] = df['Adj Close'].rolling(window=50).mean()
        df['100MA'] = df['Adj Close'].rolling(window=100).mean()

        # df['9EMA'] = df['Adj Close'].ewm(span=9).mean()
        # df['20EMA'] = df['Adj Close'].ewm(span=20).mean()



        ma20 = round((df['20MA'].iloc[-1]),2)  
        ma50 = round((df['50MA'].iloc[-1]),2)  
        ma100 = round((df['100MA'].iloc[-1]),2)                  

        df.plot(x='Date',title=ticker)
        plt.show()
         
    
    return ma20,ma50,ma100


def bitcoin_price():
    data = requests.get('https://api.coindesk.com/v1/bpi/currentprice/BTC.json').json()
    price = data['bpi']['USD']['rate']

    return price

class TreasuryDirect(object):
    def __init__(self,mode):
        self.mode = mode

    def getData(self):

        main_api = 'http://www.treasurydirect.gov/TA_WS/'
        if self.mode == 'announce':
            method = 'securities/announced?format=json&days=7&type='
        elif self.mode == 'auction':
            method = 'securities/auctioned?format=json&days=7&type='            
        else:
            method = None
            print('Invalid input: Please choose either auction or announce')

        products = ['Bill','Note','Bond','CMB','TIPS','FRN']
        data = []
        table_head = ['Cusip','Term','Type','Coupon','IssueDate','MaturityDate','AnnouncementDate','AuctionDate','DatedDate','FirstCpnDate']

        for product in products:
            url = main_api + method + product
            json_data = requests.get(url).json()
            length = len(json_data)
            for i in range(length):
                cusip = json_data[i]['cusip']
                term = json_data[i]['securityTerm']
                stype = json_data[i]['securityType']
                issue_d = json_data[i]['issueDate'][:10]
                maturity_d = json_data[i]['maturityDate'][:10]
                interest = json_data[i]['interestRate']
                announcement_d = json_data[i]['announcementDate'][:10]
                auction_d = json_data[i]['auctionDate'][:10]
                dated_d = json_data[i]['datedDate'][:10]
                first_coup = json_data[i]['firstInterestPaymentDate'][:10]
                data.append([cusip,term,stype,interest,issue_d,maturity_d,announcement_d,auction_d,dated_d,first_coup])

        df = pd.DataFrame(data,columns = table_head)
        return df

# if __name__ in "__main__":
#     print(TreasuryDirect('auction'))