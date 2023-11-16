from __future__ import (
    absolute_import, 
    division, 
    print_function, 
    unicode_literals)

import datetime
import backtrader as bt

from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def hello_backtester():
    return "<p>It's a start</p>"

@app.route('/graph/')
def graph_gui():




    # Create a Strategy
    class TestStrategy(bt.Strategy):
        
        def log(self, txt, dt=None):
            # Logging function
            dt = dt or self.datas[0].datetime.date(0)
            print('%s, %s' % (dt.isoformat(), txt))

        
        def __init__(self):
            # Keep a reference to the 'close' line in the data[0] dataseries
            self.dataclose = self.datas[0].close

            # Keep track of pending orders
            self.order = None
        
        def notify_order(self, order):


            if order.status in [order.Submitted, order.Accepted]:
                # Looks to mean that the order is being processed so
                # do nothing 
                return
            
            # Check if an order has been completed
            # Attention: broker could reject the order if not
            # enough cash
            if order.status in [order.Completed]:
                if order.isbuy():
                    self.log('BUY EXECUTED, %2f' % order.executed.price)
                elif order.issell():
                    self.log('SELL EXECUTED, %.2f' % order.executed.price)

                self.bar_executed = len(self)

            elif order.status in [order.Cancelled, order.Margin, order.Rejected]:
                self.log('Order Cancelled/Margin/Rejected')

            # Write down: no pending order
            self.order = None

        
        def next(self):
            # Log the closing price of the series from the reference
            self.log('Close, %2f' % self.dataclose[0])

            # Check if an order is pending.  If yes, we cannot
            # send a second one.
            if self.order:
                return
            
            # Check if we are in the market
            if not self.position:

                # Not yet... we miiight buy if
                if self.dataclose[0] < self.dataclose[-1]:
                    # The current close is less than the previous

                    if self.dataclose[-1] < self.dataclose[-2]:
                        # previous close less than the previous close

                        # BUYYYYYY
                        self.log('BUY CREATE, %2f' % self.dataclose[0])

                        # Keep track of the created order to avoid a second
                        self.order = self.buy()

            else:

                # Already in the market ... we might sell
                if len(self) >= (self.bar_executed + 5):
                    # SELL SELLLLLLL (with all poss params)
                    self.log('SELL CREATE, %2f' % self.dataclose[0])

                    # Keep track of the created order to avoid a second
                    self.order = self.sell()



            if self.dataclose[0] < self.dataclose[-1]:
                # current close less than previous close

                if self.dataclose[-1] < self.dataclose[-2]:
                    # previous close less than the previous close

                    # BUY BUY BUY (with all poss. default parameters)
                    self.log('BUY CREATE, %.2f' % self.dataclose[0])
                    self.buy()



    if __name__ == '__main__':
        cerebro = bt.Cerebro()

        # Add a strategy
        cerebro.addstrategy(TestStrategy)

        # Set amount to start with
        cerebro.broker.setcash(100000.0)

        data_path = 'sample_data_feed.txt'

        # Create a data feed
        data = bt.feeds.YahooFinanceCSVData(
            dataname=data_path,
            fromdate=datetime.datetime(2000, 1, 1),
            todate=datetime.datetime(2000, 12, 31),
            reverse=False
        )

        # Add data feed to cerebro
        cerebro.adddata(data)

        #  Set cash start
        cerebro.broker.setcash(100000.0)

        print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())

        cerebro.run()

        print('Final Portfolio Value:  %.2f' % cerebro.broker.getvalue())


    return render_template('graph.html')