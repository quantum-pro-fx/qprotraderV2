import numpy as np

def apply_slippage(price, direction, avg_slippage):
    """Apply realistic slippage for scalping"""
    slippage = np.random.normal(avg_slippage, avg_slippage/2)
    if direction > 0:  # Buy order
        return price + slippage
    else:  # Sell order
        return price - slippage

def estimate_fill_probability(spread, volatility, order_size):
    """Estimate probability of order filling"""
    base_prob = np.exp(-spread * 10000)  # Convert to pips
    size_penalty = min(1, 1 / (order_size ** 0.5))
    return base_prob * size_penalty