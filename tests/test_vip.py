"""VIP测试 - 5个漏洞修复后的6个用例"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from vip.system import VipSystem


class TestExp:
    def test_consumption_counts_with_ratio(self):
        # 消费同样计入VIP经验, 且比例可配置
        vs = VipSystem(consume_ratio=0.5)
        vs.add_exp("p1", 100, is_recharge=False)
        assert vs.player_exp["p1"] == 50, "消费经验比例不可配置"
        vs.add_exp("p1", 100, is_recharge=True)
        assert vs.player_exp["p1"] == 150, "充值经验计算错误"


class TestPrivilege:
    def test_privilege_data_driven(self):
        vs = VipSystem()
        # 新增等级只加配置, 不改核心代码
        vs.add_level(19, 5000, {"discount": 0.4, "daily_gift": {"gold": 5000}})
        vs.player_exp["p1"] = 5000
        assert vs.get_privilege("p1", "discount") == 0.4, "特权未从配置读取"


class TestDaily:
    def test_daily_once_per_day(self):
        vs = VipSystem()
        first = vs.claim_daily("p1", today="2026-09-29")
        assert first == {"gold": 100}, "首次领取礼包失败"
        again = vs.claim_daily("p1", today="2026-09-29")
        assert again is None, "同一天重复领取了礼包"
        next_day = vs.claim_daily("p1", today="2026-09-30")
        assert next_day == {"gold": 100}, "次日应可再次领取"


class TestShop:
    def test_discount_applied(self):
        vs = VipSystem()
        vs.player_exp["p1"] = 100
        price = vs.get_shop_price("p1", 100)
        assert price < 100, "VIP折扣不生效"
        assert price == 90, "折后价格计算错误"

    def test_purchase_charges_discounted_price(self):
        vs = VipSystem()
        vs.player_exp["p1"] = 100
        wallet = {"gold": 200}
        paid = vs.buy_shop_item("p1", 100, wallet)
        assert paid == 90, "实际扣款不是折后价"
        assert wallet["gold"] == 110, "钱包扣款金额错误"


class TestLevelCap:
    def test_level_capped_and_overflow_converted(self):
        vs = VipSystem()
        vs.add_exp("p1", 5_000_000, is_recharge=True)
        assert vs.get_level("p1") == vs.max_level == 18, "VIP等级没有上限"
        assert vs.player_exp["p1"] == vs.levels[18].exp_required, "经验未封顶"
        rewards = vs.get_overflow_rewards("p1")
        assert rewards.get("gold", 0) > 0, "超出上限的经验未转为其他奖励"
