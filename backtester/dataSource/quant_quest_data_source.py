from backtester.dataSource.data_source import DataSource
from backtester.instrumentUpdates import *
import os
from datetime import datetime
import csv
from backtester.logger import *
try:
    from urllib2 import urlopen
except ImportError:
    from urllib.request import urlopen


def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False


class QuantQuestDataSource(DataSource):
    def __init__(self, cachedFolderName, dataSetId, instrumentIds, startDateStr=None, endDateStr=None, liveUpdates=True, pad=True):
        super(QuantQuestDataSource, self).__init__(cachedFolderName, dataSetId, instrumentIds, startDateStr, endDateStr)
        self.ensureAllInstrumentsFile(dataSetId)
        self.__bookDataFeatureKeys = None
        if liveUpdates:
            self._allTimes, self._groupedInstrumentUpdates = self.getGroupedInstrumentUpdates()
        else:
            self._allTimes, self._instrumentDataDict = self.getAllInstrumentUpdates()
            if pad:
                self.padInstrumentUpdates()
            # self._allTimes, self._groupedInstrumentUpdates = self.getGroupedInstrumentUpdates()
            # self.processAllInstrumentUpdates(pad=pad)
            # del self._groupedInstrumentUpdates
            # self.filterUpdatesByDates()

    def getFileName(self, instrumentId):
        return self._cachedFolderName + self._dataSetId + '/' + instrumentId + '.csv'

    def ensureAllInstrumentsFile(self, dataSetId):
        stockListFileName = self._cachedFolderName + self._dataSetId + '/' + 'stock_list.txt'
        if os.path.isfile(stockListFileName):
            return True
        url = 'https://raw.githubusercontent.com/Auquan/auquan-historical-data/master/qq2Data/%s/stock_list.txt' % (
            dataSetId)
        print(url)
        response = urlopen(url)
        status = response.getcode()
        if status == 200:
            print('Downloading list of stocks to file: %s' % (stockListFileName))
            with open(stockListFileName, 'w') as f:
                f.write(response.read().decode('utf8'))
            return True
        else:
            logError('File not found. Please check internet')
            return False

    def getAllInstrumentIds(self):
        stockListFileName = self._cachedFolderName + self._dataSetId + '/' + 'stock_list.txt'
        if not os.path.isfile(stockListFileName):
            logError('Stock list file not present. Please try running again.')
            return []

        with open(stockListFileName) as f:
            content = f.readlines()
        # you may also want to remove whitespace characters like `\n` at the end of each line
        content = [x.strip() for x in content]
        return content

    def downloadFile(self, instrumentId, downloadLocation):
        url = 'https://raw.githubusercontent.com/Auquan/auquan-historical-data/master/qq2Data/%s/%s.csv' % (
            self._dataSetId, instrumentId)
        response = urlopen(url)
        status = response.getcode()
        if status == 200:
            print('Downloading %s data to file: %s' % (instrumentId, downloadLocation))
            with open(downloadLocation, 'w') as f:
                f.write(response.read().decode('utf8'))
            return True
        else:
            logError('File not found. Please check settings!')
            return False

    def downloadAndAdjustData(self, instrumentId, fileName):
        if not os.path.isfile(fileName):
            if not self.downloadFile(instrumentId, fileName):
                logError('Skipping %s:' % (instrumentId))
                return False
        return True

    def getInstrumentUpdateFromRow(self, instrumentId, row):
        bookData = row
        for key in bookData:
            if is_number(bookData[key]):
                bookData[key] = float(bookData[key])
        timeKey = ''
        timeOfUpdate = datetime.strptime(row[timeKey], '%Y-%m-%d %H:%M:%S')
        bookData.pop(timeKey, None)
        inst = StockInstrumentUpdate(stockInstrumentId=instrumentId,
                                     tradeSymbol=instrumentId,
                                     timeOfUpdate=timeOfUpdate,
                                     bookData=bookData)
        if self.__bookDataFeatureKeys is None:
            self.__bookDataFeatureKeys = bookData.keys()  # just setting to the first one we encounter
        return inst

    def getBookDataFeatures(self):
        return self.__bookDataFeatureKeys
