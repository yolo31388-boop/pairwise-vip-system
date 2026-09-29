"""VIP测试"""
import pytest, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from src.engine import VipSystem

class TestExp:
    def test_consumption_counts(self):
        vs = VipSystem()
        vs.add_exp("p1", 50, is_recharge=False)
        assert vs.player_exp.get("p1",0) > 0, "消费不计VIP经验"

class TestShop:
    def test_discount_applied(self):
        vs = VipSystem()
        vs.player_exp["p1"] = 100
        price = vs.get_shop_price("p1", 100)
        assert price < 100, "VIP折扣不生效"
