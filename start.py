# Known issues:
# - Internet connectivity is not checked
# - You can't add funds via this program
# - Keyboard shortcuts outside of tab don't exist,
#   ( and even then tab doesn't work for File / Settings / Help )
# - The account_limits / rate_limits aren't currently used
# - Right-click menus don't exist
#
# If for whatever reason something doesn't work with the API,
# https://docs.kraken.com/rest/#section/Changelog and https://status.kraken.com/
# should be referenced to see if anything has changed or is broken.
import base64
import decimal
import hashlib
import hmac
import queue
import sys
import threading
import time
import urllib.parse
from tkinter import ttk, Tk, S, W, DoubleVar, StringVar, IntVar, Listbox, ACTIVE, E, Radiobutton, END, N
from tkinter import messagebox, Menu, Button, Toplevel, TclError, Entry
from tkinter.ttk import Combobox
from tkinter.messagebox import askokcancel, WARNING, showinfo
import requests
from config import api_key_b, api_secret_b, api_url, verify_closing

api_key = base64.b64decode(api_key_b.encode()).decode()
api_secret = base64.b64decode(api_secret_b.encode()).decode()

# https://support.kraken.com/hc/en-us/articles/205893708-Minimum-order-size-volume-for-trading
# Last pulled 2023-02-02
# ---
# To turn each string value to float or int, the following is how to do that:
# minimum_order_sizes is a in this: .. [float(a[x]) if str(float(a[x])) == a[x] else int(a[x]) for x in a]
# ---
# These are the minimum order sizes for the "base currency". The "base currency" is the left currency in each pair.
# If the order is smaller than this, there'll be a volume error.
minimum_order_sizes = {'1INCH': 10, 'AAVE': 0.15, 'ACA': 50, 'ACH': 500, 'ADA': 15, 'ADX': 40, 'AGLD': 20, 'AIR': 700,
                       'AKT': 20, 'ALCX': 0.3, 'ALGO': 20, 'ALICE': 5, 'ALPHA': 50, 'ANKR': 200, 'ANT': 2.5, 'APE': 2,
                       'API3': 3.5, 'APT': 1.25, 'ARPA': 200, 'ASTR': 125, 'ATLAS': 2000, 'ATOM': 0.5, 'AUDIO': 30,
                       'AVAX': 0.4, 'AXS': 0.65, 'BADGER': 2, 'BAL': 1, 'BAND': 3, 'BAT': 20, 'BCH': 0.05, 'BICO': 17.5,
                       'BIT': 17.5, 'BLZ': 85, 'BNC': 50, 'BNT': 15, 'BOBA': 25, 'BOND': 1.5, 'BSX': 60000,
                       'BTC': 0.0001, 'BTT': 7500000, 'C98': 20, 'CELR': 500, 'CFG': 25, 'CHR': 40, 'CHZ': 25,
                       'COMP': 0.2, 'COTI': 65, 'CQT': 50, 'CRV': 10, 'CSM': 1250, 'CTSI': 50, 'CVC': 50, 'CVX': 1.2,
                       'DAI': 5, 'DASH': 0.13, 'DENT': 7000, 'DOGE': 60, 'DOT': 1, 'DYDX': 2.5, 'EGLD': 0.15, 'ENJ': 15,
                       'ENS': 0.4, 'EOS': 5, 'ETC': 0.25, 'ETH': 0.01, 'ETH2.S': 0.001, 'ETHW': 1.5, 'EUL': 1,
                       'EWT': 1.25, 'FARM': 0.15, 'FET': 75, 'FIDA': 10, 'FIL': 1.25, 'FIS': 15, 'FLOW': 5, 'FLR': 5,
                       'FORTH': 1.5, 'FTM': 25, 'FXS': 1, 'GAL': 2.5, 'GALA': 200, 'GARI': 150, 'GHST': 5, 'GLMR': 15,
                       'GMT': 12.5, 'GNO': 0.06, 'GRT': 80, 'GST': 200, 'GTC': 3, 'HDX': 10, 'HFT': 8.5, 'ICP': 1.5,
                       'ICX': 30, 'IDEX': 100, 'IMX': 12, 'INJ': 3, 'INTR': 250, 'JASMY': 1250, 'JUNO': 2.5,
                       'KAR': 22.5, 'KAVA': 5, 'KEEP': 75, 'KEY': 1500, 'KILT': 12, 'KIN': 500000, 'KINT': 6.5,
                       'KNC': 10, 'KP3R': 0.065, 'KSM': 0.2, 'LCX': 125, 'LDO': 5, 'LINK': 0.8, 'LPT': 0.65, 'LRC': 20,
                       'LSK': 7.5, 'LTC': 0.06, 'LUNA': 30000, 'LUNA2': 3, 'MANA': 12.5, 'MASK': 2, 'MATIC': 6,
                       'MC': 12, 'MINA': 10, 'MIR': 35, 'MKR': 0.0075, 'MLN': 0.25, 'MNGO': 250, 'MOVR': 0.65,
                       'MSOL': 0.35, 'MULTI': 1.5, 'MV': 25, 'MXC': 150, 'NANO': 8, 'NEAR': 3, 'NMR': 0.5, 'NODL': 2000,
                       'NYM': 25, 'OCEAN': 35, 'OGN': 50, 'OMG': 5, 'ORCA': 10, 'OXT': 75, 'OXY': 600, 'PARA': 350,
                       'PAXG': 0.003, 'PERP': 12.5, 'PHA': 35, 'PLA': 25, 'POLIS': 30, 'POLS': 15, 'POND': 600,
                       'POWR': 30, 'PSTAKE': 65, 'QNT': 0.05, 'QTUM': 2.5, 'RAD': 3, 'RARE': 35, 'RARI': 2, 'RAY': 25,
                       'RBC': 150, 'REN': 60, 'REP': 1.5, 'REPV2': 1, 'REQ': 50, 'RLC': 6.5, 'RNDR': 10, 'ROOK': 0.35,
                       'RPL': 0.25, 'RUNE': 5, 'SAMO': 2000, 'SAND': 8.5, 'SBR': 5000, 'SC': 2000, 'SCRT': 10,
                       'SDN': 17.5, 'SGB': 400, 'SHIB': 500000, 'SNX': 3, 'SOL': 0.35, 'SPELL': 7500, 'SRM': 20,
                       'STEP': 500, 'STG': 12, 'STORJ': 15, 'STX': 20, 'SUPER': 50, 'SUSHI': 5, 'SYN': 8, 'T': 250,
                       'TBTC': 0.0001, 'TEER': 15, 'TLM': 350, 'TOKE': 5, 'TRIBE': 25, 'TRU': 100, 'TRX': 100,
                       'TVK': 175, 'UMA': 3, 'UNFI': 1.5, 'UNI': 1, 'USDC': 5, 'USDT': 5, 'UST': 250, 'WAVES': 2.5,
                       'WAXL': 5, 'WBTC': 0.0001, 'WOO': 50, 'XCN': 100, 'XLM': 60, 'XMR': 0.05, 'XRP': 12.5, 'XRT': 2,
                       'XTZ': 5, 'YFI': 0.002, 'YGG': 25, 'ZEC': 0.15, 'ZRX': 25,
                       # These additional ones were provided from the following URL:
                       # https://support.kraken.com/hc/en-us/articles/360001185506-How-to-interpret-asset-codes
                       'ETH2': 0.001, 'WAVE': 2.5, 'XETC': 0.25, 'XETH': 0.01, 'XLTC': 0.06, 'XMLN': 0.25, 'XREP': 1.5,
                       'XREPV2': 1, 'XXBT': 0.0001, 'XXDG': 60, 'XXLM': 60, 'XXMR': 0.05, 'xxrp': 12.5, 'XXTZ': 5,
                       'XZEC': 0.15, 'ZAUD': 10, 'ZEUR': 5, 'ZUSD': 5}
# Total credits to specific account types and the amount that those credits come back every second
# TODO - Not used
account_limits = {'starter': {'amount': 60, 'decay': 1},
                  'intermediate': {'amount': 125, 'decay': 2.34},
                  'pro': {'amount': 180, 'decay': 3.75}}
# Edit / Cancel are not 5/10/15/etc. seconds
# They're all less than the specified amount, other than 301 which is greater-than 300
# These rate-limits are also not expecting you to use anything else to interact with the API
# ---
# https://support.kraken.com/hc/en-us/articles/360045239571 for trading rate-limits
# TODO - Setup these other rate limits too
# https://support.kraken.com/hc/en-us/articles/206548367 for all rate-limits
# TODO - Not used
rate_limits = {'place_order': 1,
               'edit': {5: 6, 10: 5, 15: 4, 45: 3, 90: 2, 300: 0, 301: 0},
               'cancel': {5: 8, 10: 6, 15: 5, 45: 4, 90: 2, 300: 1, 301: 0}}


# Taken from https://docs.kraken.com/rest/#section/Authentication/Headers-and-Signature
def get_kraken_signature(urlpath, data, secret):
    post_data = urllib.parse.urlencode(data)
    encoded = (str(data['nonce']) + post_data).encode()
    message = urlpath.encode() + hashlib.sha256(encoded).digest()
    mac = hmac.new(base64.b64decode(secret), message, hashlib.sha512)
    sig_digest = base64.b64encode(mac.digest())
    return sig_digest.decode()


# Attaches auth headers and returns results of a POST request
def kraken_request(uri_path, data):
    headers = {'API-Key': api_key, 'API-Sign': get_kraken_signature(uri_path, data, api_secret)}
    try:
        req = requests.post((api_url + uri_path), headers=headers, data=data)
    except requests.exceptions.ConnectionError:
        return None
    else:
        return req


# https://docs.kraken.com/rest/#tag/Market-Data/operation/getTickerInformation
# This gets volume as well as ask/bid
# Is retrieved at the beginning of program start and every 6~ seconds afterwards
def get_24_hour_volume():
    global ticker_information
    while not last_updates['kill']:
        try:
            all_ticker_pairs = requests.get('https://api.kraken.com/0/public/Ticker').json()['result']
        # TODO - "Exception" is too broad
        except Exception as e:
            if ticker_information['error'] is None:
                ticker_information['error'] = True
                time.sleep(1)
            else:
                time.sleep(6)
        else:
            for each_pair in all_ticker_pairs:
                ticker_information[each_pair] = all_ticker_pairs[each_pair]
            ticker_information['error'] = False
            time.sleep(6)


# This gets all available pairs, and is only retrieved once -- at the start of the program.
def check_available_pairs():
    global available_pairs
    while not last_updates['kill']:
        try:
            the_pairs = requests.get('https://api.kraken.com/0/public/AssetPairs').json()['result']
        # TODO - "Exception" is too broad
        except Exception as e:
            time.sleep(5)
        else:
            break
    available_pairs = the_pairs


# https://docs.kraken.com/rest/#tag/User-Trading/operation/addOrder
# Used to generate buy or sell orders
def generate_order(order_direction: str, volume: str, pair: str, price: str):
    global current_order
    global open_orders
    global last_updates
    # Loop the order until it succeeds. This gets around invalid nonces
    while True:
        order_request = kraken_request("/0/private/AddOrder",
                                       # time.time() is a float by default.
                                       # This removes the decimals with int(),
                                       # and then turns it into a string, which is what's expected by the API.
                                       {"nonce": str(int(time.time()) * 1000),
                                        'ordertype': "limit",
                                        'type': order_direction,
                                        'price': str(price),
                                        'volume': volume,
                                        'pair': pair})
        if order_request.status_code == 200:
            if not order_request.json()['error']:
                print(f'Order request: {order_request.json()}')
                break
            else:
                print("There was an issue in the order:")
                print(f"Order json: {order_request.json()}")
                print(f"Order status code: {order_request.status_code}")
                print("Trying again in 5 seconds")
                time.sleep(5)
        else:
            print("There was an issue in the order:")
            print(f"Order json: {order_request.json()}")
            print(f"Order status code: {order_request.status_code}")
            print("Trying again in 5 seconds")
            time.sleep(5)
    if order_request.status_code == 200:
        if not order_request.json()['error']:
            json_result_order = order_request.json()['result']
            the_txid = json_result_order['txid'][0]
            open_orders[the_txid] = 'No information available yet'
            # TODO - Don't do this on the main thread
            all_current_orders.insert(0, json_result_order['txid'][0])
            # TODO - store order information better
            # Force an update for orders
            last_updates['order'] = 0
            current_order = None


# https://docs.kraken.com/rest/#tag/User-Trading/operation/cancelOrder
# Used to close orders
# Is used when "cancel order" is pressed after selecting an order on the main screen
def close_this_order(txid):
    try:
        cancel_request = kraken_request("/0/private/CancelOrder",
                                        {"nonce": str(int(time.time()) * 1000),
                                         'txid': txid})
    except Exception as e:
        if str(e) != 'EOrder:Unknown order':
            print(f"Issue cancelling order, will not retry. Here's your error: {str(e)}")
        else:
            print("This order can't be cancelled as it's already completed.")
    else:
        if cancel_request is not None:
            if cancel_request.status_code == 200:
                if not cancel_request.json()['error']:
                    json_result_cancel = cancel_request.json()['result']
                    if not cancel_request.json()['error']:
                        # TODO - Don't do this on the main thread
                        all_current_orders.delete(ACTIVE)
                        print(f"Cancelled order: {json_result_cancel}")
                    else:
                        print(f"Issue cancelling order, will not retry. Here's your error: {cancel_request.json()}")
                else:
                    print(f"Issue cancelling order, will not retry. Here's your error: {cancel_request.json()}")
            else:
                print(f"Issue cancelling order, will not retry. Status code was {cancel_request.status_code} for some reason.")
        else:
            print("Connection issue. Will not retry cancelling this order.")


# Get account balance
# Is retrieved at the beginning of program start and every 34~ seconds afterwards
def get_account_balance():
    global current_balance
    while not last_updates['kill']:
        if last_updates['balance'] == 0:
            last_updates['balance'] = (int(time.time()) - 35)
            time.sleep(1)
        time_since_last = (int(time.time()) - last_updates['balance'])
        if time_since_last >= 34:
            resp = kraken_request("/0/private/Balance",
                                  {"nonce": str(int(time.time()) * 1000)})
            if resp is not None:
                if resp.status_code == 200:
                    if not resp.json()['error']:
                        new_current_balance = {'error': False}
                        json_result = resp.json()['result']
                        for each_item in json_result:
                            if decimal.Decimal(json_result[each_item]) != 0:
                                new_current_balance[each_item] = json_result[each_item]
                        current_balance = new_current_balance
                    else:
                        current_balance['error'] = True
                else:
                    current_balance['error'] = True
            else:
                current_balance['error'] = True
            last_updates['balance'] = int(time.time())
        time.sleep(1)


# https://docs.kraken.com/rest/#tag/User-Data/operation/getOpenOrders
# Get new orders
# Is retrieved at the beginning of program start and every 15~ seconds afterwards
def get_open_orders():
    global open_orders
    global all_current_orders
    global current_order
    while not last_updates['kill']:
        if last_updates['order'] == 0:
            last_updates['order'] = (int(time.time()) - 3)
        time_since_last = (int(time.time()) - last_updates['order'])
        if time_since_last >= 5:
            resp = kraken_request("/0/private/OpenOrders",
                                  {"nonce": str(int(time.time() * 1000)), "trades": "true"})
            if resp is not None:
                if resp.status_code == 200:
                    if not resp.json()['error']:
                        new_open_orders = {'error': False}
                        json_result_open = resp.json()['result']["open"]
                        for the_index, each_open_order in enumerate(json_result_open):
                            new_open_orders[each_open_order] = json_result_open[each_open_order]
                        open_orders = new_open_orders
                    else:
                        open_orders['error'] = True
                else:
                    open_orders['error'] = True
            else:
                open_orders['error'] = True
            last_updates['order'] = int(time.time())
        time.sleep(1)


# Is used in the order double-check screen
def check_order_direction():
    if buy_or_sell_box_var.get() == 0:
        return 'buy'
    elif buy_or_sell_box_var.get() == 1:
        return 'sell'


def check_existence_of_all_vars(the_pair, limit_price, the_total_amount,
                                the_interval, trade_type, the_trade_size_percent):
    not_found = []
    # trade_type is either fixed/volume and can't be blank
    # if not the_trade_type:
    # order_direction is either buy/sell and also can't be blank
    # if not order_direction
    if not the_pair:
        not_found.append('coin pair symbol')
    if not limit_price:
        not_found.append('limit price')
    if not the_total_amount:
        not_found.append('total amount')
    if not the_interval:
        not_found.append('second inbetween trades')
    if not the_trade_size_percent:
        if trade_type == 'fixed':
            not_found.append('order size')
        elif trade_type == 'volume':
            not_found.append('volume percent')
    if len(not_found) >= 3:
        not_found[-1] = f'and {not_found[-1]}'
    return not_found


def find_minimum_order_size():
    the_coin_pair = pair_symbol_variable.get()
    if the_coin_pair:
        for each_coin in minimum_order_sizes:
            if the_coin_pair.startswith(each_coin):
                return minimum_order_sizes[each_coin], each_coin
    return None, None


def calculate_order_sizes(trade_type, total_amount_var, trade_size_percent_var):
    if trade_type == 'fixed':
        how_many_each_order = decimal.Decimal(total_amount_var) / decimal.Decimal(trade_size_percent_var)
        return str(how_many_each_order)
    elif trade_type == 'volume':
        how_many_each_order = decimal.Decimal(total_amount_var) * decimal.Decimal(trade_size_percent_var)
        return str(how_many_each_order)


def process_order():
    global this_bot
    global current_order
    global last_updates
    interval = int(this_bot["interval"])
    limit_price = this_bot["limit_price"]
    order_direction = this_bot['direction']
    the_price = get_current_ask_and_buy()
    while not last_updates['kill']:
        # Is there currently an order being done?
        if current_order is None:
            # How many orders are left?
            if this_bot["total_orders"] >= 1:
                # If total orders are at least 1, there's no current orders, and get_current_ask_and_buy() is good,
                # ORDER. Otherwise, sleep for interval
                if the_price >= limit_price:
                    # How much is this order for?
                    the_order_size = this_bot["order_sizes"]
                    pair = this_bot["pair"]
                    if this_bot["total_orders"] != 0:
                        this_bot["total_orders"] -= 1
                        generate_order(order_direction, the_order_size, pair, str(the_price))
                    time.sleep(interval)
                else:
                    time.sleep(interval)
            else:
                time.sleep(interval)
        else:
            time.sleep(interval)


def get_current_ask_and_buy():
    order_direction = check_order_direction()
    limit_price = decimal.Decimal(limit_price_variable.get())
    current_ask = decimal.Decimal(ticker_information[pair_symbol_variable.get()]['a'][1])
    current_bid = decimal.Decimal(ticker_information[pair_symbol_variable.get()]['b'][1])
    if order_direction == 'sell':
        order_sell = decimal.Decimal(current_ask) * decimal.Decimal(0.999)
        the_price = max([limit_price, order_sell])
        return the_price
    else:
        order_buy = decimal.Decimal(current_bid) * decimal.Decimal(0.999)
        the_price = min([limit_price, order_buy])
        return the_price


# Order double-check screen. Presents user with all the information for a just-in-case.
def submit_order_double_check(the_new_order_box):
    global order_wait_time
    global this_bot
    the_trade_type = None
    the_pair = pair_symbol_variable.get()
    order_direction = check_order_direction()
    limit_price = decimal.Decimal(limit_price_variable.get())
    the_total_amount = total_amount_variable.get()
    the_interval = interval_between.get()
    the_trade_size_percent = trade_size_percent.get()
    the_price = get_current_ask_and_buy()
    # fixed - 0
    if trade_or_volume_fixed_checkbox_var.get() == 0:
        the_trade_type = 'fixed'
        order_sizes = calculate_order_sizes(the_trade_type, the_total_amount, the_trade_size_percent)
        if order_direction == 'sell':
            double_check_message = f"You're trying to submit an order with the following info:\n\nOrder direction: {order_direction}\nPair: {the_pair}\nLimit price: {limit_price}\nSell price:{the_price}\nTotal amount: {the_total_amount}\nInterval: {the_interval}\nTrade type: {the_trade_type}\nTotal orders: {the_trade_size_percent}\nOrder sizes: {order_sizes}",
        else:
            double_check_message = f"You're trying to submit an order with the following info:\n\nOrder direction: {order_direction}\nPair: {the_pair}\nLimit price: {limit_price}\nBuy price:{the_price}\nTotal amount: {the_total_amount}\nInterval: {the_interval}\nTrade type: {the_trade_type}\nTotal orders: {the_trade_size_percent}\nOrder sizes: {order_sizes}",
    # else, which can only be 1
    else:
        the_trade_type = 'volume'
        order_sizes = calculate_order_sizes(the_trade_type, the_total_amount, the_trade_size_percent)
        # TODO - Verify these
        if order_direction == 'sell':
            double_check_message = f"You're trying to submit an order with the following info:\n\nOrder direction: {order_direction}\nPair: {the_pair}\nLimit price: {limit_price}\nSell price:{the_price}\nTotal amount: {the_total_amount}\nInterval: {the_interval}\nTrade type: {the_trade_type}\nTrade size percent: {the_trade_size_percent}\nOrder sizes: {order_sizes}",
        else:
            double_check_message = f"You're trying to submit an order with the following info:\n\nOrder direction: {order_direction}\nPair: {the_pair}\nLimit price: {limit_price}\nBuy price:{the_price}\nTotal amount: {the_total_amount}\nInterval: {the_interval}\nTrade type: {the_trade_type}\nTrade size percent: {the_trade_size_percent}\nOrder sizes: {order_sizes}",
    if the_trade_type in ['fixed', 'volume']:
        these_werent_found = check_existence_of_all_vars(the_pair, limit_price, the_total_amount,
                                                         the_interval, the_trade_type, the_trade_size_percent)
        if not these_werent_found:
            if not minimum_amount_warning.get():
                the_new_order_box.lower()
                submitted_verification = askokcancel(title="Does this look right?",
                                                     message=double_check_message,
                                                     icon=WARNING)
                if submitted_verification:
                    current_time_string = str(current_time)
                    these_orders = {'total_orders': int(the_trade_size_percent),
                                    'order_sizes': order_sizes,
                                    'pair': the_pair,
                                    'limit_price': limit_price,
                                    'interval': the_interval,
                                    'direction': order_direction,
                                    'orders': {},
                                    'status': 'not_started'}
                    this_bot = these_orders
                    if int(the_trade_size_percent) >= 2:
                        showinfo(title="Orders processing", message="The orders are now being processed")
                    else:
                        showinfo(title="Order processing", message="The order is now being processed")
                    process_order_thread = threading.Thread(target=process_order, name="process_order").start()
                    q.put(process_order_thread)
                else:
                    the_new_order_box.lift()
                    the_new_order_box.focus_set()
            else:
                the_new_order_box.lower()
                showinfo(title="Order problem", message="The minimum amount warning wasn't followed. Please do so.")
                the_new_order_box.lift()
                the_new_order_box.focus_set()
        else:
            the_new_order_box.lower()
            showinfo(title="Order problem", message=f"You're missing the following: {', '.join(these_werent_found)}")
            the_new_order_box.lift()
            the_new_order_box.focus_set()


# Get more information on the selected order on the main screen
def get_more_info_selected(event):
    the_txid = all_current_orders.get(all_current_orders.curselection()[0])
    if the_txid not in open_orders:
        messagebox.showinfo("Info",
                            "This is a new order and we haven't retrieved the info for it yet.\n\nThe wait time should be at most 15 seconds.")
    else:
        messagebox.showinfo("Info", f"{open_orders[the_txid]}")


# If you press the "cancel order" button on the main screen, this is ran
def cancel_selected_order():
    if all_current_orders.size() >= 1:
        if all_current_orders.curselection():
            the_index = all_current_orders.curselection()[0]
            txid = all_current_orders.get(the_index)
            cancel_this_txid = threading.Thread(target=close_this_order(txid), name="cancel_txid").start()
            q.put(cancel_this_txid)
            # Focus the main window so an order doesn't get cancelled on accident
            main_window.focus_set()
        else:
            messagebox.showinfo("Info", "Cancel won't work if you haven't selected an order.")
    else:
        messagebox.showinfo("Info", "You can't cancel something that doesn't exist.")
        main_window.focus_set()


# An X button was pressed, or you went to File > Exit
def closing_verify():
    if verify_closing:
        if messagebox.askokcancel("Quit", "Would you like to quit?"):
            print("Killing threads, one moment..")
            last_updates['kill'] = True
            main_window.destroy()
    else:
        print("Killing threads, one moment..")
        last_updates['kill'] = True
        main_window.destroy()


# You pressed X for the loading screen
def closing_loading_screen():
    print("Killing threads, one moment..")
    last_updates['kill'] = True
    try:
        loading_screen.destroy()
        main_window.destroy()
    # TODO - Exception is too broad
    except Exception as e:
        print(str(e))


# Help > How-to
def how_do_i():
    messagebox.showinfo("How do I?",
                        f'Create a new order:\nPress "Add New" and supply the information asked.\n\nGet information about an order:\nDouble-click the order in the list.\n\nCancel an order:\nSelect the order from the list and then press "Cancel" and confirm.')


# You pressed cancel in the new order screen
def cancel_new_order(the_order_window):
    the_order_window.destroy()
    main_window.lift()
    main_window.focus_set()


# In new order screen
# it changed the dropdown for pairs depending on if you chose 'buy' or 'sell'
def check_buy_sell_buttons(pair_symbol_dropdown):
    global buy_or_sell_box_var
    pair_symbol_dropdown.set('')
    if buy_or_sell_box_var.get() == 0:
        pair_symbol_dropdown.config(values=show_pairs['buy'])
        total_amount_variable.set('')
    elif buy_or_sell_box_var.get() == 1:
        pair_symbol_dropdown.config(values=show_pairs['sell'])
        total_amount_variable.set('')


# In new order screen
# If fixed is chosen, set "Order size" label.
# - If volume is chosen, set "Volume percent" label.#
#   If pair symbol from dropdown is ALSO chosen, do "Volume percent" + 24h volume from ticker_information
def check_trade_type_buttons(fixed_or_volume, the_pair_symbol_variable):
    if fixed_or_volume.get() == 0:
        percent_label_variable.set("Order size:")
    elif fixed_or_volume.get() == 1:
        if not the_pair_symbol_variable.get():
            percent_label_variable.set("Volume percent:")
        else:
            the_24h_volume = ticker_information[the_pair_symbol_variable.get()]['v'][1]
            volume_percent_string = f'{"Volume percent:":^22}'
            the_24h_volume_string = f'24h v: {int(float(the_24h_volume))}'
            percent_label_variable.set(f"{volume_percent_string}\n{the_24h_volume_string:^22}")
    else:
        percent_label_variable.set("Trade type unselected:")


# New order screen
# When 'limit_price_entry' and 'total_amount_entry' have anything changed ( 'w' mode )
# TODO - It's a known error that you can copy/paste a number with more than one period to get around the limit
def limit_to_just_numbers_and_decimal(*args):
    global limit_price_variable
    global total_amount_variable
    allowed_characters = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '.']
    period_found = False
    temp_variable = ''
    if args[0] == 'PY_VAR1':
        the_limit_price = limit_price_variable.get()
        for each_character in the_limit_price:
            if each_character in allowed_characters:
                if each_character == '.':
                    if period_found:
                        pass
                    else:
                        period_found = True
                        temp_variable += each_character
                else:
                    temp_variable += each_character
        limit_price_variable.set(temp_variable)
        if len(the_limit_price) >= 27:
            while len(the_limit_price) != 26:
                the_limit_price = the_limit_price[:-1]
            limit_price_variable.set(the_limit_price)
    else:
        the_total_amount = total_amount_variable.get()
        minimum_amount, the_coin = find_minimum_order_size()
        if minimum_amount is not None:
            try:
                if minimum_amount > float(the_total_amount):
                    minimum_amount_warning.set(f'{the_coin} has a minimum required amount of {minimum_amount}')
                elif minimum_amount < float(the_total_amount):
                    minimum_amount_warning.set('')
            # This only happens when the total amount is blank
            except ValueError:
                pass
        for each_character in the_total_amount:
            if each_character in allowed_characters:
                if each_character == '.':
                    if period_found:
                        pass
                    else:
                        period_found = True
                        temp_variable += each_character
                else:
                    temp_variable += each_character
        total_amount_variable.set(temp_variable)
        if len(the_total_amount) >= 27:
            while len(the_total_amount) != 26:
                the_total_amount = the_total_amount[:-1]
            total_amount_variable.set(the_total_amount)
        the_minimum_order_size, the_coin = find_minimum_order_size()
        # If trade_size_percent or total_amount_variable are present but fail decimal.Decimal(), print it.
        try:
            if trade_size_percent.get() and total_amount_variable.get():
                try:
                    the_trade_size = decimal.Decimal(trade_size_percent.get())
                except decimal.ConversionSyntax as trade_size_exception:
                    print(trade_size_exception)
                else:
                    try:
                        the_total_amount = decimal.Decimal(total_amount_variable.get())
                    except decimal.ConversionSyntax as total_amount_exception:
                        print(total_amount_exception)
                    else:
                        # buy
                        if trade_or_volume_fixed_checkbox_var.get() == 0:
                            each_per_order = the_total_amount / the_trade_size
                            if the_minimum_order_size > each_per_order:
                                minimum_amount_warning.set(
                                    f"Amount / order size won't meet\n  minimum required amount of {the_minimum_order_size}")
                        # sell will be 1, but it's the only other option.
                        else:
                            each_per_order = the_total_amount * the_trade_size
                            if the_minimum_order_size > each_per_order:
                                minimum_amount_warning.set(
                                    f"Amount * order size won't meet\n  minimum required amount of {the_minimum_order_size}")
        except decimal.DivisionByZero as e:
            minimum_amount_warning.set(
                f"Amount / order size won't meet\n  minimum required amount of {the_minimum_order_size}")
        except TypeError as ee:
            if minimum_amount is None:
                minimum_amount_warning.set(f"Did you forget to select a pair?")
        # TODO - Exception is too broad here
        except Exception as eeee:
            print(f'trade_size_percent_check encountered an error: {str(eeee)}')
            pass


# New order screen
# When interval_entry has anything changed in it ( 'w' mode )
def interval_function(*args):
    global interval_between
    allowed_characters = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
    the_interval = interval_between.get()
    temp_variable = ''
    for each_character in the_interval:
        if each_character in allowed_characters:
            temp_variable += each_character
        interval_between.set(temp_variable)
    # Seeing as a year is 31536000 seconds, this should be fine.
    # There's no chance that we'll be waiting 3+ years inbetween.
    if len(the_interval) >= 9:
        interval_between.set(the_interval[:-1])


# New order screen
# When "trade_size_percent" has anything changed in it ( 'w' mode )
def trade_size_percent_check(*args):
    global trade_size_percent
    the_trade_size_percent = trade_size_percent.get()
    the_total_amount = total_amount_variable.get()
    the_pair_symbol_variable = pair_symbol_variable.get()
    allowed_characters = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '.']
    period_found = False
    temp_variable = ''
    for each_character in the_trade_size_percent:
        if each_character in allowed_characters:
            if each_character == '.':
                if period_found:
                    pass
                else:
                    period_found = True
                    temp_variable += each_character
            else:
                temp_variable += each_character
        trade_size_percent.set(temp_variable)
    if len(the_trade_size_percent) >= 25:
        trade_size_percent.set(the_trade_size_percent[:-1])

    the_minimum_order_size, the_coin = find_minimum_order_size()
    # If trade_size_percent or total_amount_variable are present but fail decimal.Decimal(), print it.
    try:
        if the_trade_size_percent and the_total_amount:
            the_trade_size_decimal = decimal.Decimal(the_trade_size_percent)
            the_total_amount_decimal = decimal.Decimal(the_total_amount)
            # fixed
            if trade_or_volume_fixed_checkbox_var.get() == 0:
                each_per_order = decimal.Decimal(the_total_amount_decimal) / decimal.Decimal(the_trade_size_decimal)
                percentage_math_variable.set(f'Total amount each order: {each_per_order}')
                if the_minimum_order_size > each_per_order:
                    minimum_amount_warning.set(f"Amount * order size won't meet\nminimum required amount of {the_minimum_order_size}")
                else:
                    minimum_amount_warning.set("")
            # volume
            else:
                if the_pair_symbol_variable and the_trade_size_percent:
                    try:
                        the_24_hour_volume = ticker_information[the_pair_symbol_variable]['v'][1]
                        volume_per_order = decimal.Decimal(the_trade_size_percent) * decimal.Decimal(the_24_hour_volume)
                        percentage_math_variable.set(str(volume_per_order))
                        percentage_math_variable.set(f'Total amount each order: {str(volume_per_order)}')
                        if the_minimum_order_size > volume_per_order:
                            minimum_amount_warning.set(f"Amount * order size won't meet\nminimum required amount of {the_minimum_order_size}")
                        else:
                            minimum_amount_warning.set("")
                    except TypeError as ee:
                        percentage_math_variable.set('Calculating volume order size failed.\nCheck pair/percent inputs')
    except(decimal.DivisionByZero, TypeError) as e:
        minimum_amount_warning.set(f"Amount / order size won't meet\nminimum required amount of {the_minimum_order_size}")


# New order screen
# When the pair symbol combobox "pair_symbol_dropdown" changes selection
def pair_symbol_changed(*args):
    the_pair = pair_symbol_variable.get()
    the_24h_volume = ticker_information[the_pair]['v'][1]
    if trade_or_volume_fixed_checkbox_var.get() == 1:
        if not the_pair:
            percent_label_variable.set("Volume percent:")
        else:
            volume_percent_string = f'{"Volume percent:":^22}'
            the_24h_volume_string = f'24h v: {int(float(the_24h_volume))}'
            percent_label_variable.set(f"{volume_percent_string}\n{the_24h_volume_string:^22}")
    for each_asset in current_balance:
        if each_asset != 'error':
            # buy
            if buy_or_sell_box_var.get() == 0:
                if the_pair.endswith(each_asset):
                    the_asset_amount = current_balance[each_asset]
                    total_amount_variable.set(the_asset_amount)
                    break
            # sell
            else:
                if the_pair.startswith(each_asset):
                    the_asset_amount = current_balance[each_asset]
                    total_amount_variable.set(the_asset_amount)
                    break


# THE new order screen. The entire thing.
def create_new_order():
    new_order_box = Toplevel()
    new_order_box.title("Kraken API - New Order Screen")
    # TODO - Set up a different size for Windows
    new_order_box.geometry('390x265')
    new_order_box.maxsize(390, 265)
    new_order_box.minsize(390, 265)
    new_order_box.resizable(False, False)
    new_order_box.config(highlightthickness=0)

    buy_or_sell_box_var.set(1)

    buy_or_sell_label = ttk.Label(new_order_box, text="Buy or sell:")
    buy_or_sell_label.grid(row=1, column=0)

    buy_check_box = Radiobutton(new_order_box, text='Buy', variable=buy_or_sell_box_var,
                                value=0,
                                command=lambda: check_buy_sell_buttons(pair_symbol_dropdown))
    buy_check_box.grid(row=1, column=1, sticky=W)

    sell_check_box = Radiobutton(new_order_box, text='Sell', variable=buy_or_sell_box_var,
                                 value=1,
                                 command=lambda: check_buy_sell_buttons(pair_symbol_dropdown))
    sell_check_box.grid(row=1, column=1, sticky=E)

    pair_symbol_label = ttk.Label(new_order_box, text="Pair symbol:")
    pair_symbol_label.grid(row=2, column=0)

    pair_symbol_dropdown = Combobox(new_order_box, textvariable=pair_symbol_variable)
    pair_symbol_dropdown['state'] = 'readonly'
    pair_symbol_dropdown.grid(row=2, column=1)
    pair_symbol_dropdown.bind("<<ComboboxSelected>>", pair_symbol_changed)
    pair_symbol_dropdown.config(values=show_pairs['sell'])
    pair_symbol_dropdown.set('')

    limit_price_label = ttk.Label(new_order_box, text="Limit price:")
    limit_price_label.grid(row=3, column=0)

    limit_price_entry = Entry(new_order_box, textvariable=limit_price_variable)
    limit_price_entry.grid(row=3, column=1)
    limit_price_variable.trace('w', limit_to_just_numbers_and_decimal)
    limit_price_variable.set('')

    total_amount_label = ttk.Label(new_order_box, text="Total amount to trade:")
    total_amount_label.grid(row=4, column=0)

    total_amount_entry = Entry(new_order_box, textvariable=total_amount_variable)
    total_amount_entry.grid(row=4, column=1)
    total_amount_variable.trace('w', limit_to_just_numbers_and_decimal)
    total_amount_variable.set('')

    interval_label = ttk.Label(new_order_box, text="Seconds inbetween trades:")
    interval_label.grid(row=5, column=0)

    interval_entry = Entry(new_order_box, textvariable=interval_between)
    interval_entry.grid(row=5, column=1)
    interval_between.trace('w', interval_function)
    interval_between.set('')

    trade_type_label = ttk.Label(new_order_box, text="Trade type:")
    trade_type_label.grid(row=6, column=0)

    trade_type_fixed_box = Radiobutton(new_order_box, text='Fixed', variable=trade_or_volume_fixed_checkbox_var,
                                       value=0,
                                       command=lambda: check_trade_type_buttons(trade_or_volume_fixed_checkbox_var,
                                                                                pair_symbol_variable))

    trade_type_volume_box = Radiobutton(new_order_box, text='Volume', variable=trade_or_volume_fixed_checkbox_var,
                                        value=1,
                                        command=lambda: check_trade_type_buttons(trade_or_volume_fixed_checkbox_var,
                                                                                 pair_symbol_variable))
    trade_or_volume_fixed_checkbox_var.set(0)

    # fixed / volume radio buttons
    trade_type_fixed_box.grid(row=6, column=1, sticky=W)
    trade_type_fixed_box.select()

    trade_type_volume_box.grid(row=6, column=1, sticky=E)

    # "Order size" / "Volume percent" / "Volume percent" with label
    trade_size_percent_label = ttk.Label(new_order_box, textvariable=percent_label_variable)
    trade_size_percent_label.grid(row=7, column=0, sticky=S)
    percent_label_variable.set('Order size:')

    trade_size_percent_entry = Entry(new_order_box, textvariable=trade_size_percent)
    trade_size_percent_entry.grid(row=7, column=1)
    trade_size_percent.trace('w', trade_size_percent_check)
    trade_size_percent.set('')

    percentage_math_label = ttk.Label(new_order_box, textvariable=percentage_math_variable)
    percentage_math_label.grid(row=8, column=0, columnspan=2)

    submit_this_order_button = Button(new_order_box, text="Submit order",
                                      command=lambda: submit_order_double_check(new_order_box))
    submit_this_order_button.grid(row=9, column=0, sticky=E)

    cancel_this_order_button = Button(new_order_box, text="Cancel", command=lambda: cancel_new_order(new_order_box))
    cancel_this_order_button.grid(row=9, column=1, sticky=S)

    minimum_amount_warning_label = ttk.Label(new_order_box, textvariable=minimum_amount_warning)
    minimum_amount_warning_label.grid(row=10, column=0, columnspan=2)

    filler_label = ttk.Label(new_order_box, text="")
    filler_label.grid(row=11, column=0)


# TODO
def view_current_settings():
    pass


# TODO
def edit_settings():
    pass


if __name__ == '__main__':
    current_time = str(time.time())
    main_window = Tk()
    main_window.title("Kraken API - Main Screen")
    # For whatever reason, Windows makes the window far larger than it needs to be.
    # geometry is W-E x N-S
    if sys.platform.startswith('win32'):
        main_window.geometry('235x224')
        main_window.maxsize(235, 224)
        main_window.minsize(235, 224)
    elif sys.platform.startswith('linux'):
        main_window.geometry('328x250')
        main_window.maxsize(328, 250)
        main_window.minsize(328, 250)
    main_window.resizable(False, False)
    main_window.config(highlightthickness=0)
    main_window.protocol("WM_DELETE_WINDOW", closing_verify)

    all_current_orders = Listbox(main_window, activestyle='none')

    this_bot = {}
    # internet_available = None
    open_orders = {'error': None}
    show_pairs = {'buy': [], 'sell': []}
    current_balance = {'error': None}
    last_updates = {'balance': 0, 'order': 0, 'kill': False}
    available_pairs = {}
    ticker_information = {'error': None}

    q = queue.Queue()
    open_orders_thread = threading.Thread(target=get_open_orders, name="open_orders").start()
    account_balance_thread = threading.Thread(target=get_account_balance, name="account_balance").start()
    available_pairs_thread = threading.Thread(target=check_available_pairs, name="available_pairs").start()
    ticker_thread = threading.Thread(target=get_24_hour_volume, name="ticker").start()
    q.put(open_orders_thread)
    q.put(account_balance_thread)
    q.put(available_pairs_thread)
    q.put(ticker_thread)

    percent_label_variable = StringVar()
    percent_label_variable.set("Order size:")
    limit_price_variable = StringVar()
    total_amount_variable = StringVar()
    trade_or_volume_fixed_checkbox_var = IntVar()
    trade_or_volume_fixed_checkbox_var.set(0)
    minimum_amount_warning = StringVar()
    percentage_math_variable = StringVar()
    order_wait_time = 0
    current_order = None

    # to buy or sell
    buy_or_sell_box_var = IntVar()

    # what actually stores whether it's buy or sell
    buy_or_sell = StringVar()

    total_amount = DoubleVar()
    # minimum amount of time between trades
    interval_between = StringVar()
    # percent of interval volume or total amount, depending on trade_size_type
    trade_size_percent = StringVar()

    pair_symbol_variable = StringVar()
    loading_text = StringVar()
    loading_text.set("\n\n\nLoading.. one moment!")
    loading_screen = Toplevel(main_window)
    loading_screen.title("Please wait")
    loading_label = ttk.Label(loading_screen, text=loading_text.get(), font=("Arial", 30))
    loading_label.pack()
    loading_screen.bind('<Alt-F4>', closing_loading_screen)
    loading_screen.protocol("WM_DELETE_WINDOW", closing_loading_screen)
    loading_screen.geometry('420x350')
    loading_screen.maxsize(420, 350)
    loading_screen.minsize(420, 350)

    # Show loading screen until we've gotten orders and current balance
    while True:
        try:
            main_window.update()
            loading_screen.lift()
            loading_screen.focus_set()
        except TclError:
            pass
        time.sleep(3)
        if open_orders['error'] is not None and not open_orders['error']:
            if current_balance['error'] is not None and not current_balance['error']:
                if available_pairs:
                    if ticker_information['error'] is not None:
                        for each_available_pair in available_pairs:
                            for each_balance in current_balance:
                                if each_balance != 'error':
                                    if each_available_pair.endswith(each_balance):
                                        show_pairs['buy'].append(each_available_pair)
                                    elif each_available_pair.startswith(each_balance):
                                        show_pairs['sell'].append(each_available_pair)
                        break
    try:
        loading_screen.destroy()
        the_menu = Menu(main_window)
        main_window.config(menu=the_menu)

        file_menu = Menu(the_menu, tearoff=False)
        the_menu.add_cascade(label='File', menu=file_menu)
        file_menu.add_command(label='Exit', command=closing_verify)

        settings_menu = Menu(the_menu, tearoff=False)
        the_menu.add_cascade(label='Settings', menu=settings_menu)
        # TODO
        settings_menu.add_command(label='View', command=view_current_settings)
        # TODO
        settings_menu.add_command(label='Edit', command=edit_settings)

        help_menu = Menu(the_menu, tearoff=False)
        the_menu.add_cascade(label='Help', menu=help_menu)
        help_menu.add_command(label='How-to', command=how_do_i)

        current_bots_text = ttk.Label(main_window, text="Current orders:")
        current_bots_text.grid(row=1, column=2, sticky=S)

        all_current_orders.configure(width=21)
        all_current_orders.bind('<Double-Button-1>', get_more_info_selected)
        all_current_orders.grid(row=2, column=2)

        add_new_button = Button(main_window, text="Add new\norder", command=create_new_order)
        add_new_button.grid(row=3, column=1)

        cancel_selected = Button(main_window, text="Cancel\norder", command=cancel_selected_order)
        cancel_selected.grid(row=3, column=3, sticky=W)

        main_window.mainloop()
    except TclError as the_error:
        if 'application has been destroyed' in str(the_error):
            # Loading screen was closed. Application will be killed soon.
            pass
        # Program was exited. Application will be killed soon.
        elif 'invalid command name' in str(the_error):
            pass
        else:
            print(f'TclError: {str(the_error)}')
else:
    sys.exit()
