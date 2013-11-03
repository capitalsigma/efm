import datetime
import math
import csv

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
        

class MarketAccount(object):
    def __init__(self, starting_bal, order_factory):
        self._order_factory = order_factory
        self.balance = Balance(starting_bal)
        self.orders = []
        self._orders_processed = []


    def _add_order(self, date, qty, is_buy):
        trans_funcs = [self._order_factory.sell, self._order_factory.buy]
        self.orders.append(trans_funcs[is_buy](date, qty))

    def place_buy(self, date, qty):
        self._add_order(date, qty, True)

    def place_sell(self, date, qty):
        self._add_order(date, qty, False)

    def settle(self):
        for order in self.orders:
            self._orders_processed.append(order)
            self.balance.add(*order.execute())
            

        
class OrderFactory(object):
    def __init__(self, csv_path):
        self._parser = Parser(csv_path)

    def buy(self, date, qty):
        return BuyOrder(date, qty, self._parser.data[date])

    def sell(self, date, qty):
        return SellOrder(date, qty, self._parser.data[date])
            

class Order(object):
    @abstractmethod
    def __init__(self, qty, price_data):
#        self.date = date
        self.qty = qty
        self.price_data = price_data

    
    def execute(self):
        return \
          self.sign * self.price_data['Adjusted Close'] * self.qty, \
          self.sign * self.qty

class BuyOrder(Order):
    def __init__(self, qty, price_data):
        super().__init__(qty, price_data)
        self._sign = -1
        
class SellOrder(Order):
    def __init__(self, qty, price_data):
        super().__init__(qty, price_data)
        self._sign = 1


class Parser(object):
    ONE_DAY = datetime.timedelta(days=1)
    def __init__(self, csv_path):
        self.data = {}
        with open(csv_path, 'r') as data_file:
            reader = csv.DictReader(data_file)
            for row in reader:
                self.data[datetime_from_str(row.pop("Date"))] = row


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
        self.wave_threshold = wave_threshold

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
            current_run = current_run + 1 if \
                self._sign_has_changed(date, avg_range) \
                else 0

            if current_run >= self.wave_threshold:
                wave = (wave + 1) % 5
                current_run = 0

            self._WAVE_BEHAVIORS[wave]()
                
    def _do_nothing(self):
        pass

    def _buy_all(self):
        #TODO: IMPLEMENT ME
        pass

    def _sell_all(self):
        #TOOD: IMPLEMENT ME
        pass
                      

    def _sign_has_changed(self, date, avg_range):
        return sign(self._parser.avg_change(date, avg_range)) != \
                sign(self._parser.avg_change(date - 1, avg_range))
    
def datetime_from_str(date_str):
    FORMAT = "%Y-%m-%d"
    return datetime.strptime(date_str, FORMAT)

def sign(num):
    return math.copysign(1, num)
