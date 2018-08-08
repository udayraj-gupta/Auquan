import numpy as np
import sys
sys.path.append(r'''C:\Users\tejaswini\Desktop\auquantoolbox''')
from backtester.features.ratio_feature import RatioMarketFeature
from backtester.instruments_manager import *
from backtester.instruments_lookback_data import *
from backtester.modelLearningManagers.feature_manager import FeatureManager
from unittest.mock import Mock, MagicMock
from tester.initialize import Initialize
import math
import pandas as pd
import pytest

@pytest.fixture
def mockInstrumentManager():
    return Mock(spec=InstrumentManager)
@pytest.fixture
def mockFeatureManager():
    return Mock(spec=FeatureManager)
@pytest.fixture
def mockInstrumentLookbackData():
	return Mock(spec=InstrumentsLookbackData)

def test_ratio(mockInstrumentManager, mockFeatureManager, mockInstrumentLookbackData):
    for i in range(1,4):
        dataSet = Initialize.getDataSet(i)
        mockInstrumentManager.getLookbackInstrumentFeatures.return_value = mockInstrumentLookbackData
        mockInstrumentLookbackData.getFeatureDf.return_value=dataSet["data"]
        resultInstrument = RatioMarketFeature.computeForInstrument(i, "", dataSet["featureParams"], "ma_m", mockInstrumentManager)
        mockInstrumentManager.getInstrument.return_value = dataSet["data"]
        resultMarket = RatioMarketFeature.computeForMarket(i, "", dataSet["featureParams"], "ma_m", {}, mockInstrumentManager)
        mockFeatureManager.getFeatureDf.return_value = dataSet["data"]
        resultInstrumentData = RatioMarketFeature.computeForInstrumentData(i, dataSet["featureParams"], "ma_m", mockFeatureManager )
        assert round(resultMarket,2) == round(dataSet['ratio'][-1],2)
        assert round(resultInstrument,2) == round(dataSet['ratio'][-1],2)
        assert round(resultInstrumentData.iloc[-1],2) == round(dataSet['ratio'][-1],2)
    for i in range(4,5):
        dataSet = Initialize.getDataSet(i)
        mockInstrumentManager.getLookbackInstrumentFeatures.return_value = mockInstrumentLookbackData
        mockInstrumentLookbackData.getFeatureDf.return_value=dataSet["data"]
        with pytest.raises(ValueError):
        	RatioMarketFeature.computeForInstrument(i, "", dataSet["featureParams"], "ma_m", mockInstrumentManager)
        mockInstrumentManager.getInstrument.return_value = dataSet["data"]
        with pytest.raises(ValueError):
        	RatioMarketFeature.computeForMarket(i, "", dataSet["featureParams"], "ma_m", {}, mockInstrumentManager)
        mockFeatureManager.getFeatureDf.return_value = dataSet["data"]
        with pytest.raises(ValueError):
        	RatioMarketFeature.computeForInstrumentData(i, dataSet["featureParams"], "ma_m", mockFeatureManager )