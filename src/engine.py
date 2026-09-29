"""VIP系统入口 - 核心实现见 vip/system.py (5个漏洞已修复)

向后兼容: 原有代码从 src.engine 导入 VipSystem。
"""
from vip.system import VipSystem, VIPLevel

__all__ = ["VipSystem", "VIPLevel"]
