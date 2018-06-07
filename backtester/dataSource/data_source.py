import pandas as pd
import os, csv
from datetime import datetime
from backtester.dataSource.data_source_utils import groupAndSortByTimeUpdates

class DataSource(object):
    def __init__(self, cachedFolderName, dataSetId, instrumentIds, startDateStr, endDateStr):
        self._cachedFolderName = cachedFolderName
        self._dataSetId = dataSetId
        self.ensureDirectoryExists(self._cachedFolderName, self._dataSetId)
        if instrumentIds is not None and len(instrumentIds) > 0:
            self._instrumentIds = instrumentIds
        else:
            self._instrumentIds = self.getAllInstrumentIds()

        if startDateStr and endDateStr:
            # # TODO: write method to also parse date string in different formats
            self._startDate = datetime.strptime(startDateStr, "%Y/%m/%d")
            self._endDate = datetime.strptime(endDateStr, "%Y/%m/%d")

        # Class variables: To be set by child class
        self._allTimes = None
        self._groupedInstrumentUpdates = None
        self._instrumentDataDict = None


    # def emitInstrumentUpdates(self):
        # raise NotImplementedError

    # returns a list of feature keys which are already present in the data.
    def getBookDataFeatures(self):
        raise NotImplementedError

    def getInstrumentUpdateFromRow(self, instrumentId, row):
        raise NotImplementedError

    def downloadAndAdjustData(self, instrumentId, fileName):
        raise NotImplementedError

    # returns a list of all instrument identifiers
    def getAllInstrumentIds(self):
        logError("No instrument provided")
        raise NotImplementedError

    # returns a list of instrument identifiers
    def getInstrumentIds(self):
        return self._instrumentIds

    # emits list of instrument updates at the same time.
    # The caller needs to ensure all these updates are happening at the same time
    # emits [t1, [i1, i2, i3]], where i1, i2, i3 are updates happening at time t1
    def emitInstrumentUpdates(self):
        for timeOfUpdate, instrumentUpdates in self._groupedInstrumentUpdates:
            yield([timeOfUpdate, instrumentUpdates])

    # emits the dict of all instrument updates where
    # keys are instrumentId and values are pandas dataframe
    def emitAllInstrumentUpdates(self):
        ## stock wise data
        # for instrumentId in self.getInstrumentIds():
            # yield self._instrumentDataDict[instrumentId]
        return self._instrumentDataDict

    def getGroupedInstrumentUpdates(self):
        allInstrumentUpdates = []
        for instrumentId in self._instrumentIds:
            print('Processing data for stock: %s' % (instrumentId))
            fileName = self.getFileName(instrumentId)
            if not self.downloadAndAdjustData(instrumentId, fileName):
                continue
            with open(fileName) as f:
                records = csv.DictReader(f)
                for row in records:
                    try:
                        inst = self.getInstrumentUpdateFromRow(instrumentId, row)
                        allInstrumentUpdates.append(inst)
                    except:
                        continue
        timeUpdates, groupedInstrumentUpdates = groupAndSortByTimeUpdates(allInstrumentUpdates)
        return timeUpdates, groupedInstrumentUpdates

    def getAllInstrumentUpdates(self, chunks=None):
        allInstrumentUpdates = {instrumentId : None for instrumentId in self._instrumentIds}
        timeUpdates = []
        for instrumentId in self._instrumentIds:
            print('Processing data for stock: %s' % (instrumentId))
            fileName = self.getFileName(instrumentId)
            if not self.downloadAndAdjustData(instrumentId, fileName):
                continue
            allInstrumentUpdates[instrumentId] = pd.read_csv(fileName, index_col=0, parse_dates=True, dtype=float)
            timeUpdates = allInstrumentUpdates[instrumentId].index.union(timeUpdates)
            # NOTE: Assuming data is sorted by timeUpdates
            # allInstrumentUpdates[instrumentId] = allInstrumentUpdates[instrumentId].loc[allInstrumentUpdates[instrumentId].index.sort_values()]
        timeUpdates = timeUpdates if type(timeUpdates) is list else list(timeUpdates.values)
        return timeUpdates, allInstrumentUpdates

    # set same timestamps in all instrument data and then pad
    def padInstrumentUpdates(self):
        timeUpdates = pd.Series(self._allTimes)
        for instrumentId in self._instrumentIds:
            if not timeUpdates.isin(self._instrumentDataDict[instrumentId].index).all():
                df = pd.DataFrame(index=self._allTimes, columns=self._instrumentDataDict[instrumentId].columns)
                df.at[self._instrumentDataDict[instrumentId].index] = self._instrumentDataDict[instrumentId].copy()
                del self._instrumentDataDict[instrumentId]
                self._instrumentDataDict[instrumentId] = df
                self._instrumentDataDict[instrumentId].fillna(method='ffill', inplace=True)
                self._instrumentDataDict[instrumentId].fillna(0.0, inplace=True)

    # accretes all instrument updates using emitInstrumentUpdates method
    def processAllInstrumentUpdates(self, pad=True):
        self._instrumentDataDict = {instrumentId : pd.DataFrame(index=self._allTimes) for instrumentId in self._instrumentIds}
        for timeOfUpdate, instrumentUpdates in self.emitInstrumentUpdates():
            for instrumentUpdate in instrumentUpdates:
                instrumentId = instrumentUpdate.getInstrumentId()
                for col in instrumentUpdate.getBookData():
                    self._instrumentDataDict[instrumentId].at[timeOfUpdate, col] = instrumentUpdate.getBookData()[col]
        for instrumentId in self._instrumentDataDict:
            if pad:
                self._instrumentDataDict[instrumentId].fillna(method='ffill', inplace=True)
                self._instrumentDataDict[instrumentId].fillna(0.0, inplace=True)
            else:
                self._instrumentDataDict[instrumentId].dropna(inplace=True)

    # selects only those instrument updates which lie within dateRange
    def filterUpdatesByDates(self, dateRange=None):
        dateRange = dateRange if dateRange else (self._startDate.strftime("%Y%m%d"), self._endDateStr.strftime("%Y%m%d"))
        for instrumentId in self._instrumentIds:
            if type(dateRange) is list and self._instrumentDataDict[instrumentId] is not None:
                frames = []
                for dr in dateRange:
                    frames.append(self._instrumentDataDict[instrumentId][dr[0]:dr[1]])
                self._instrumentDataDict[instrumentId] = pd.concat(frames)
            elif self._instrumentDataDict[instrumentId] is not None:
                self._instrumentDataDict[instrumentId] = self._instrumentDataDict[instrumentId][dateRange[0]:dateRange[1]]

    def setStartDate(self, startDateStr):
        self._startDate = datetime.strptime(startDateStr, "%Y/%m/%d")

    def setEndDate(self, endDateStr):
        self._endDate = datetime.strptime(endDateStr, "%Y/%m/%d")

    def setDateRange(self, dateRange):
        self._dateRange = dateRange

    '''
    Helper Functions
    '''

    def ensureDirectoryExists(self, cachedFolderName, dataSetId):
        if not os.path.exists(cachedFolderName):
            os.mkdir(cachedFolderName, 0o755)
        if not os.path.exists(cachedFolderName + '/' + dataSetId):
            os.mkdir(cachedFolderName + '/' + dataSetId)

    '''
    Called at end of trading to cleanup stuff
    '''
    def cleanup(self):
        return
