"""VIP系统 - 带5个bug"""
from dataclasses import dataclass, field

@dataclass
class VIPLevel:
    level: int
    exp_required: int
    privileges: dict

class VipSystem:
    def __init__(self):
        self.levels = {1: VIPLevel(1, 0, {"discount": 0.95}), 2: VIPLevel(2, 100, {"discount": 0.9})}
        self.player_exp = {}
        self.daily_claimed = {}  # bug3: 无记录

    def add_exp(self, player_id, amount, is_recharge=True):
        # bug1: 只算充值
        if is_recharge:
            self.player_exp[player_id] = self.player_exp.get(player_id, 0) + amount

    def get_privilege(self, player_id, priv_name):
        level = self.get_level(player_id)
        # bug2: 硬编码
        if priv_name == "discount":
            return 0.95 if level >= 1 else 1.0
        return None

    def claim_daily(self, player_id):
        # bug3: 无领取记录
        return {"gold": 100}

    def get_shop_price(self, player_id, base_price):
        level = self.get_level(player_id)
        # bug4: 折扣只显示不生效
        display_price = base_price * 0.9
        return base_price  # 实际扣款原价

    def get_level(self, player_id):
        exp = self.player_exp.get(player_id, 0)
        # bug5: 无上限
        level = 1
        for lvl, data in sorted(self.levels.items()):
            if exp >= data.exp_required:
                level = lvl
        return level
