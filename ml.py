
import robin_stocks
from robin_stocks import *
import robin_stocks as r

import os
from dotenv import load_dotenv

from tensortrade import *

import pandas as pd
from pandas import *

import ta

import pandas as pd
from tensortrade.agents.agent import Agent
import tensortrade.env.default as default

from tensortrade.data.cdd import CryptoDataDownload
from tensortrade.env.default.renderers import ScreenLogger

from tensortrade.feed.core import Stream, DataFeed, NameSpace
from tensortrade.oms.instruments import USD, BTC
from tensortrade.oms.wallets import Wallet, Portfolio
from tensortrade.oms.exchanges import Exchange
from tensortrade.oms.services.execution.simulated import execute_order
from tensortrade.agents import DQNAgent


import warnings
warnings.filterwarnings("ignore", category=RuntimeWarning) 



load_dotenv()
EMAIL = os.getenv('EMAIL')
PASSWORD = os.getenv('PASSWORD')

login = r.login(EMAIL, PASSWORD)

interval = '5minute'
span = 'day' 

btc_historicals = robin_stocks.get_crypto_historicals('DOGE', interval, span)
price_data = robin_stocks.crypto.get_crypto_quote('DOGE')

    
btc_data = []
for key in btc_historicals:
    data = {
    'date' : float(key['begins_at'].replace('T', '').replace('Z', '').replace(':', '').replace('-', '')),
    'open' : float(key['open_price']),
    'high' : float(key['high_price']),
    'low' : float(key['low_price']),
    'close' : float(key['close_price']),
    'volume' :float(key['volume'])
    }
    btc_data.append(data)
        
data = pd.DataFrame.from_dict(btc_data)
robinhood_btc_data = data.add_prefix('BTC:')


robinhood = Exchange("robinhood", service=execute_order)(
    Stream.source(list(robinhood_btc_data['BTC:close']), dtype="float").rename("USD-BTC"))

robinhood_btc = robinhood_btc_data.loc[:, [name.startswith("BTC") for name in robinhood_btc_data.columns]]

ta.add_all_ta_features(
    robinhood_btc,
    colprefix="BTC:",
    **{k: "BTC:" + k for k in ['open', 'high', 'low', 'close', 'volume']}
)

with NameSpace("robinhood"):
    robinhood_stream = [
        Stream.source(list(robinhood_btc[c]), dtype="float").rename(c) for c in robinhood_btc.columns
    ]


def buying_power():
    profile = robin_stocks.load_phoenix_account(info=None)
    try:
        return float(profile['account_buying_power']['amount'])
    except:
        return 0

ticker = 'BTC'
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

   return amount

portfolio = Portfolio(USD, [
    Wallet(robinhood, buying_power() * USD),
    Wallet(robinhood, crypto_position(ticker) * BTC)
])


feed = DataFeed(robinhood_stream)
feed.compile()


renderer_feed = DataFeed([
    Stream.source(list(data["date"])).rename("date"),
    Stream.source(list(data["open"]), dtype="float").rename("open"),
    Stream.source(list(data["high"]), dtype="float").rename("high"),
    Stream.source(list(data["low"]), dtype="float").rename("low"),
    Stream.source(list(data["close"]), dtype="float").rename("close"), 
    Stream.source(list(data["volume"]), dtype="float").rename("volume") 
])


env = default.create(
    portfolio=portfolio,
    action_scheme="managed-risk",
    reward_scheme="risk-adjusted",
    feed=feed,
    renderer_feed=renderer_feed,
    renderer=default.renderers.PlotlyTradingChart(),
    window_size=20,
)

env.observer.feed.next()

agent = DQNAgent(env)

agent.train(n_episodes=2, n_steps=288, render_interval=288)















