import numpy as np
import pandas as pd

def calculate_metrics(trades):
    """Calculate performance metrics for scalping"""
    if not trades:
        return {}
        
    df = pd.DataFrame([t for t in trades if t['status'] == 'closed'])
    df['pnl'] = df['direction'] * (df['exit_price'] - df['entry_price'])
    df['returns'] = df['pnl'] / df['entry_price']
    
    wins = df[df['pnl'] > 0]
    losses = df[df['pnl'] <= 0]
    
    metrics = {
        'total_trades': len(df),
        'win_rate': len(wins) / len(df) if len(df) > 0 else 0,
        'avg_win': wins['pnl'].mean() if not wins.empty else 0,
        'avg_loss': losses['pnl'].mean() if not losses.empty else 0,
        'profit_factor': abs(wins['pnl'].sum() / losses['pnl'].sum()) if not losses.empty else np.inf,
        'sharpe_ratio': (df['returns'].mean() / df['returns'].std()) * np.sqrt(252*24*60) if len(df) > 1 else 0,
        'max_drawdown': calculate_drawdown(df['pnl'].cumsum())
    }
    
    return metrics
    
def calculate_drawdown(cum_pnl):
    """Calculate maximum drawdown"""
    peak = cum_pnl.max()
    trough = cum_pnl.min()
    return (trough - peak) / peak if peak != 0 else 0