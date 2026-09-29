"""VIP系统 - 5个漏洞修复版

修复点:
1. VIP经验同时计算充值与消费, 比例可配置 (recharge_ratio / consume_ratio)
2. 等级特权数据驱动 (LEVEL_CONFIG), 新增等级只需加配置不改核心代码
3. 每日礼包有领取记录与日期校验, 每人每天限领一次
4. 商店折扣真实生效, 扣款按折后价计算 (buy_shop_item)
5. VIP有等级上限 (默认VIP18), 超出上限的经验转为其他奖励
"""
from dataclasses import dataclass, field
from datetime import date


# 充值/消费换算VIP经验的默认比例
DEFAULT_RECHARGE_RATIO = 1.0
DEFAULT_CONSUME_RATIO = 1.0

# 超过等级上限后经验转化的奖励 (每1点溢出经验兑换的奖励)
DEFAULT_OVERFLOW_REWARDS = {"gold": 1}

# 每日礼包默认奖励
DEFAULT_DAILY_GIFT = {"gold": 100}


@dataclass(frozen=True)
class VIPLevel:
    level: int
    exp_required: int
    privileges: dict = field(default_factory=dict)


# 数据驱动的等级配置: 新增VIP等级只需在此追加一行, 无需修改核心代码。
# 每个等级是 (等级, 所需累计经验, 特权)。
LEVEL_CONFIG = (
    (1, 0, {"discount": 0.95, "daily_gift": {"gold": 100}}),
    (2, 100, {"discount": 0.90, "daily_gift": {"gold": 150}}),
    (3, 300, {"discount": 0.88, "daily_gift": {"gold": 200}}),
    (4, 600, {"discount": 0.85, "daily_gift": {"gold": 250}}),
    (5, 1000, {"discount": 0.80, "daily_gift": {"gold": 300}}),
    (6, 2000, {"discount": 0.78, "daily_gift": {"gold": 350}}),
    (7, 4000, {"discount": 0.75, "daily_gift": {"gold": 400}}),
    (8, 8000, {"discount": 0.72, "daily_gift": {"gold": 450}}),
    (9, 15000, {"discount": 0.70, "daily_gift": {"gold": 500}}),
    (10, 30000, {"discount": 0.65, "daily_gift": {"gold": 600}}),
    (11, 50000, {"discount": 0.62, "daily_gift": {"gold": 700}}),
    (12, 80000, {"discount": 0.60, "daily_gift": {"gold": 800}}),
    (13, 120000, {"discount": 0.58, "daily_gift": {"gold": 900}}),
    (14, 200000, {"discount": 0.55, "daily_gift": {"gold": 1000}}),
    (15, 300000, {"discount": 0.52, "daily_gift": {"gold": 1200}}),
    (16, 500000, {"discount": 0.50, "daily_gift": {"gold": 1500}}),
    (17, 800000, {"discount": 0.48, "daily_gift": {"gold": 1800}}),
    (18, 1000000, {"discount": 0.45, "daily_gift": {"gold": 2000}}),
)

DEFAULT_MAX_LEVEL = 18


class VipSystem:
    def __init__(self, level_config=None, max_level=DEFAULT_MAX_LEVEL,
                 recharge_ratio=DEFAULT_RECHARGE_RATIO,
                 consume_ratio=None,
                 overflow_rewards=None, daily_gift=None,
                 levels=None, consumption_ratio=None):
        # 兼容别名: levels=level_config, consumption_ratio=consume_ratio
        if level_config is None:
            level_config = levels if levels is not None else LEVEL_CONFIG
        if consume_ratio is None:
            consume_ratio = (DEFAULT_CONSUME_RATIO if consumption_ratio is None
                             else consumption_ratio)
        # 数据驱动等级表, 支持外部传入自定义配置
        self.max_level = max_level
        self.levels = {}
        for level, exp_required, privileges in level_config:
            if level > max_level:
                continue
            self.levels[level] = VIPLevel(level, exp_required, dict(privileges))
        # 经验换算比例可配置
        self.recharge_ratio = recharge_ratio
        self.consume_ratio = consume_ratio
        self.overflow_rewards = dict(
            DEFAULT_OVERFLOW_REWARDS if overflow_rewards is None else overflow_rewards
        )
        self.default_daily_gift = dict(
            DEFAULT_DAILY_GIFT if daily_gift is None else daily_gift
        )

        # 玩家累计VIP经验
        self.player_exp = {}
        # 每日礼包领取记录: {player_id: "YYYY-MM-DD"}
        self.daily_claimed = {}
        # 已超出等级上限转化的其他奖励: {player_id: {reward: amount}}
        self.overflow_claimed = {}

    # ---- 数据驱动: 新增等级不改核心代码 ----
    def add_level(self, level, exp_required, privileges):
        self.levels[level] = VIPLevel(level, exp_required, dict(privileges))
        if level > self.max_level:
            self.max_level = level

    def _exp_cap(self):
        """最高等级所需经验, 超出部分不再提升等级。"""
        return self.levels[self.max_level].exp_required

    # ---- 修复1: 充值与消费都计入VIP经验, 比例可配置 ----
    def add_exp(self, player_id, amount, is_recharge=True):
        if amount is None or amount < 0:
            return self.player_exp.get(player_id, 0)
        ratio = self.recharge_ratio if is_recharge else self.consume_ratio
        gained = int(amount * ratio)

        exp = self.player_exp.get(player_id, 0)
        exp_cap = self._exp_cap()
        if exp >= exp_cap:
            overflow = gained
        elif exp + gained > exp_cap:
            overflow = exp + gained - exp_cap
        else:
            overflow = 0

        # ---- 修复5: 经验封顶, 溢出转为其他奖励 ----
        if overflow > 0:
            self._grant_overflow(player_id, overflow)
            gained -= overflow

        self.player_exp[player_id] = exp + gained
        return self.player_exp[player_id]

    def _grant_overflow(self, player_id, overflow):
        rewards = self.overflow_claimed.setdefault(player_id, {})
        for name, per_point in self.overflow_rewards.items():
            rewards[name] = rewards.get(name, 0) + int(overflow * per_point)

    def get_overflow_rewards(self, player_id):
        return dict(self.overflow_claimed.get(player_id, {}))

    # ---- 修复2: 特权从数据驱动的等级配置读取 ----
    def _level_data(self, level):
        if level in self.levels:
            return self.levels[level]
        data = None
        for lvl, level_info in sorted(self.levels.items()):
            if lvl <= level:
                data = level_info
        return data

    def get_privilege(self, player_id, priv_name, default=None):
        level = self.get_level(player_id)
        data = self._level_data(level)
        if data is not None and priv_name in data.privileges:
            return data.privileges[priv_name]
        if priv_name == "discount":
            return 1.0
        return default

    # ---- 修复5: 等级有上限 ----
    def get_level(self, player_id):
        exp = self.player_exp.get(player_id, 0)
        level = 0
        for lvl, data in sorted(self.levels.items()):
            if exp >= data.exp_required:
                level = lvl
        return level

    # ---- 修复3: 每日礼包记录领取日期, 每天限领一次 ----
    def _today(self, today=None):
        if today is None:
            return date.today().isoformat()
        if hasattr(today, "isoformat"):
            return today.isoformat()
        return str(today)

    def can_claim_daily(self, player_id, today=None):
        return self.daily_claimed.get(player_id) != self._today(today)

    def claim_daily(self, player_id, today=None):
        day = self._today(today)
        if self.daily_claimed.get(player_id) == day:
            return None
        self.daily_claimed[player_id] = day
        gift = self.get_privilege(player_id, "daily_gift", self.default_daily_gift)
        return dict(gift)

    # ---- 修复4: 折扣真实生效, 显示价即实际扣款价 ----
    def get_shop_price(self, player_id, base_price):
        discount = self.get_privilege(player_id, "discount", 1.0)
        return int(base_price * discount)

    def buy_shop_item(self, player_id, base_price, wallet):
        """按折后价扣款, 返回实际支付金额; 余额不足返回None且不扣款。"""
        price = self.get_shop_price(player_id, base_price)
        if wallet.get("gold", 0) < price:
            return None
        wallet["gold"] = wallet["gold"] - price
        return price

    # 常见命名别名, 方便不同调用方
    buy_item = buy_shop_item
    purchase = buy_shop_item
