import os
import tempfile
from boss.core.config import ConfigManager

def test_config_load_and_save():
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = os.path.join(tmpdir, 'BOSSsettings.json')
        cm = ConfigManager(config_path)
        assert cm.validate()
        assert cm.get_app_for_value(1) is None
        cm.set_app_mapping(1, 'app_example', {'foo': 'bar'})
        assert cm.get_app_for_value(1)["app"] == 'app_example'
        assert cm.get_app_for_value(1)["params"]["foo"] == 'bar'
        # Reload and check persistence
        cm2 = ConfigManager(config_path)
        assert cm2.get_app_for_value(1)["app"] == 'app_example'
