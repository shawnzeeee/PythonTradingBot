import ibapi
from ibapi.client import EClient
from ibapi.wrapper import EWrapper

from ibapi.contract import Contract
from ibapi.order import *
import threading
import time

import numpy as np
import scipy
from scipy.interpolate import interp1d
from scipy.signal import find_peaks
import matplotlib.pyplot as plt

from Orange.data import Domain, ContinuousVariable,DiscreteVariable, StringVariable

class IBApi(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self, self)
    
    def historicalData(self, reqId, bar):
        bot.onBarUpdate(reqId, bar)
        #print(f"Historical Data: {bar}")
        #return bar

    def historicalDataEnd(self, reqId, start, end):
        bot.onBarFinish(start,end)


class Bot:
    ib = None 
    bars = []
    i = 0
    domain = 30
    testDomain = 4
    testExtrapl = []
    accuracyTotal = 0
    accuracyAverage = 0
    features = ['a','b','c','e','f']
    base = 20;
    tableDomain = Domain([ContinuosVariable(f) for f in features],
    DiscreteVariable('target', values=[str(i*base) for i in range(1,5)]))
    data = Orange.data.Table(tableDomain)
    def __init__(self):
        self.ib = IBApi()
        self.ib.connect("127.0.0.1", 7497, 1)
        ib_thread = threading.Thread(target=self.runLoop, daemon=False)
        ib_thread.start()
        time.sleep(1)
        myContract = Contract()
        myContract.symbol = "AAPL"
        myContract.secType = "STK"  
        myContract.exchange = "SMART"
        myContract.currency = "USD"
        self.ib.reqHistoricalData(0, myContract, "20230123 15:59:00 US/Eastern", "1 D", "1 min", "TRADES", 0,1,0,[])
    def runLoop(self):
        self.ib.run()
        return
    def onBarUpdate(self, reqId, bar):
        self.bars.append(bar)
        if len(self.bars) > self.domain:
            x = np.arange(len(self.bars))
            closeValues = [bar.close for bar in self.bars]
            y = np.array(closeValues)
            a,b,c,d,e,f = np.polyfit([x[i] for i in range(self.i-self.domain-self.testDomain, self.i-self.testDomain,1)],[y[i] for i in range(self.i-self.domain-self.testDomain,self.i-self.testDomain,1)],5)
            #x_extrap = np.add(np.arange(self.domain + self.testDomain), (np.ones((self.domain + self.testDomain,))* (self.i-self.domain)))
            x_extrap = np.add(np.arange(self.testDomain),(np.ones(self.testDomain) * (self.i - self.testDomain)))
            y_extrap = a * np.power(x_extrap,5) + b*np.power(x_extrap,4) + c* np.power(x_extrap,3) + d*np.power(x_extrap,2)+ e* np.power(x_extrap,1) + f
            peaks = find_peaks(y_extrap)
            accuracy = 0
            for i in range(1, self.testDomain):
                slope = y_extrap[i] - y_extrap[i-1]
                if (slope < 0 and closeValues[self.i - (self.testDomain-i)] < y_extrap[i]) or (slope > 0 and closeValues[self.i - (self.testDomain-i)] > y_extrap[i]):
                    accuracy += 1
            #print(accuracy/self.testDomain)
            accuracy = accuracy/self.testDomain
            inputAccuracy = self.base * round(accuracy/self.base)
            self.data.append([a,b,c,d,e,inputAccuracy])         
            #plt.plot(x_extrap, y_extrap, label='Interpolated function')
            #plt.plot(x, y, 'o', label='Data points')
            #plt.legend()
            #plt.show()
        self.i += 1
    def onBarFinish(self,start,end):
        self.accuracyAverage = self.accuracyTotal/self.i
        model = Orange.classification.NeuralNetworkLearner(
        hidden_layers=[5],  # one hidden layer with 5 neurons
        activation_function=Orange.classification.neural.Activation.Sigmoid,
        weight_decay=0.1,  # regularization parameter
        max_iter=1000,  # maximum number of iterations
        )
        train_data, test_data = Orange.evaluation.testing.sample(data, n=0.8)
        classifier = model(train_data)
        result = Orange.evaluation.testing.TestOnTestData(train_data, test_data, [classifier])

        print(f"End of HistoricalData")
        print(f"Start: {start}, End: {end}")
        print(f"The training results: {result}")
bot = Bot()
count = 0
