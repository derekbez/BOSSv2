"""
Unit tests for GPIO screen implementations (Rich and Pillow backends)
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from boss.infrastructure.hardware.gpio.gpio_screens import GPIORichScreen, GPIOPillowScreen
from boss.domain.models.config import HardwareConfig


@pytest.fixture
def hardware_config():
    """Create a test hardware configuration."""
    return HardwareConfig(
        screen_width=800,
        screen_height=480,
        screen_backend="rich"
    )


class TestGPIORichScreen:
    """Test cases for GPIORichScreen implementation."""
    
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
    
    def test_cleanup(self, hardware_config):
        """Test cleanup of GPIORichScreen."""
        with patch('boss.infrastructure.hardware.gpio.gpio_screens.Console') as mock_console:
            mock_console_instance = Mock()
            mock_console.return_value = mock_console_instance
            
            screen = GPIORichScreen(hardware_config)
            screen.initialize()
            screen.cleanup()
            
            assert not screen.is_available
            mock_console_instance.clear.assert_called_once()
    
    def test_clear_screen(self, hardware_config):
        """Test screen clearing functionality."""
        with patch('boss.infrastructure.hardware.gpio.gpio_screens.Console') as mock_console:
            mock_console_instance = Mock()
            mock_console.return_value = mock_console_instance
            
            screen = GPIORichScreen(hardware_config)
            screen.initialize()
            screen.clear_screen("blue")
            
            mock_console_instance.clear.assert_called()
            mock_console_instance.print.assert_called_with("", style="on blue")
    
    def test_display_text_center(self, hardware_config):
        """Test text display with center alignment."""
        with patch('boss.infrastructure.hardware.gpio.gpio_screens.Console') as mock_console:
            with patch('boss.infrastructure.hardware.gpio.gpio_screens.Text') as mock_text:
                mock_console_instance = Mock()
                mock_console.return_value = mock_console_instance
                mock_text_instance = Mock()
                mock_text.return_value = mock_text_instance
                
                screen = GPIORichScreen(hardware_config)
                screen.initialize()
                screen.display_text("Hello World", color="white", background="black", align="center")
                
                mock_text.assert_called_with("Hello World", style="white on black")
                mock_console_instance.clear.assert_called()
                mock_console_instance.print.assert_called_with(mock_text_instance, justify="center")
    
    def test_display_text_not_available(self, hardware_config):
        """Test text display when screen is not available."""
        with patch('boss.infrastructure.hardware.gpio.gpio_screens.Console'):
            screen = GPIORichScreen(hardware_config)
            # Don't initialize, so is_available remains False
            screen.display_text("Test")
            # Should not raise exception, just log warning
    
    def test_display_image(self, hardware_config):
        """Test image display (shows placeholder for Rich backend)."""
        with patch('boss.infrastructure.hardware.gpio.gpio_screens.Console') as mock_console:
            mock_console_instance = Mock()
            mock_console.return_value = mock_console_instance
            
            screen = GPIORichScreen(hardware_config)
            screen.initialize()
            screen.display_image("/path/to/image.png")
            
            mock_console_instance.print.assert_called_with("[Image: /path/to/image.png]", style="bold yellow")
    
    def test_get_screen_size(self, hardware_config):
        """Test getting screen dimensions."""
        with patch('boss.infrastructure.hardware.gpio.gpio_screens.Console'):
            screen = GPIORichScreen(hardware_config)
            size = screen.get_screen_size()
            assert size == (800, 480)

    def test_display_table(self, hardware_config):
        """Test Rich table display functionality."""
        with patch('boss.infrastructure.hardware.gpio.gpio_screens.Console') as mock_console:
            with patch('boss.infrastructure.hardware.gpio.gpio_screens.Table') as mock_table:
                mock_console_instance = Mock()
                mock_console.return_value = mock_console_instance
                mock_table_instance = Mock()
                mock_table.return_value = mock_table_instance
                
                screen = GPIORichScreen(hardware_config)
                screen.initialize()
                
                table_data = {"row1": {"col1": "data1", "col2": "data2"}}
                screen.display_table(table_data, "Test Table")
                
                mock_table.assert_called_with(title="Test Table")
                mock_console_instance.clear.assert_called()
                mock_console_instance.print.assert_called_with(mock_table_instance)

    def test_display_progress(self, hardware_config):
        """Test Rich progress bar display."""
        with patch('boss.infrastructure.hardware.gpio.gpio_screens.Console') as mock_console:
            with patch('boss.infrastructure.hardware.gpio.gpio_screens.Progress') as mock_progress:
                mock_console_instance = Mock()
                mock_console.return_value = mock_console_instance
                
                screen = GPIORichScreen(hardware_config)
                screen.initialize()
                screen.display_progress(75.0, "Loading...")
                
                mock_progress.assert_called()

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


class TestGPIOPillowScreen:
    """Test cases for GPIOPillowScreen implementation."""
    
    def test_init(self, hardware_config):
        """Test GPIOPillowScreen initialization."""
        screen = GPIOPillowScreen(hardware_config)
        assert screen.hardware_config == hardware_config
        assert not screen.is_available
    
    @patch('boss.infrastructure.hardware.gpio.gpio_screens.open')
    @patch('boss.infrastructure.hardware.gpio.gpio_screens.Image')
    @patch('boss.infrastructure.hardware.gpio.gpio_screens.ImageDraw')
    @patch('boss.infrastructure.hardware.gpio.gpio_screens.ImageFont')
    def test_initialize_success(self, mock_font, mock_draw, mock_image, mock_open, hardware_config):
        """Test successful initialization of GPIOPillowScreen."""
        # Mock file reads for framebuffer info
        mock_open.side_effect = [
            Mock(__enter__=Mock(return_value=Mock(read=Mock(return_value="800,480")))),
            Mock(__enter__=Mock(return_value=Mock(read=Mock(return_value="16"))))
        ]
        
        mock_image_instance = Mock()
        mock_image.new.return_value = mock_image_instance
        mock_draw_instance = Mock()
        mock_draw.Draw.return_value = mock_draw_instance
        mock_font.load_default.return_value = Mock()
        
        screen = GPIOPillowScreen(hardware_config)
        result = screen.initialize()
        
        assert result is True
        assert screen.is_available is True
    
    def test_initialize_failure(self, hardware_config):
        """Test failed initialization of GPIOPillowScreen."""
        with patch('boss.infrastructure.hardware.gpio.gpio_screens.Image.new', side_effect=Exception("Test error")):
            screen = GPIOPillowScreen(hardware_config)
            result = screen.initialize()
            
            assert result is False
            assert not screen.is_available
    
    def test_cleanup(self, hardware_config):
        """Test cleanup of GPIOPillowScreen."""
        screen = GPIOPillowScreen(hardware_config)
        screen._available = True
        screen.cleanup()
        
        assert not screen.is_available
        assert screen._image is None
    
    def test_get_screen_size(self, hardware_config):
        """Test getting screen dimensions."""
        screen = GPIOPillowScreen(hardware_config)
        size = screen.get_screen_size()
        assert size == (800, 480)


class TestScreenBackendComparison:
    """Test cases comparing Rich and Pillow backend behavior."""
    
    def test_both_backends_implement_interface(self, hardware_config):
        """Test that both backends implement the same interface methods."""
        with patch('boss.infrastructure.hardware.gpio.gpio_screens.Console'):
            rich_screen = GPIORichScreen(hardware_config)
            pillow_screen = GPIOPillowScreen(hardware_config)
            
            # Both should have the same interface methods
            interface_methods = ['initialize', 'cleanup', 'is_available', 'clear_screen', 
                               'display_text', 'display_image', 'get_screen_size']
            
            for method in interface_methods:
                assert hasattr(rich_screen, method)
                assert hasattr(pillow_screen, method)
                assert callable(getattr(rich_screen, method))
                assert callable(getattr(pillow_screen, method))
    
    def test_screen_size_consistency(self, hardware_config):
        """Test that both backends return consistent screen sizes."""
        with patch('boss.infrastructure.hardware.gpio.gpio_screens.Console'):
            rich_screen = GPIORichScreen(hardware_config)
            pillow_screen = GPIOPillowScreen(hardware_config)
            
            assert rich_screen.get_screen_size() == pillow_screen.get_screen_size()