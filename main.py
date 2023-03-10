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
            a,b,c,d,e,f = np.polyfit([x[i] for i in range(self.i-self.domain, self.i,1)],[y[i] for i in range(self.i-self.domain,self.i,1)],5)
            x_extrap = np.add(np.arange(self.domain + self.testDomain), (np.ones((self.domain + self.testDomain,))* (self.i-self.domain)))
            y_extrap = a * np.power(x_extrap,5) + b*np.power(x_extrap,4) + c* np.power(x_extrap,3) + d*np.power(x_extrap,2)+ e* np.power(x_extrap,1) + f
            peaks = find_peaks(y_extrap)
            accuracy = 0
            for i in range(1, self.testDomain):
                print(len(y_extrap)-(self.testDomain-i))
                slope = y_extrap[len(y_extrap)-(self.testDomain-i)] - y_extrap[len(y_extrap)-(self.testDomain-i)-1]
                print(slope)
                if (slope < 0 and closeValues[self.i - (self.testDomain-i)] < y_extrap[len(y_extrap)-(self.testDomain-i)]) or (slope > 0 and closeValues[self.i - (self.testDomain-i)] > y_extrap[len(y_extrap)-(self.testDomain-i)]):
                    accuracy += 1
            #print(accuracy/self.testDomain)
            self.accuracyTotal += accuracy/self.testDomain         
            #plt.plot(x_extrap, y_extrap, label='Interpolated function')
            #plt.plot(x, y, 'o', label='Data points')
            #plt.legend()
            #plt.show()
        self.i += 1
    def onBarFinish(self,start,end):
        self.accuracyAverage = self.accuracyTotal/self.i
        print(f"End of HistoricalData")
        print(f"Start: {start}, End: {end}")
        print(f"The accuracy for this strategy is {self.accuracyAverage}")
bot = Bot()
count = 0
