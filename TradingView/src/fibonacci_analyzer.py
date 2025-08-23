"""
斐波那契分析模块
计算回撤位、扩展位和时间周期分析
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import logging


@dataclass
class FibonacciLevels:
    """斐波那契水平"""
    swing_high: float
    swing_low: float
    retracement: Dict[float, float]
    extension: Dict[float, float]
    projection: Dict[float, float]


@dataclass
class SwingPoint:
    """波段点"""
    price: float
    timestamp: str
    type: str  # 'high' or 'low'
    strength: float  # 强度评分


class FibonacciAnalyzer:
    """斐波那契分析器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # 斐波那契比率
        self.retracement_levels = [0.236, 0.382, 0.5, 0.618, 0.786]
        self.extension_levels = [1.272, 1.414, 1.618, 2.618, 4.236]
        self.projection_levels = [0.618, 1.0, 1.272, 1.618]
    
    def analyze(self, df: pd.DataFrame) -> Dict:
        """
        执行斐波那契分析
        
        Args:
            df: OHLCV数据
            
        Returns:
            斐波那契分析结果
        """
        try:
            # 识别波段高低点
            swing_points = self._find_swing_points(df)
            
            # 获取最近的主要波段
            major_swing = self._get_major_swing(swing_points, df)
            
            if not major_swing:
                return {'error': '无法识别有效的波段'}
            
            # 计算斐波那契水平
            fib_levels = self._calculate_fibonacci_levels(
                major_swing['high'], 
                major_swing['low']
            )
            
            # 分析当前价格位置
            current_price = df['close'].iloc[-1]
            price_analysis = self._analyze_price_position(current_price, fib_levels)
            
            # 识别关键支撑阻力位
            key_levels = self._identify_key_levels(fib_levels, df)
            
            # 时间周期分析
            time_analysis = self._analyze_time_cycles(swing_points, df)
            
            return {
                'fibonacci_levels': fib_levels,
                'current_price': current_price,
                'price_analysis': price_analysis,
                'key_levels': key_levels,
                'time_analysis': time_analysis,
                'swing_points': swing_points[-10:],  # 最近10个波段点
                'confidence': self._calculate_confidence(fib_levels, df)
            }
            
        except Exception as e:
            self.logger.error(f"斐波那契分析失败: {e}")
            return {'error': str(e)}
    
    def _find_swing_points(self, df: pd.DataFrame, window: int = 10) -> List[SwingPoint]:
        """识别波段高低点"""
        swing_points = []
        
        # 使用滑动窗口识别局部极值
        for i in range(window, len(df) - window):
            # 波段高点
            if df['high'].iloc[i] == df['high'].iloc[i-window:i+window+1].max():
                strength = self._calculate_swing_strength(df, i, 'high', window)
                swing_points.append(SwingPoint(
                    price=df['high'].iloc[i],
                    timestamp=str(df.index[i]),
                    type='high',
                    strength=strength
                ))
            
            # 波段低点
            if df['low'].iloc[i] == df['low'].iloc[i-window:i+window+1].min():
                strength = self._calculate_swing_strength(df, i, 'low', window)
                swing_points.append(SwingPoint(
                    price=df['low'].iloc[i],
                    timestamp=str(df.index[i]),
                    type='low',
                    strength=strength
                ))
        
        # 按时间排序
        swing_points.sort(key=lambda x: x.timestamp)
        
        return swing_points
    
    def _calculate_swing_strength(self, df: pd.DataFrame, index: int, swing_type: str, window: int) -> float:
        """计算波段点强度"""
        try:
            if swing_type == 'high':
                price = df['high'].iloc[index]
                surrounding_prices = df['high'].iloc[index-window:index+window+1]
                volume = df['volume'].iloc[index-window:index+window+1].mean()
            else:
                price = df['low'].iloc[index]
                surrounding_prices = df['low'].iloc[index-window:index+window+1]
                volume = df['volume'].iloc[index-window:index+window+1].mean()
            
            # 基于价格差异计算强度
            price_diff = abs(price - surrounding_prices.median()) / price
            
            # 基于成交量计算强度
            avg_volume = df['volume'].mean()
            volume_strength = min(volume / avg_volume, 2.0) if avg_volume > 0 else 1.0
            
            return min(price_diff * volume_strength * 100, 100)
            
        except Exception:
            return 50.0  # 默认强度
    
    def _get_major_swing(self, swing_points: List[SwingPoint], df: pd.DataFrame) -> Optional[Dict]:
        """获取最近的主要波段"""
        if len(swing_points) < 2:
            return None
        
        # 过滤高强度波段点
        strong_points = [p for p in swing_points if p.strength > 30]
        
        if len(strong_points) < 2:
            strong_points = swing_points[-10:]  # 使用最近10个点
        
        # 找到最近的高低点对
        recent_highs = [p for p in strong_points if p.type == 'high'][-3:]
        recent_lows = [p for p in strong_points if p.type == 'low'][-3:]
        
        if not recent_highs or not recent_lows:
            return None
        
        # 选择最高点和最低点
        highest = max(recent_highs, key=lambda x: x.price)
        lowest = min(recent_lows, key=lambda x: x.price)
        
        return {
            'high': highest.price,
            'low': lowest.price,
            'high_time': highest.timestamp,
            'low_time': lowest.timestamp
        }
    
    def _calculate_fibonacci_levels(self, high: float, low: float) -> FibonacciLevels:
        """计算斐波那契水平"""
        diff = high - low
        
        # 回撤位（从高点向下）
        retracement = {}
        for level in self.retracement_levels:
            retracement[level] = high - (diff * level)
        
        # 扩展位（突破低点后的目标）
        extension = {}
        for level in self.extension_levels:
            extension[level] = low - (diff * (level - 1))
        
        # 投射位（突破高点后的目标）
        projection = {}
        for level in self.projection_levels:
            projection[level] = high + (diff * level)
        
        return FibonacciLevels(
            swing_high=high,
            swing_low=low,
            retracement=retracement,
            extension=extension,
            projection=projection
        )
    
    def _analyze_price_position(self, current_price: float, fib_levels: FibonacciLevels) -> Dict:
        """分析当前价格位置"""
        position_info = {
            'current_price': current_price,
            'swing_range_pct': 0,
            'nearest_support': None,
            'nearest_resistance': None,
            'trend_bias': 'neutral'
        }
        
        # 计算在波段中的位置百分比
        total_range = fib_levels.swing_high - fib_levels.swing_low
        if total_range > 0:
            position_info['swing_range_pct'] = (current_price - fib_levels.swing_low) / total_range * 100
        
        # 找到最近的支撑阻力位
        all_levels = []
        all_levels.extend(fib_levels.retracement.values())
        all_levels.extend([fib_levels.swing_high, fib_levels.swing_low])
        
        # 支撑位（当前价格下方最近的水平）
        support_levels = [level for level in all_levels if level < current_price]
        if support_levels:
            position_info['nearest_support'] = max(support_levels)
        
        # 阻力位（当前价格上方最近的水平）
        resistance_levels = [level for level in all_levels if level > current_price]
        if resistance_levels:
            position_info['nearest_resistance'] = min(resistance_levels)
        
        # 趋势偏向
        if position_info['swing_range_pct'] > 60:
            position_info['trend_bias'] = 'bullish'
        elif position_info['swing_range_pct'] < 40:
            position_info['trend_bias'] = 'bearish'
        
        return position_info
    
    def _identify_key_levels(self, fib_levels: FibonacciLevels, df: pd.DataFrame) -> List[Dict]:
        """识别关键支撑阻力位"""
        key_levels = []
        current_price = df['close'].iloc[-1]
        
        # 添加斐波那契关键位
        important_retracements = [0.382, 0.5, 0.618]
        for level in important_retracements:
            price = fib_levels.retracement[level]
            key_levels.append({
                'price': price,
                'type': 'fibonacci_retracement',
                'level': level,
                'strength': 'high',
                'distance_pct': abs(price - current_price) / current_price * 100
            })
        
        # 添加波段高低点
        key_levels.append({
            'price': fib_levels.swing_high,
            'type': 'swing_high',
            'strength': 'very_high',
            'distance_pct': abs(fib_levels.swing_high - current_price) / current_price * 100
        })
        
        key_levels.append({
            'price': fib_levels.swing_low,
            'type': 'swing_low',
            'strength': 'very_high',
            'distance_pct': abs(fib_levels.swing_low - current_price) / current_price * 100
        })
        
        # 按距离当前价格远近排序
        key_levels.sort(key=lambda x: x['distance_pct'])
        
        return key_levels
    
    def _analyze_time_cycles(self, swing_points: List[SwingPoint], df: pd.DataFrame) -> Dict:
        """分析时间周期"""
        if len(swing_points) < 3:
            return {'error': '数据不足以进行时间周期分析'}
        
        try:
            # 计算波段间时间差
            time_differences = []
            for i in range(1, len(swing_points)):
                prev_time = pd.to_datetime(swing_points[i-1].timestamp)
                curr_time = pd.to_datetime(swing_points[i].timestamp)
                diff_hours = (curr_time - prev_time).total_seconds() / 3600
                time_differences.append(diff_hours)
            
            if not time_differences:
                return {'error': '无法计算时间差'}
            
            avg_cycle = np.mean(time_differences)
            
            # 预测下一个转折点时间
            last_swing_time = pd.to_datetime(swing_points[-1].timestamp)
            next_turning_point = last_swing_time + pd.Timedelta(hours=avg_cycle)
            
            return {
                'average_cycle_hours': avg_cycle,
                'cycle_consistency': np.std(time_differences) / avg_cycle if avg_cycle > 0 else 1,
                'next_turning_point': str(next_turning_point),
                'time_until_next': avg_cycle - ((pd.Timestamp.now() - last_swing_time).total_seconds() / 3600)
            }
            
        except Exception as e:
            return {'error': f'时间周期分析失败: {e}'}
    
    def _calculate_confidence(self, fib_levels: FibonacciLevels, df: pd.DataFrame) -> float:
        """计算分析置信度"""
        confidence_factors = []
        
        # 基于数据量
        data_points = len(df)
        data_confidence = min(data_points / 200, 1.0)  # 200个数据点为最佳
        confidence_factors.append(data_confidence)
        
        # 基于波段幅度
        swing_range = fib_levels.swing_high - fib_levels.swing_low
        current_price = df['close'].iloc[-1]
        range_confidence = min(swing_range / current_price * 10, 1.0)
        confidence_factors.append(range_confidence)
        
        # 基于成交量
        volume_std = df['volume'].std()
        volume_mean = df['volume'].mean()
        volume_confidence = min(volume_std / volume_mean, 1.0) if volume_mean > 0 else 0.5
        confidence_factors.append(volume_confidence)
        
        return np.mean(confidence_factors) * 100