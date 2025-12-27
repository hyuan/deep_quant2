"""Fractals indicator for identifying reversal points."""

import backtrader as bt


class Fractals(bt.Indicator):
    """
    Bill Williams Fractals indicator to identify potential reversal points.
    
    A fractal high is formed when a bar has the highest high with lower highs
    on both sides. A fractal low is formed when a bar has the lowest low with
    higher lows on both sides.
    
    Parameters:
        left_period: Number of bars to the left of peak/valley (default: 2)
        right_period: Number of bars to the right of peak/valley (default: 2)
        scale_factor: Factor to scale output values (default: 1.0)
    
    Lines:
        fractal_high: Value at fractal high (peak), NaN otherwise
        fractal_low: Value at fractal low (valley), NaN otherwise
    
    Example:
        # Fractals for price
        self.fractals_price = Fractals(
            self.datas[0].close,
            left_period=2,
            right_period=2
        )
        
        # Fractals for volume
        self.fractals_volume = Fractals(
            self.datas[0].volume,
            left_period=2,
            right_period=2,
            scale_factor=1.0
        )
        self.fractals_volume.plotinfo.subplot = True
    """
    
    lines = ('fractal_high', 'fractal_low')
    
    params = dict(
        left_period=2,
        right_period=2,
        scale_factor=1.0,
    )
    
    plotinfo = dict(subplot=False)
    plotlines = dict(
        fractal_high=dict(marker='^', markersize=8.0, color='red', fillstyle='full'),
        fractal_low=dict(marker='v', markersize=8.0, color='green', fillstyle='full'),
    )
    
    def __init__(self):
        total_period = self.p.left_period + self.p.right_period + 1
        self.addminperiod(total_period)
        
        super(Fractals, self).__init__()
    
    def next(self):
        left_p = self.p.left_period
        right_p = self.p.right_period
        total_p = left_p + right_p + 1
        
        # Ensure enough data points
        if len(self.data) < total_p:
            self.lines.fractal_high[0] = float('nan')
            self.lines.fractal_low[0] = float('nan')
            return
        
        # Get window of data points
        highs = [self.data[-i] for i in range(total_p)]
        lows = [self.data[-i] for i in range(total_p)]
        
        mid_idx = right_p
        max_high = max(highs)
        min_low = min(lows)
        
        # Fractal High (Peak) - middle bar must be unique maximum
        if highs[mid_idx] == max_high and highs.count(max_high) == 1:
            self.lines.fractal_high[0] = self._scale_data(self.data[0])
        else:
            self.lines.fractal_high[0] = float('nan')
        
        # Fractal Low (Valley) - middle bar must be unique minimum
        if lows[mid_idx] == min_low and lows.count(min_low) == 1:
            self.lines.fractal_low[0] = self._scale_data(self.data[0])
        else:
            self.lines.fractal_low[0] = float('nan')
    
    def _scale_data(self, data):
        """Apply scale factor to data value."""
        return data * self.params.scale_factor
