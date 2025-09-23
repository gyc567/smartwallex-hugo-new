#!/usr/bin/env python3
"""
加密货币合约分析器配置文件

定义支持的加密货币列表、分析参数和系统配置
遵循KISS原则，保持配置简单明了
"""

from typing import Dict, List, NamedTuple
from dataclasses import dataclass


class CryptoConfig(NamedTuple):
    """单个加密货币配置"""
    symbol: str           # 货币符号
    name: str            # 中文名称
    contract_type: str   # 合约类型
    min_leverage: int    # 最小杠杆
    max_leverage: int    # 最大杠杆
    risk_level: str      # 风险等级


@dataclass
class AnalysisConfig:
    """分析配置参数"""
    # 风险管理
    max_position_risk: float = 0.02  # 单笔最大风险2%
    min_risk_reward_ratio: float = 2.0  # 最小风险回报比1:2
    default_account_size: float = 10000.0  # 默认账户大小10000美元
    
    # AI模型参数
    temperature: float = 0.3  # 降低随机性
    max_tokens: int = 2000
    
    # 技术指标参数
    rsi_oversold: int = 30
    rsi_overbought: int = 70
    mcp_phases: List[str] = None
    
    def __post_init__(self):
        if self.mcp_phases is None:
            self.mcp_phases = ['积累', '上涨', '分布', '下跌']


# 支持的加密货币配置
SUPPORTED_CRYPTOS: Dict[str, CryptoConfig] = {
    'BTC': CryptoConfig(
        symbol='BTC',
        name='比特币',
        contract_type='USDT永续',
        min_leverage=1,
        max_leverage=5,
        risk_level='中等'
    ),
    'ETH': CryptoConfig(
        symbol='ETH',
        name='以太坊',
        contract_type='USDT永续',
        min_leverage=1,
        max_leverage=5,
        risk_level='中等'
    ),
    'BNB': CryptoConfig(
        symbol='BNB',
        name='币安币',
        contract_type='USDT永续',
        min_leverage=1,
        max_leverage=5,
        risk_level='中等'
    ),
    'SOL': CryptoConfig(
        symbol='SOL',
        name='Solana',
        contract_type='USDT永续',
        min_leverage=1,
        max_leverage=3,  # SOL波动较大，降低杠杆
        risk_level='高'
    ),
    'BCH': CryptoConfig(
        symbol='BCH',
        name='比特币现金',
        contract_type='USDT永续',
        min_leverage=1,
        max_leverage=5,
        risk_level='中等'
    )
}

# 分析配置实例
ANALYSIS_CONFIG = AnalysisConfig()

# 文章模板配置
ARTICLE_CONFIG = {
    'author': 'SmartWallex团队',
    'contact': {
        'website': 'https://smartwallex.com',
        'email': 'contact@smartwallex.com',
        'twitter': '@SmartWallex'
    },
    'categories': ['合约交易'],
    'base_tags': ['加密货币', '永续合约', '交易信号', '技术分析'],
    'disclaimer': '本报告基于技术分析提供参考信息，不构成投资建议。加密货币交易存在极高风险，请理性投资。'
}

# 日志配置
LOGGING_CONFIG = {
    'level': 'INFO',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'file_name': 'crypto_swap_analyzer.log'
}


def get_crypto_list() -> List[str]:
    """获取支持的加密货币列表"""
    return list(SUPPORTED_CRYPTOS.keys())


def get_crypto_config(symbol: str) -> CryptoConfig:
    """获取指定加密货币的配置
    
    Args:
        symbol: 加密货币符号
        
    Returns:
        CryptoConfig对象
        
    Raises:
        KeyError: 不支持的加密货币
    """
    if symbol not in SUPPORTED_CRYPTOS:
        raise KeyError(f"不支持的加密货币: {symbol}")
    return SUPPORTED_CRYPTOS[symbol]


def validate_config() -> bool:
    """验证配置的有效性
    
    Returns:
        配置有效返回True，否则返回False
    """
    try:
        # 验证必要的配置项
        assert len(SUPPORTED_CRYPTOS) == 5, "必须支持5种加密货币"
        assert all(crypto in ['BTC', 'ETH', 'BNB', 'SOL', 'BCH'] 
                  for crypto in SUPPORTED_CRYPTOS.keys()), "必须包含指定的5种货币"
        
        # 验证分析参数
        assert 0 < ANALYSIS_CONFIG.max_position_risk <= 0.05, "单笔风险应在0-5%之间"
        assert ANALYSIS_CONFIG.min_risk_reward_ratio >= 1.5, "风险回报比应≥1.5"
        assert ANALYSIS_CONFIG.default_account_size > 0, "账户大小必须为正数"
        
        # 验证加密货币配置
        for symbol, config in SUPPORTED_CRYPTOS.items():
            assert config.min_leverage >= 1, f"{symbol} 最小杠杆必须≥1"
            assert config.max_leverage <= 10, f"{symbol} 最大杠杆不应超过10"
            assert config.min_leverage <= config.max_leverage, f"{symbol} 杠杆配置无效"
            
        return True
        
    except AssertionError as e:
        print(f"配置验证失败: {e}")
        return False
    except Exception as e:
        print(f"配置验证出错: {e}")
        return False


if __name__ == "__main__":
    # 配置自测试
    print("🔧 加密货币合约分析器配置验证")
    print(f"支持的加密货币: {get_crypto_list()}")
    
    if validate_config():
        print("✅ 配置验证通过")
        for symbol in get_crypto_list():
            config = get_crypto_config(symbol)
            print(f"  {symbol} ({config.name}): {config.min_leverage}-{config.max_leverage}x杠杆, {config.risk_level}风险")
    else:
        print("❌ 配置验证失败")
        exit(1)