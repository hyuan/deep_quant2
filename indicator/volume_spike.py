"""Volume spike detection indicator using MACD on volume."""

from typing import Any

import backtrader as bt


class VolumeSpike(bt.Indicator):
    """
    Detects significant volume spikes and fires buy signals.
    
    Implementation:
    1. Computes MACD on volume data
    2. Checks if MACD histogram's mean exceeds threshold
    3. Fires signal when histogram crosses from positive to negative
       and mean is above threshold
    
    Parameters:
        macd_fast: Fast EMA period for MACD on volume (default: 12)
        macd_slow: Slow EMA period for MACD on volume (default: 26)
        macd_signal: Signal EMA period for MACD on volume (default: 9)
        macd_hist_mean_period: Period for histogram mean calculation (default: 9)
        macd_hist_mean_threshold: Threshold for mean histogram (default: 4000000.0)
    """
    
    lines = ('signal', 'hist', 'hist_mean')
    
    params = (
        ('macd_fast', 12),
        ('macd_slow', 26),
        ('macd_signal', 9),
        ('macd_hist_mean_period', 9),
        ('macd_hist_mean_threshold', 4000000.0),
    )
    
    plotinfo = dict(subplot=True)
    plotlines = dict(
        signal=dict(marker='^', markersize=8, color='green', ls=''),
        hist_mean=dict(color='blue'),
        hist=dict(_method='bar', color='gray', alpha=0.5)
    )
    
    def __init__(self, *args: Any, **kwargs: Any):
        # Compute MACD from volume
        vol = self.data.volume
        ema_fast = bt.ind.EMA(vol, period=self.p.macd_fast)
        ema_slow = bt.ind.EMA(vol, period=self.p.macd_slow)
        macd_line = ema_fast - ema_slow
        signal_line = bt.ind.EMA(macd_line, period=self.p.macd_signal)
        hist = macd_line - signal_line
        
        # Assign lines
        self.l.hist = hist
        
        # Compute histogram mean
        self.l.hist_mean = bt.ind.SMA(hist, period=self.p.macd_hist_mean_period)
        
        # Ensure enough data
        self.addminperiod(max(self.p.macd_slow, self.p.macd_hist_mean_period))
    
    def next(self):
        hist_now = self.l.hist[0]
        hist_prev = self.l.hist[-1]
        mean_now = self.l.hist_mean[0]
        
        # Check conditions:
        # 1) MACD histogram crosses from positive to negative
        macd_bearish_cross = (hist_prev > 0) and (hist_now <= 0)
        
        # 2) Histogram mean above threshold
        mean_above_threshold = (mean_now > self.p.macd_hist_mean_threshold)
        
        # Generate signal if both conditions met
        if macd_bearish_cross and mean_above_threshold:
            self.l.signal[0] = 1
        else:
            self.l.signal[0] = float('nan')
