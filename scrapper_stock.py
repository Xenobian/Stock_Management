import requests
import json
from bs4 import BeautifulSoup
from decimal import Decimal

def stock_data(symbol):
    #getting content from NSE website and applying bs4 functions over it
    url = 'https://www1.nseindia.com/live_market/dynaContent/live_watch/get_quote/GetQuote.jsp?symbol='+str(symbol)+'&illiquid=0&smeFlag=0&itpFlag=0#'
    response = requests.get(url,headers={'User-Agent': 'Mozilla/5.0'})
    html = response.content
    soup = BeautifulSoup(html,features="html5lib")

    #extracting the information in JSON
    data = json.loads(soup.find(id='responseDiv').text) 
    
    #storing the data in the form of a dictionary
    stock_info = {}
    price = data['data'][0]['lastPrice'] 
    stock_info['stock_price'] = Decimal(price.replace(',',''))
    stock_info['high_52_week'] =  data['data'][0]['high52']
    stock_info['low_52_week'] =  data['data'][0]['low52']
    stock_info['market_cap'] =  data['data'][0]['cm_ffm']
    stock_info['date'] = data['tradedDate']
    stock_info['companyName'] = data['data'][0]['companyName']
    
    #returning the dictionary to the calling function
    return stock_info


