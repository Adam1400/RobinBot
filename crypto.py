
import robin_stocks
from robin_stocks import *
import robin_stocks as r

import os
from dotenv import load_dotenv




import tulipy as ti

import threading

import numpy as np

from datetime import datetime

import sys

import time



rsi_check = []
macd_check = [0,0,0,0,0]
macd_swap = [0,0]
macd_cross_up = False
macd_cross_down = False
high_macd = False
candle_check = [0,0]
candle_update = False
candle_color = ""
trend_check = []
adx_check = []
high_delta = 0
low_delta = 0
avg_rsi_low = 0
low_macd = False
low_rsi = False
high_rsi = False

starting_amount = 0
gains = 0
price_high = 0
stop_loss = 0
period = 5
profit = 0
position = 0
total_profit = 0

cross_up = False
cross_down = False
swing_low = 0

passed = 0
candle = 0
candles = []

epoc = 0

ema_diff = 0

load_dotenv()
EMAIL = os.getenv('EMAIL')
PASSWORD = os.getenv('PASSWORD')

login = r.login(EMAIL, PASSWORD)


def current_time():
    now = datetime.now()
    day = now.strftime("%A")
    date = now.strftime("%m/%d/%Y")
    localtime = now.strftime("%I:%M:%S %p")
    return localtime + ' | ' + day + ' | ' + date

def get_quote():
    global current_market_price
    global current_bid_price
    global current_ask_price
    price_data = robin_stocks.crypto.get_crypto_quote(ticker)
    
    quote = float(price_data['mark_price'])
    bid = float(price_data['bid_price'])
    ask = float(price_data['ask_price'])

    current_market_price = round(quote, 2)
    current_bid_price = round(bid, 2)
    current_ask_price = round(ask, 2)
 

def get_historicals():
    global current_close_price
    global close_price_historicals
    global high_price_historicals
    global low_price_historicals
    global open_price_historicals

    global candle_check
    global candle_update
    global candle_color
    global swing_low

    #interval = '5minute'
    #span = 'day' 

    #interval = '15second'
    #span = 'hour' 

    interval = 'hour'
    span = 'week' 

    historicals = robin_stocks.get_crypto_historicals(ticker, interval, span)

    close_prices = []
    high_prices = []
    low_prices = []
    open_prices = []

    for key in historicals:
        close = (float(key['close_price']))
        high = (float(key['high_price']))
        low = (float(key['low_price']))
        popen = (float(key['open_price']))
        close_prices.append(close)
        high_prices.append(high)
        low_prices.append(low)
        open_prices.append(popen)
        

    current_close_price = round(close_prices[-1], 2)
    close_price_historicals = np.array(close_prices)
    high_price_historicals = np.array(high_prices)
    low_price_historicals = np.array(low_prices)
    open_price_historicals = np.array(open_prices)

    current_candle = open_price_historicals[-1]
    candle_check.append(current_candle)
    if(len(candle_check) > 2):
        candle_check.remove(candle_check[0])

    if(candle_check[0] == candle_check[1]):
        candle_update = False
    else:
        candle_update = True

    if(close_price_historicals[-1] > open_price_historicals[-1]):
        candle_color = "green"
    else:
        candle_color = "red"

    


def get_ema():
    global short_ema
    global long_ema
    global cross_up
    global cross_down
    global ema_diff

    short = ti.ema(close_price_historicals, 10)
    long = ti.ema(close_price_historicals, 20)

    short_ema = short[-1]
    long_ema = long[-1]

    ema_diff = short_ema - long_ema

    short_cross_up = ti.crossover(short, long)[-1]
    short_cross_down = ti.crossover(long, short)[-1]

    if(short_cross_up == 1):
        cross_up = True
    else:
        cross_up = False

    if(short_cross_down == 1):
        cross_down == True
    else:
        cross_down == False

class Candle:
    def __init__(self, num, color, close, open, cross):
        self.num = num
        self.color = color
        self.close = close
        self.open = open
        self.cross = cross
        
    

def scalp_check():
    global bought
    global entery
    global swing_low
    if(cross_up == True):
        candle = 0
        candle_ls = []
        signal = -1
        
        
        while(candle <= 12 and bought == False):
            get_historicals()
            get_ema()
            
            current_close = close_price_historicals[-1]
            current_open = open_price_historicals[-1]

            thisCandle = Candle(candle, candle_color, current_close, current_open, False)

            print(thisCandle.num, thisCandle.color, thisCandle.open, thisCandle.close)
            
            if(thisCandle.num == 0):
                print("wait for next")

            else:

                if(thisCandle.num == 1):
                    if(thisCandle.close < short_ema):
                        print("1st candle below ema")
                        document("BUY", "FAILED | 1st candle below ema", 0)
                        break

                
                if(ema_diff > 100):
                    if(thisCandle.color == "red"):
                        signal = thisCandle.num + 1
                    if(thisCandle.num == signal):
                        if(thisCandle.color == "green"):
                            if(candle_ls[-1].color =="red"):
                                buy("Red then Green")
                                break
                            elif(candle_ls[-1].close > short_ema and candle_ls[-1].color =="green"):
                                buy("Green Cross then Green")
                                break
                        else:
                            signal = thisCandle.num + 1
                
                    


                    if(len(candle_ls) > 3):
                        redcount = 0
                        greencount = 0
                        for cndl in candle_ls:
                            if(cndl.color == "red"):
                                redcount += 1
                                greencount -= 1
                            else:
                                greencount += 1


                        if(greencount >= 4):
                            buy("4 Green")
                            break 
                            
                else:
                    if(thisCandle.num >= 2):
                        print("macd too low")
                        document("BUY", "FAILED | ema dropped too low", 0)
                        break 

            
            cycles = 0
            while(candle_update == False):
                current_close = close_price_historicals[-1]
                get_historicals()
                get_ema()

                print("waiting on next candle", ema_diff, end=" | ")
                for x in candle_ls:
                    print(x.num ,x.color, end=" , ")
                sys.stdout.flush()

                print(thisCandle.num , thisCandle.color)
                
                for x in range(abs(round(ema_diff))):
                    time.sleep(1)
                    print(".", end="")
                    sys.stdout.flush()

                print()
                


            #update close price
            thisCandle.close = current_close
    
            #check for a cross
            if(thisCandle.open > short_ema and thisCandle.close < short_ema or thisCandle.open < short_ema and thisCandle.close > short_ema):
                        thisCandle.cross = True

            #update color too.....?
            if(thisCandle.close > thisCandle.open):
                thisCandle.color = "green"
            else:
                thisCandle.color = "red"


            candle_ls.append(thisCandle)

            print()
            candle +=1

    

def buying_power():
    profile = robin_stocks.load_phoenix_account(info=None)
    try:
        return float(profile['account_buying_power']['amount'])
    except:
        return 0

def crypto_position(ticker):
   id = robin_stocks.crypto.get_crypto_positions('currency')
   index = 0
   amount = 0
   for item in id:
        if(item['code'] == ticker):
           try:
                amount = float(robin_stocks.crypto.get_crypto_positions()[index]['quantity_available'])
           except:
               amount = 0
        else:
            index += 1

   return amount * current_market_price

def state_check():
    global bought
    global entery
    global starting_amount
    global swing_low

    get_historicals()
    get_quote()
    starting_amount = get_crypto_entery(ticker)

    if(crypto_position(ticker) > 6):
        bought = True
        entery = starting_amount * (current_market_price / crypto_position(ticker))
        swing_low = ti.min(close_price_historicals, 12)[-1]
        if(entery < swing_low):
            swing_low = (entery + swing_low)/2
    else:
        bought = False

def buy(condition):
    global bought
    global entery
    global starting_amount
    global swing_low
    bp = 250
    #bp = buying_power() - (buying_power()* 0.012) 
    attempts = 0
    #max_attempts = 10
    max_attempts = round(buying_power() / bp)

    buy_order = robin_stocks.order_buy_crypto_by_price(ticker, bp , jsonify=False)
    

    while(buy_order.status_code != 200 and attempts < max_attempts):
        buy_order = robin_stocks.order_buy_crypto_by_price(ticker, bp, jsonify=False)
        
        attempts += 1
        print("buy pending")
        time.sleep(1)

    if(attempts == max_attempts):
        if(crypto_position(ticker) > 6):
            bought = True
            entery = get_crypto_entery(ticker) * (current_market_price / crypto_position(ticker))
            starting_amount = get_crypto_entery(ticker)
            document("BUY", condition, entery) 
            swing_low = ti.min(close_price_historicals, 12)[-1] 
        else:
            robin_stocks.cancel_all_crypto_orders()
            bought = False
            document("BUY", "FAILED", 0)
                               
    else:
        if(crypto_position(ticker) > 6):
            bought = True
            entery = get_crypto_entery(ticker) * (current_market_price / crypto_position(ticker))
            starting_amount = get_crypto_entery(ticker)
            document("BUY", condition, entery)
            swing_low = ti.min(close_price_historicals, 12)[-1] 
        else:
            robin_stocks.cancel_all_crypto_orders()
            bought = False
            document("BUY", "FAILED", 0)
    

def sell(condition):
    global bought
    global entery
    global total_profit

    price = current_market_price

    cp = crypto_position(ticker) - 5

    sell_order = robin_stocks.order_sell_crypto_by_price(ticker, cp , jsonify=False)
    
    attempts = 0
    max_attempts = 10

    while(sell_order.status_code != 200 and attempts < max_attempts):
        sell_order = robin_stocks.order_sell_crypto_by_price(ticker, cp , jsonify=False)
        attempts += 1
        print("Sell pending")
        time.sleep(1)
                    
    if (attempts == max_attempts):
        if(crypto_position(ticker) < 6):
            profit = ((price - entery)/price) * cp
            total_profit = total_profit + profit
            bought = False
            entery = 0
            document("SELL", condition, total_profit) 
                            
        else:
            robin_stocks.cancel_all_crypto_orders()
            bought = True
            document("SELL", "FAILED", 0)
                         
    else:
        if(crypto_position(ticker) < 6):
            profit = ((price - entery)/price) * cp
            total_profit = total_profit + profit
            bought = False
            entery = 0
            document("SELL", condition, total_profit)
              
        else:
            robin_stocks.cancel_all_crypto_orders()
            bought = True
            document("SELL", "FAILED", 0)
    


def get_crypto_entery(ticker):
    id = robin_stocks.crypto.get_crypto_positions('currency')
    index = 0
    for item in id:
        if (item['code'] == ticker):       
            return float(robin_stocks.crypto.get_crypto_positions('cost_bases')[index][0]['direct_cost_basis'])
        else:
            index +=1

    return -1                           

def document(type, condition, ammount):
    if(condition == "FAILED"):
        p = str(current_time()) + " | " + condition + " ==> " + type +"\n"  
    if(condition != "FAILED" and type == "BUY"):
        p = str(current_time()) + " | " + condition + " ==> " + type + " | $" + str(ammount) +"\n"  
    if(condition != "FAILED" and type == "SELL"):
        p = str(current_time()) + " | " + condition + " ==> " + type + " | profit ==> $" + str(ammount) +"\n"  

    print(condition, type)
    f = open(ticker+'-transactions.txt', "a")
    f.write(p)
    f.close()

def get_gains():
    global gains
    global starting_amount
    global bought

    if(bought == True): 
        if(starting_amount < 6):
            starting_amount = get_crypto_entery(ticker) 
        
        gains = round((crypto_position(ticker) - starting_amount), 2)
        
    else:
        gains = 0

         

def trade():
    global bought

    #BULLISH ON DOGE STRAT... 
    
    """
    BUY RULES
    """
    if(bought == False):
        print("waiting for entery", ema_diff)
        if(cross_up == True):
            buy("EMA cross up")
        

    """
    SELL RULES
    """
   
    if(bought == True):
        print("waiting for sell", ema_diff, "| gains ==>", gains) 
        if(current_ask_price >= entery + .01 and cross_down == True):
            sell("EMA cross down")
            #take no L's



    sys.stdout.flush()




ticker = "DOGE"

# check if you are already in
state_check()

while(True):
   
        

        qt = threading.Thread(target=get_quote, args=( ))
        ht = threading.Thread(target=get_historicals, args=())
        emaT = threading.Thread(target=get_ema, args=())
        gainsT =threading.Thread(target=get_gains, args=())
        
    
        
        tradet = threading.Thread(target=trade, args=())


        qt.start()
        ht.start()
        gainsT.start()

        qt.join()
        ht.join()
        gainsT.join()


        emaT.start()

        emaT.join()
        

        tradet.start()
        tradet.join()

        #need epoc to reduce internet usage lamo
        weight = 1
        if current_market_price < 1:
            weight = 30000

        epoc = round(abs(ema_diff * weight))
        for x in range(epoc):
            time.sleep(1)
            print(".", end="")
            sys.stdout.flush()
            

        print()
        


        


    

