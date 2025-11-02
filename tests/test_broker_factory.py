import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import config as app_config
from src.tradingagent.core.brokers import BrokerFactory, SimulationBroker


def teardown_module(module):
    """测试结束后清理注册表, 确保其它用例使用默认状态。"""
    # 重置为默认仿真券商
    BrokerFactory.unregister("temp")
    BrokerFactory.set_default("simulation")


def test_factory_returns_default_simulation_broker():
    """验证默认情况下可以创建仿真券商。"""
    broker = BrokerFactory.create()
    assert isinstance(broker, SimulationBroker)


def test_resolve_simulation_from_config():
    """验证配置默认券商解析结果。"""
    broker_type, params = app_config.resolve_broker("simulation")
    assert broker_type == "simulation"
    assert isinstance(params, dict)


def test_register_custom_broker(monkeypatch):
    """验证注册自定义券商构造器后可被创建。"""

    class DummyBroker(SimulationBroker):
        """提供可检测的自定义券商实现。"""

    def builder(**kwargs):
        return DummyBroker(**kwargs)

    BrokerFactory.register("temp", builder, is_default=True)

    broker = BrokerFactory.create()
    assert isinstance(broker, DummyBroker)


def test_alpaca_registered():
    """验证 Alpaca 券商已默认注册。"""
    assert "alpaca" in BrokerFactory.registered_brokers()
