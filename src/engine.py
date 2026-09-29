"""VIP系统 - 修复版"""
from dataclasses import dataclass, field
from datetime import date


@dataclass
class VIPLevel:
    level: int
    exp_required: int
    privileges: dict


# 数据驱动的等级配置：新增/调整等级只改这里，不改核心代码
DEFAULT_LEVELS = {
    1: VIPLevel(1, 0, {"discount": 0.95, "daily_gift": {"gold": 100}}),
    2: VIPLevel(2, 100, {"discount": 0.9, "daily_gift": {"gold": 200}}),
    3: VIPLevel(3, 300, {"discount": 0.85, "daily_gift": {"gold": 300}}),
    18: VIPLevel(18, 100000, {"discount": 0.5, "daily_gift": {"gold": 5000}}),
}

DEFAULT_CONFIG = {
    "recharge_ratio": 1.0,      # 充值换算VIP经验比例
    "consumption_ratio": 1.0,   # 消费换算VIP经验比例
    "overflow_reward_ratio": 0.1,  # 超出上限的经验转为金币的比例
}


class VipSystem:
    def __init__(self, levels=None, config=None, today=None):
        self.levels = dict(levels) if levels else dict(DEFAULT_LEVELS)
        self.config = {**DEFAULT_CONFIG, **(config or {})}
        self._today = today or date.today
        self.max_level = max(self.levels)
        self.player_exp = {}
        self.daily_claimed = {}  # player_id -> 最近领取日期
        self.overflow_rewards = {}  # player_id -> 超出上限转换的奖励

    def add_exp(self, player_id, amount, is_recharge=True):
        # 修复bug1: 充值和消费都计入VIP经验，比例可配置
        ratio = self.config["recharge_ratio"] if is_recharge else self.config["consumption_ratio"]
        gained = amount * ratio
        cap_exp = self.levels[self.max_level].exp_required
        current = self.player_exp.get(player_id, 0)
        new_exp = current + gained
        # 修复bug5: 经验封顶，超出部分按比例转为其他奖励
        if new_exp > cap_exp:
            overflow = new_exp - cap_exp
            gold = int(overflow * self.config["overflow_reward_ratio"])
            rewards = self.overflow_rewards.setdefault(player_id, {"gold": 0})
            rewards["gold"] = rewards.get("gold", 0) + gold
            new_exp = cap_exp
        self.player_exp[player_id] = new_exp

    def get_privilege(self, player_id, priv_name):
        # 修复bug2: 特权从等级配置中读取，数据驱动
        level = self.get_level(player_id)
        best = None
        for lvl in sorted(self.levels):
            if lvl <= level and priv_name in self.levels[lvl].privileges:
                best = self.levels[lvl].privileges[priv_name]
        return best

    def claim_daily(self, player_id):
        # 修复bug3: 记录领取日期，同一天只能领一次
        today = self._today()
        if self.daily_claimed.get(player_id) == today:
            return None
        self.daily_claimed[player_id] = today
        gift = self.get_privilege(player_id, "daily_gift")
        return dict(gift) if gift else None

    def get_shop_price(self, player_id, base_price):
        # 修复bug4: 折扣真实生效，返回折后价用于实际扣款
        discount = self.get_privilege(player_id, "discount")
        if discount is None:
            discount = 1.0
        return base_price * discount

    def get_level(self, player_id):
        exp = self.player_exp.get(player_id, 0)
        level = 1
        for lvl, data in sorted(self.levels.items()):
            if exp >= data.exp_required:
                level = lvl
        # 修复bug5: 等级不超过配置的最高等级
        return min(level, self.max_level)
