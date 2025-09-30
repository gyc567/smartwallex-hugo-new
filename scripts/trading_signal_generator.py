#!/usr/bin/env python3
"""
Trading Signal Generator
Generates professional cryptocurrency trading signals based on market analysis
"""

import json
import random
import datetime
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class TradingSignalGenerator:
    """Generates realistic trading signals for major cryptocurrencies"""
    
    def __init__(self):
        self.symbols = ["BTC/USDT", "ETH/USDT", "BNB/USDT", "SOL/USDT", "BCH/USDT"]
        self.signals = ["BUY", "SELL", "HOLD"]
        self.timeframes = ["1h", "4h", "1d"]
        
        # Realistic price ranges (approximate current market prices)
        self.price_ranges = {
            "BTC/USDT": {"min": 40000, "max": 50000, "step": 100},
            "ETH/USDT": {"min": 2500, "max": 3200, "step": 10},
            "BNB/USDT": {"min": 400, "max": 600, "step": 1},
            "SOL/USDT": {"min": 120, "max": 180, "step": 0.5},
            "BCH/USDT": {"min": 300, "max": 450, "step": 1}
        }
        
    def generate_signals(self, count: int = 3) -> List[Dict[str, Any]]:
        """
        Generate trading signals
        
        Args:
            count: Number of signals to generate
            
        Returns:
            List of signal dictionaries
        """
        if count <= 0:
            return []
            
        signals = []
        selected_symbols = random.sample(self.symbols, min(count, len(self.symbols)))
        
        for symbol in selected_symbols:
            signal = self._generate_single_signal(symbol)
            signals.append(signal)
            
        return signals
    
    def _generate_single_signal(self, symbol: str) -> Dict[str, Any]:
        """Generate a single trading signal"""
        current_price = self._generate_current_price(symbol)
        signal_type = random.choice(self.signals)
        
        # Generate signal-specific parameters
        if signal_type == "BUY":
            entry_price = current_price
            stop_loss = entry_price * random.uniform(0.97, 0.99)  # 1-3% stop loss
            take_profit = entry_price * random.uniform(1.02, 1.05)  # 2-5% take profit
        elif signal_type == "SELL":
            entry_price = current_price
            stop_loss = entry_price * random.uniform(1.01, 1.03)  # 1-3% stop loss
            take_profit = entry_price * random.uniform(0.95, 0.98)  # 2-5% take profit
        else:  # HOLD
            entry_price = current_price
            stop_loss = entry_price * random.uniform(0.95, 0.97)  # Wider stops for hold
            take_profit = entry_price * random.uniform(1.03, 1.06)
        
        # Round prices appropriately
        price_range = self.price_ranges[symbol]
        decimals = len(str(price_range["step"]).split('.')[-1]) if '.' in str(price_range["step"]) else 0
        
        signal = {
            "symbol": symbol,
            "signal": signal_type,
            "entry_price": f"${entry_price:,.{decimals}f}",
            "stop_loss": f"${stop_loss:,.{decimals}f}",
            "take_profit": f"${take_profit:,.{decimals}f}",
            "confidence": f"{random.randint(60, 90)}%",
            "timestamp": datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
            "indicators": self._generate_indicators(signal_type),
            "risk_reward_ratio": self._calculate_risk_reward(entry_price, stop_loss, take_profit, signal_type),
            "timeframe": random.choice(self.timeframes),
            "market_condition": self._generate_market_condition()
        }
        
        return signal
    
    def _generate_current_price(self, symbol: str) -> float:
        """Generate current price for symbol"""
        price_range = self.price_ranges[symbol]
        
        # Generate price within range, weighted towards middle
        base_price = random.uniform(price_range["min"], price_range["max"])
        
        # Round to step size
        step = price_range["step"]
        return round(base_price / step) * step
    
    def _generate_indicators(self, signal_type: str) -> Dict[str, str]:
        """Generate technical indicators based on signal type"""
        indicators = {}
        
        # RSI based on signal
        if signal_type == "BUY":
            indicators["rsi"] = str(random.randint(25, 45))
        elif signal_type == "SELL":
            indicators["rsi"] = str(random.randint(55, 75))
        else:  # HOLD
            indicators["rsi"] = str(random.randint(40, 60))
        
        # MACD
        macd_signals = {
            "BUY": ["Bullish crossover", "Positive divergence", "Signal line crossover"],
            "SELL": ["Bearish crossover", "Negative divergence", "Signal line crossover"],
            "HOLD": ["Neutral", "Consolidating", "Sideways momentum"]
        }
        indicators["macd"] = random.choice(macd_signals[signal_type])
        
        # Volume
        volume_levels = ["Above average", "High", "Normal", "Low"]
        indicators["volume"] = random.choice(volume_levels)
        
        # Moving averages
        ma_signals = {
            "BUY": ["Price above MA50", "MA20 above MA50", "Golden cross"],
            "SELL": ["Price below MA50", "MA20 below MA50", "Death cross"],
            "HOLD": ["Price near MA50", "MA lines converging", "Mixed signals"]
        }
        indicators["moving_averages"] = random.choice(ma_signals[signal_type])
        
        return indicators
    
    def _calculate_risk_reward(self, entry: float, stop: float, take: float, signal_type: str) -> str:
        """Calculate risk/reward ratio"""
        if signal_type == "BUY":
            risk = abs(entry - stop)
            reward = abs(take - entry)
        elif signal_type == "SELL":
            risk = abs(stop - entry)
            reward = abs(entry - take)
        else:  # HOLD
            risk = abs(entry - stop)
            reward = abs(take - entry)
        
        if risk == 0:
            return "N/A"
            
        ratio = reward / risk
        return f"1:{ratio:.1f}"
    
    def _generate_market_condition(self) -> str:
        """Generate market condition"""
        conditions = [
            "Trending up", "Trending down", "Sideways", "Volatile",
            "Consolidating", "Breakout potential", "Support test", "Resistance test"
        ]
        return random.choice(conditions)
    
    def generate_market_summary(self) -> Dict[str, Any]:
        """Generate overall market summary"""
        return {
            "date": datetime.datetime.utcnow().strftime("%Y-%m-%d"),
            "time": datetime.datetime.utcnow().strftime("%H:%M:%S UTC"),
            "market_sentiment": random.choice(["Bullish", "Bearish", "Neutral"]),
            "volatility": random.choice(["Low", "Medium", "High"]),
            "dominant_trend": random.choice(["Up", "Down", "Sideways"]),
            "key_levels": {
                "btc_support": f"${random.randint(40000, 42000):,}",
                "btc_resistance": f"${random.randint(46000, 48000):,}",
                "eth_support": f"${random.randint(2500, 2700):,}",
                "eth_resistance": f"${random.randint(3000, 3200):,}"
            }
        }


def main():
    """CLI interface for signal generation"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate cryptocurrency trading signals")
    parser.add_argument("--count", type=int, default=3, help="Number of signals to generate")
    parser.add_argument("--output", type=str, help="Output file (default: stdout)")
    parser.add_argument("--format", choices=["json", "pretty"], default="json", help="Output format")
    parser.add_argument("--include-summary", action="store_true", help="Include market summary")
    
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO)
    
    generator = TradingSignalGenerator()
    
    try:
        signals = generator.generate_signals(args.count)
        
        output = {
            "signals": signals,
            "generated_at": datetime.datetime.utcnow().isoformat(),
            "total_signals": len(signals)
        }
        
        if args.include_summary:
            output["market_summary"] = generator.generate_market_summary()
        
        if args.format == "json":
            result = json.dumps(output, indent=2, ensure_ascii=False)
        else:
            result = format_pretty(output)
        
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(result)
            print(f"✅ Generated {len(signals)} signals to {args.output}")
        else:
            print(result)
            
    except Exception as e:
        logger.error(f"Error generating signals: {e}")
        return 1
    
    return 0


def format_pretty(data: Dict[str, Any]) -> str:
    """Format output in pretty text format"""
    lines = []
    
    if "market_summary" in data:
        summary = data["market_summary"]
        lines.append("📊 Market Summary")
        lines.append(f"Date: {summary['date']}")
        lines.append(f"Sentiment: {summary['market_sentiment']}")
        lines.append(f"Volatility: {summary['volatility']}")
        lines.append("")
    
    lines.append("🎯 Trading Signals")
    lines.append(f"Generated: {data['generated_at']}")
    lines.append("")
    
    for i, signal in enumerate(data["signals"], 1):
        lines.append(f"Signal #{i}")
        lines.append(f"  Symbol: {signal['symbol']}")
        lines.append(f"  Signal: {signal['signal']}")
        lines.append(f"  Entry: {signal['entry_price']}")
        lines.append(f"  Stop Loss: {signal['stop_loss']}")
        lines.append(f"  Take Profit: {signal['take_profit']}")
        lines.append(f"  Confidence: {signal['confidence']}")
        lines.append(f"  Risk/Reward: {signal['risk_reward_ratio']}")
        lines.append(f"  Timeframe: {signal['timeframe']}")
        lines.append("")
    
    return "\n".join(lines)


if __name__ == "__main__":
    exit(main())