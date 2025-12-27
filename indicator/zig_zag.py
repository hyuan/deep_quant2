"""ZigZag indicator for detecting trend reversals."""

import backtrader as bt


class ZigZag(bt.Indicator):
    """
    ZigZag indicator to detect uptrends and downtrends.
    
    Identifies significant price swings by filtering out minor fluctuations.
    Only reverses direction when price moves by the specified percentage.
    
    Parameters:
        retrace_perc: Minimum percentage change for reversal (default: 5)
        scale_factor: Factor to scale input data (default: 1.0)
    
    Example:
        # ZigZag for price
        self.zigzag_price = ZigZag(self.datas[0].close, retrace_perc=15)
        
        # ZigZag for volume
        self.zigzag_volume = ZigZag(self.datas[0].volume, retrace_perc=15)
        self.zigzag_volume.plotinfo.subplot = True
    """
    
    lines = ('zigzag', 'zigzag_up', 'zigzag_down')
    
    params = dict(
        retrace_perc=5,
        scale_factor=1.0,
    )
    
    plotinfo = dict(subplot=False)
    plotlines = dict(
        zigzag=dict(_name='ZigZag', color='magenta', linestyle='-', linewidth=1.5),
        zigzag_up=dict(marker='^', markersize=8.0, color='blue', fillstyle='full'),
        zigzag_down=dict(marker='v', markersize=8.0, color='brown', fillstyle='full'),
    )
    
    def __init__(self):
        self.last_pivot = None
        self.last_pivot_idx = None
        self.prev_last_pivot_idx = None
        self.trend = 0  # 1 for uptrend, -1 for downtrend
        
        super(ZigZag, self).__init__()
    
    def next(self):
        idx = len(self.data) - 1
        price = self.data[0] * self.params.scale_factor
        
        if self.last_pivot is None:
            self.last_pivot = price
            self.last_pivot_idx = idx
            self.lines.zigzag[0] = price
            return
        
        # Calculate percentage change from last pivot
        change_perc = (price - self.last_pivot) / self.last_pivot * 100
        
        if self.trend >= 0 and change_perc <= -self.params.retrace_perc:
            # Downtrend reversal
            self.trend = -1
            self.backward_fill(idx)
            self.last_pivot = price
            self.prev_last_pivot_idx = self.last_pivot_idx
            self.last_pivot_idx = idx
            self.lines.zigzag[0] = price
            self.lines.zigzag_up[0] = price
        elif self.trend <= 0 and change_perc >= self.params.retrace_perc:
            # Uptrend reversal
            self.trend = 1
            self.backward_fill(idx)
            self.prev_last_pivot_idx = self.last_pivot_idx
            self.last_pivot = price
            self.last_pivot_idx = idx
            self.lines.zigzag[0] = price
            self.lines.zigzag_down[0] = price
        else:
            # No trend change
            if self.trend == 1:
                if self.last_pivot < price:
                    self.last_pivot = price
                    self.last_pivot_idx = idx
            elif self.trend == -1:
                if self.last_pivot > price:
                    self.last_pivot = price
                    self.last_pivot_idx = idx
            
            self.lines.zigzag[0] = self.last_pivot
            self.lines.zigzag_up[0] = float('nan')
            self.lines.zigzag_down[0] = float('nan')
    
    def backward_fill(self, idx):
        """Fill backward from previous pivot to create continuous line."""
        if self.prev_last_pivot_idx is None or self.last_pivot_idx is None:
            return
        
        # Fill backward between pivots
        for i in range(self.prev_last_pivot_idx + 1, self.last_pivot_idx):
            offset = idx - i
            if offset < len(self.lines.zigzag):
                self.lines.zigzag[-offset] = self.last_pivot
