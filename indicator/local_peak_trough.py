"""Local peak and trough detection indicator."""

import backtrader as bt


class LocalPeakTrough(bt.Indicator):
    """
    Detects local peaks and troughs in price data.
    
    Uses SMA smoothing and consecutive bar confirmation to identify
    local maximum and minimum points.
    
    Parameters:
        min_confirm: Number of consecutive rising/falling bars required (default: 3)
        sma_period: Period for smoothing SMA (default: 5)
    
    Lines:
        peak: Shows value at confirmed peak, NaN otherwise
        trough: Shows value at confirmed trough, NaN otherwise
    """
    
    lines = ('peak', 'trough')
    
    params = (
        ('min_confirm', 3),
        ('sma_period', 5),
    )
    
    plotlines = dict(
        peak=dict(marker='^', markersize=8, color='green', ls=''),
        trough=dict(marker='v', markersize=8, color='red', ls=''),
    )
    
    def __init__(self):
        # Apply smoothing
        if self.p.sma_period > 1:
            self.sma = bt.indicators.SimpleMovingAverage(
                self.data, period=self.p.sma_period
            )
        else:
            self.sma = self.data
        
        # Ensure enough data for analysis
        self.addminperiod(self.p.min_confirm + self.p.sma_period)
        
        super(LocalPeakTrough, self).__init__()
    
    def next(self):
        """
        Detect peaks and troughs:
        1. Check recent min_confirm bars for highest/lowest values
        2. Confirm peak if previous bar is highest and preceded by consecutive rises
        3. Confirm trough if previous bar is lowest and preceded by consecutive falls
        """
        # Default: no peak or trough
        self.l.peak[0] = float('nan')
        self.l.trough[0] = float('nan')
        
        # Get recent SMA values
        recent_ma_values = [self.sma[-i] for i in range(self.p.min_confirm + 1)]
        previous_value = self.sma[-1]
        
        max_val = max(recent_ma_values)
        min_val = min(recent_ma_values)
        
        # Check for local maximum (peak)
        if abs(previous_value - max_val) < 1e-12:
            # Verify consecutive upward movement
            is_consecutive_up = True
            for i in range(1, self.p.min_confirm + 1):
                if not (self.sma[-i] > self.sma[-(i + 1)]):
                    is_consecutive_up = False
                    break
            
            if is_consecutive_up:
                self.l.peak[-1] = previous_value
        
        # Check for local minimum (trough)
        if abs(previous_value - min_val) < 1e-12:
            # Verify consecutive downward movement
            is_consecutive_down = True
            for i in range(1, self.p.min_confirm + 1):
                if not (self.sma[-i] < self.sma[-(i + 1)]):
                    is_consecutive_down = False
                    break
            
            if is_consecutive_down:
                self.l.trough[-1] = previous_value
