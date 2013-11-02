class Balance(object):
    def __init__(self, starting_bal):
        self.bal = starting_bal
        assert(starting_bal)

    def add(self, cash_val):
        self.bal += starting_bal
        if self.bal < 0:
            raise InsufficentFunds            
        

class MarketAccount(object):
    def __init__(self, starting_bal, order_factory):
        self._order_factory = order_factory
        self._balance = Balance(starting_bal)
        self._orders = []
        self._orders_processed = []


    def _add_order(self, date, qty, is_buy):
        if is_buy:
            self.orders.append(self._order_factory.buy(date, qty))
        else:
            self.orders.append(self._order_factory.sell(date, qty))

    def place_buy(date, qty):
        self._add_order(date, qty, True)

    def place_sell(date, qty):
        self._add_order(date, qty, False)

    def settle(self):
        for order in self.orders:
            self._orders_processed.append(order)
            self._balance.add(order.execute())
            

        
class OrderFactory(object):
    def __init__(self, csv_path):
        self.data = {}
        with open(csv_path, 'r') as data_file:
            reader = csv.DictReader(data_file)
            for row in reader:
                # Date key removed as side effect
                # TODO: these should be datetime objects
                self.data[row.pop("Date")] = row

    def buy(date, qty):
        return BuyOrder(date, qty, self.data[date])

    def sell(date, qty):
        return SellOrder(date, qty, self.data[date])
            

class Order(object):
    def __init__(self, qty, price_data):
#        self.date = date
        self.qty = qty
        self.price_data = price_data

    
    def execute(self):
        return self.sign * price_data['Adjusted Close'] * self.qty

class BuyOrder(Order):
    def __init__(self, qty, price_data):
        super().__init__(qty, price_data)
        self._sign = -1
        
class SellOrder(Order):
    def __init__(self, qty, price_data):
        super().__init__(qty, price_data)
        self._sign = 1

        
