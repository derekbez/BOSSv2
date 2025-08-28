"""
Unit tests for GPIO screen implementations (Textual primary, Rich fallback; Pillow removed)
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from boss.infrastructure.hardware.gpio.gpio_screens import GPIORichScreen
from boss.domain.models.config import HardwareConfig


@pytest.fixture
def hardware_config():
    """Create a test hardware configuration."""
    return HardwareConfig(
    switch_data_pin=18,
    switch_select_pins=[23,24,25],
    go_button_pin=4,
    button_pins={"red":5,"yellow":6,"green":13,"blue":19},
    led_pins={"red":21,"yellow":20,"green":26,"blue":12},
    display_clk_pin=2,
    display_dio_pin=3,
    screen_width=800,
    screen_height=480,
    screen_backend="textual",
    screen_fullscreen=False,
    enable_audio=False,
    audio_volume=50
    )


class TestGPIORichScreen:
    """Test cases for GPIORichScreen implementation (Pillow removed)."""
    
    def test_init(self, hardware_config):
        """Test GPIORichScreen initialization."""
        with patch('boss.infrastructure.hardware.gpio.gpio_screens.Console') as mock_console:
            screen = GPIORichScreen(hardware_config)
            assert screen.hardware_config == hardware_config
            assert not screen.is_available
            mock_console.assert_called_once()
    
    def test_initialize_success(self, hardware_config):
        """Test successful initialization of GPIORichScreen."""
        with patch('boss.infrastructure.hardware.gpio.gpio_screens.Console'):
            screen = GPIORichScreen(hardware_config)
            result = screen.initialize()
            assert result is True
            assert screen.is_available is True
    
    def test_only_rich_screen_present(self, hardware_config):
        screen = GPIORichScreen(hardware_config)
        ok = screen.initialize()
        assert ok is True
        size = screen.get_screen_size()
        assert isinstance(size, tuple) and len(size) == 2

    def test_display_panel(self, hardware_config):
        """Test Rich panel display functionality."""
        with patch('boss.infrastructure.hardware.gpio.gpio_screens.Console') as mock_console:
            with patch('boss.infrastructure.hardware.gpio.gpio_screens.Panel') as mock_panel:
                mock_console_instance = Mock()
                mock_console.return_value = mock_console_instance
                mock_panel_instance = Mock()
                mock_panel.return_value = mock_panel_instance
                
                screen = GPIORichScreen(hardware_config)
                screen.initialize()
                screen.display_panel("Test content", "Test Title", "red")
                
                mock_panel.assert_called_with("Test content", title="Test Title", border_style="red")
                mock_console_instance.clear.assert_called()
                mock_console_instance.print.assert_called_with(mock_panel_instance)

    def test_display_tree(self, hardware_config):
        """Test Rich tree display functionality."""
        with patch('boss.infrastructure.hardware.gpio.gpio_screens.Console') as mock_console:
            with patch('boss.infrastructure.hardware.gpio.gpio_screens.Tree') as mock_tree:
                mock_console_instance = Mock()
                mock_console.return_value = mock_console_instance
                mock_tree_instance = Mock()
                mock_tree.return_value = mock_tree_instance
                
                screen = GPIORichScreen(hardware_config)
                screen.initialize()
                
                tree_data = {"branch1": {"leaf1": "value1", "leaf2": "value2"}}
                screen.display_tree(tree_data, "Root")
                
                mock_tree.assert_called_with("Root")
                mock_console_instance.clear.assert_called()
                mock_console_instance.print.assert_called_with(mock_tree_instance)

    def test_display_code(self, hardware_config):
        """Test Rich syntax highlighting functionality."""
        with patch('boss.infrastructure.hardware.gpio.gpio_screens.Console') as mock_console:
            with patch('boss.infrastructure.hardware.gpio.gpio_screens.Syntax') as mock_syntax:
                mock_console_instance = Mock()
                mock_console.return_value = mock_console_instance
                mock_syntax_instance = Mock()
                mock_syntax.return_value = mock_syntax_instance
                
                screen = GPIORichScreen(hardware_config)
                screen.initialize()
                screen.display_code("print('hello')", "python", "monokai")
                
                mock_syntax.assert_called_with("print('hello')", "python", theme="monokai", line_numbers=True)
                mock_console_instance.clear.assert_called()
                mock_console_instance.print.assert_called_with(mock_syntax_instance)

    def test_display_markup(self, hardware_config):
        """Test Rich markup display functionality."""
        with patch('boss.infrastructure.hardware.gpio.gpio_screens.Console') as mock_console:
            mock_console_instance = Mock()
            mock_console.return_value = mock_console_instance
            
            screen = GPIORichScreen(hardware_config)
            screen.initialize()
            screen.display_markup("[bold red]Bold Red Text[/bold red]")
            
            mock_console_instance.clear.assert_called()
            mock_console_instance.print.assert_called_with("[bold red]Bold Red Text[/bold red]")

    def test_rich_features_not_available(self, hardware_config):
        """Test Rich-specific features when screen is not available."""
        with patch('boss.infrastructure.hardware.gpio.gpio_screens.Console'):
            screen = GPIORichScreen(hardware_config)
            # Don't initialize, so is_available remains False
            
            # All these should not raise exceptions, just log warnings
            screen.display_table({"test": "data"})
            screen.display_progress(50.0)
            screen.display_panel("content")
            screen.display_tree({"test": "data"})
            screen.display_code("code")
            screen.display_markup("markup")


def test_pillow_symbol_removed():
    import boss.infrastructure.hardware.gpio.gpio_screens as mod
    assert 'GPIOPillowScreen' not in dir(mod)