"""Analysis and formatting utilities for backtest results."""

from typing import Dict, Any


def format_trade_analysis(analysis: Dict[str, Any]) -> str:
    """
    Format trade analysis results in a human-readable way.
    
    Args:
        analysis: Trade analysis dictionary from Backtrader TradeAnalyzer
        
    Returns:
        Formatted string with trade statistics
    """
    output = []
    
    # Overall statistics
    output.append("\n===== TRADE ANALYSIS =====")
    total = analysis.get('total', {})
    output.append(
        f"Total Trades: {total.get('total', 0)} "
        f"(Open: {total.get('open', 0)}, Closed: {total.get('closed', 0)})"
    )
    
    # Win/Loss stats
    won = analysis.get('won', {})
    lost = analysis.get('lost', {})
    total_closed = won.get('total', 0) + lost.get('total', 0)
    win_rate = (won.get('total', 0) / total_closed * 100) if total_closed > 0 else 0
    
    output.append("\n----- Win/Loss Statistics -----")
    output.append(f"Won Trades: {won.get('total', 0)} ({win_rate:.2f}%)")
    output.append(f"Lost Trades: {lost.get('total', 0)} ({100-win_rate:.2f}%)")
    
    # Winning streak information
    streak = analysis.get('streak', {})
    output.append("\n----- Win/Loss Streaks -----")
    output.append(f"Current Winning Streak: {streak.get('won', {}).get('current', 0)}")
    output.append(f"Longest Winning Streak: {streak.get('won', {}).get('longest', 0)}")
    output.append(f"Current Losing Streak: {streak.get('lost', {}).get('current', 0)}")
    output.append(f"Longest Losing Streak: {streak.get('lost', {}).get('longest', 0)}")
    
    # PnL information
    pnl = analysis.get('pnl', {})
    output.append("\n----- Profit/Loss Information -----")
    gross = pnl.get('gross', {})
    net = pnl.get('net', {})
    output.append(f"Gross Profit: ${gross.get('total', 0):.2f}")
    output.append(f"Average Profit per Trade: ${gross.get('average', 0):.2f}")
    output.append(f"Net Profit: ${net.get('total', 0):.2f}")
    output.append(f"Average Net Profit per Trade: ${net.get('average', 0):.2f}")
    
    # Won trades details
    output.append("\n----- Won Trades -----")
    won_pnl = won.get('pnl', {})
    output.append(f"Total PnL: ${won_pnl.get('total', 0):.2f}")
    output.append(f"Average PnL: ${won_pnl.get('average', 0):.2f}")
    output.append(f"Max PnL: ${won_pnl.get('max', 0):.2f}")
    
    # Lost trades details
    output.append("\n----- Lost Trades -----")
    lost_pnl = lost.get('pnl', {})
    output.append(f"Total PnL: ${lost_pnl.get('total', 0):.2f}")
    output.append(f"Average PnL: ${lost_pnl.get('average', 0):.2f}")
    output.append(f"Max Loss: ${abs(lost_pnl.get('max', 0)):.2f}")
    
    # Long/Short breakdown
    long = analysis.get('long', {})
    short = analysis.get('short', {})
    output.append("\n----- Long/Short Breakdown -----")
    output.append(
        f"Long Trades: {long.get('total', 0)} "
        f"(Won: {long.get('won', 0)}, Lost: {long.get('lost', 0)})"
    )
    output.append(
        f"Short Trades: {short.get('total', 0)} "
        f"(Won: {short.get('won', 0)}, Lost: {short.get('lost', 0)})"
    )
    
    # Trade duration stats
    length = analysis.get('len', {})
    output.append("\n----- Trade Duration -----")
    output.append(f"Average Trade Length: {length.get('average', 0):.1f} bars")
    output.append(f"Longest Trade: {length.get('max', 0)} bars")
    output.append(f"Shortest Trade: {length.get('min', 0)} bars")
    
    won_len = length.get('won', {})
    lost_len = length.get('lost', {})
    output.append(f"Average Winning Trade Length: {won_len.get('average', 0):.1f} bars")
    output.append(f"Average Losing Trade Length: {lost_len.get('average', 0):.1f} bars")
    
    return "\n".join(output)


def format_analyzer_results(analyzers: Dict[str, Any]) -> str:
    """
    Format all analyzer results.
    
    Args:
        analyzers: Dictionary of analyzer results
        
    Returns:
        Formatted string with all analysis
    """
    output = []
    
    output.append("\n" + "="*50)
    output.append("BACKTEST ANALYSIS RESULTS")
    output.append("="*50)
    
    # Sharpe Ratio
    if 'sharpe' in analyzers:
        sharpe = analyzers['sharpe'].get('sharperatio', 0)
        output.append(f"\nSharpe Ratio: {sharpe:.4f}" if sharpe else "\nSharpe Ratio: N/A")
    
    # Max Drawdown
    if 'drawdown' in analyzers:
        dd = analyzers['drawdown']
        output.append(f"Max Drawdown: {dd.get('max', {}).get('drawdown', 0):.2f}%")
        output.append(f"Drawdown Period: {dd.get('max', {}).get('len', 0)} bars")
    
    # SQN (System Quality Number)
    if 'sqn' in analyzers:
        sqn = analyzers['sqn'].get('sqn', 0)
        output.append(f"SQN: {sqn:.4f}" if sqn else "SQN: N/A")
    
    # Trade Analysis
    if 'trades' in analyzers:
        output.append(format_trade_analysis(analyzers['trades']))
    
    output.append("\n" + "="*50 + "\n")
    return "\n".join(output)
