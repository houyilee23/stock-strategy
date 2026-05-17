"""Common imports & helpers shared by all template modules.

All template generator files start with:
    from ._common import *

This consolidates the boilerplate (pandas/numpy + the indicator functions)
into one place. If a new helper is needed across templates, add it here.
"""
import numpy as np
import pandas as pd

from src.strategy.indicators.trend import sma, ema
from src.strategy.indicators.momentum import rsi
from src.strategy.indicators.volatility import atr, bollinger
from src.strategy.indicators.volume import volume_ma
