import datetime
import math
import csv
import abc

# Testing
import unittest


class InsufficientFundsError(Exception):
    pass

class InsufficentSharesError(Exception):
    pass

class Balance(object):
    def __init__(self, starting_bal):
        assert(starting_bal)
        self.balance = starting_bal
        self.qty_owned = 0

    def add(self, cash_val, qty):
        self.balance += cash_val
        self.qty_owned += qty
        if self.balance < 0:
            raise InsufficentFundsError
        if self.qty_owned < 0:
            raise InsufficientSharesError

    def __repr__(self):
        return "balance: {}, qty_owned: {}".format(self.balance, self.qty_owned)
        

class MarketAccount(object):
    def __init__(self, starting_bal, order_factory):
        self._order_factory = order_factory
        self.balance = Balance(starting_bal)
        self.orders = []
        self._orders_processed = []

    def __repr__(self):
        s = \
          '''Account:
        Balance:
        {}
        Pending orders:
        {}
        Resolved orders:
        {}'''.format(self.balance, self.orders, self._orders_processed)
        return s

    def _add_order(self, date, qty, is_buy):
        TRANS_FUNCS = [self._order_factory.sell, self._order_factory.buy]
        self.orders.append(TRANS_FUNCS[is_buy](date, qty))
        # I intended this to come at the end but it fits more naturally here
        self.settle()

    def place_buy(self, date, qty):
        self._add_order(date, qty, True)

    def place_sell(self, date, qty):
        self._add_order(date, qty, False)

    def settle(self):
        for order in self.orders:
            self._orders_processed.append(order)
            self.balance.add(*order.execute())

    def buy_max(self, date):
        # A little ugly, oops
        price = self._order_factory.buy(date, 1)['Adjusted Close']
        qty_to_buy = self.balance.balance/price
        self.place_buy(date, qty_to_buy)

    def sell_max(self, date):
        qty_to_buy = self.balance.qty_owned
        self.place_sell(date, qty_to_buy)
        
            

        
class OrderFactory(object):
    def __init__(self, csv_path):
        self._parser = Parser(csv_path)

    def buy(self, date, qty):
        return BuyOrder(date, qty, self._parser.data[date])

    def sell(self, date, qty):
        return SellOrder(date, qty, self._parser.data[date])
            

class Order(object):
    @abc.abstractmethod
    def __init__(self, qty, price_data):
#        self.date = date
        self.qty = qty
        self.price_data = price_data
        self._repr_name = ""
        self._sign = 0

    def __repr__(self):
        s = "{}Order for {}: {}".format(self._repr_name,
                                        self.qty, self.price_data)
        return s

            
    def execute(self):
        return \
          self._sign * self.price_data['Adjusted Close'] * self.qty, \
          self._sign * self.qty


class BuyOrder(Order):
    def __init__(self, qty, price_data):
        super().__init__(qty, price_data)
        self._sign = -1
        self._repr_name = "Buy"
        
class SellOrder(Order):
    def __init__(self, qty, price_data):
        super().__init__(qty, price_data)
        self._sign = 1
        self._repr_name = "Sell"


class Parser(object):
    ONE_DAY = datetime.timedelta(days=1)
    
    def __init__(self, csv_path):
        self._csv_path = csv_path
        self.data = {}
        # we need universal newline mode here b/c throwing ex. 
        with open(csv_path, 'rU') as data_file:
            reader = csv.DictReader(data_file)
            for row in reader:
                self.data[datetime_from_str(row.pop("Date"))] = row

    def __repr__(self):
        s = "Parser for {}".format(self._csv_path)
        return s

    # TODO: I'm inefficient! Linear on the size of the sliding window rather
    # than constant, like it could be. I'm going to leave it like this for now
    # for readability.
    def avg_change(self, start_date, num_days):
        dates = [start_date - self.ONE_DAY * i for i in range(1, num_days + 2)]
        prices = [self.data[date] for date in dates]

        return sum(prices)/num_days
                  
                  

class Model(object):
    def __init__(self, csv_path, starting_bal, wave_threshold):
        self._WAVE_BEHAVIORS = [
            self._buy_all,
            self._do_nothing,
            self._do_nothing,
            self._do_nothing,
            self._sell_all,
            ]

        
        self._parser = Parser(csv_path)
        self._account = MarketAccount(starting_bal, OrderFactory(csv_path))
        self._today = None
        self.wave_threshold = wave_threshold


    def __repr__(self):
        DATE_FORMAT = "%Y-%m-%d"
        date_str = self._today.strptime(DATE_FORMAT) if self._today else None
        s = \
          '''Model:
        {}
        {}
        on {}'''.format(self._parser, self._account, date_str)
        
    def _date_generator(self, start_date, end_date):
        ONE_DAY = datetime.timedelta(days=1)
        date = start_date
        while date < end_date:
            yield date
            date += ONE_DAY
        
        
    def execute(self, start_date, end_date, avg_range):
        assert(isinstance(start_date, datetime.datetime))
        assert(isinstance(end_date, datetime.datetime))

        # model state
        current_run = 0
        wave = 0
        
        # min_sell_threshold = 0
        
        for date in self._date_generator(start_date, end_date):
            self._today = date
            current_run = current_run + 1 if \
                self._sign_has_changed(date, avg_range) \
                else 0

            if current_run >= self.wave_threshold:
                wave = (wave + 1) % 5
                current_run = 0

            self._WAVE_BEHAVIORS[wave]()

            #debugging
            print(self)

        # TODO: let's return some values in a dict so we can unittest
        print("Results:")
        print(self)
                
    def _do_nothing(self):
        pass

    def _buy_all(self):
        self._account.buy_max(self._today)
        pass

    def _sell_all(self):
        self._account.sell_max(self._today)
        pass
                      

    def _sign_has_changed(self, date, avg_range):
        return sign(self._parser.avg_change(date, avg_range)) != \
                sign(self._parser.avg_change(date - 1, avg_range))
        
    
def datetime_from_str(date_str):
    FORMAT = "%Y-%m-%d"
    return datetime.datetime.strptime(date_str, FORMAT)

def sign(num):
    return math.copysign(1, num)


def test_harness():
    m = Model("../day1/INDEX_GSPC.csv", 10000000, 3)
    start_date = datetime.datetime(1970, 04, 29)
    end_date = datetime.datetime(2013, 10, 14)
    m.execute(start_date, end_date, 7)
