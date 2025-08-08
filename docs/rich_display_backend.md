# Rich Display Backend

The Rich Display Backend provides enhanced console-style display capabilities for BOSS applications, offering advanced features like tables, progress bars, syntax highlighting, and rich text formatting.

## Overview

The Rich backend uses the [Rich library](https://rich.readthedocs.io/) to provide modern, feature-rich console output. Unlike the Pillow backend which renders pixel-perfect graphics, the Rich backend focuses on structured, text-based content with enhanced formatting and styling.

## Features

### Core Features (Baseline Parity)
- Text display with color, background, and alignment
- Screen clearing with background colors
- Multi-line text support
- Screen size management

### Enhanced Rich Features
- **Tables**: Structured data display with columns, rows, and styling
- **Progress Bars**: Animated progress indicators with descriptions
- **Panels**: Content with borders, titles, and styling
- **Trees**: Hierarchical data structures
- **Syntax Highlighting**: Code display with language-specific formatting
- **Rich Markup**: Advanced text formatting with colors, bold, italic

## Configuration

### System Configuration
Set the screen backend in `boss/config/boss_config.json`:

```json
{
  "hardware": {
    "screen_backend": "rich",
    "screen_width": 800,
    "screen_height": 480
  }
}
```

### App-Specific Configuration
Apps can specify their preferred backend in `manifest.json`:

```json
{
  "name": "My Rich App",
  "preferred_screen_backend": "rich"
}
```

## Usage Examples

### Basic Text Display
```python
def run(stop_event, api):
    # Standard text display (works with both backends)
    api.hardware.screen.display_text(
        "Hello World", 
        color="white", 
        background="blue", 
        align="center"
    )
```

### Rich-Specific Features
```python
def run(stop_event, api):
    # Check if Rich backend is available
    screen = api.hardware.screen
    if hasattr(screen, 'display_table'):
        # Rich-specific features
        
        # Display a table
        data = {
            "CPU": {"Usage": "45%", "Temp": "62°C"},
            "Memory": {"Used": "2.1GB", "Free": "1.9GB"}
        }
        screen.display_table(data, "System Status")
        
        # Display a progress bar
        screen.display_progress(75.0, "Loading...")
        
        # Display content in a panel
        screen.display_panel("Important info", "Alert", "red")
        
        # Display syntax-highlighted code
        code = "def hello(): print('world')"
        screen.display_code(code, "python")
        
        # Display rich markup
        screen.display_markup("[bold red]Error:[/bold red] Connection failed")
        
    else:
        # Fallback for Pillow backend
        api.hardware.screen.display_text("Rich features not available")
```

## API Reference

### GPIORichScreen Methods

#### Core Methods (ScreenInterface)
- `initialize() -> bool`: Initialize the Rich console
- `cleanup() -> None`: Clean up resources
- `clear_screen(color="black") -> None`: Clear screen with background color
- `display_text(text, font_size=48, color="white", background="black", align="center") -> None`: Display text
- `display_image(image_path, scale=1.0, position=(0,0)) -> None`: Display image placeholder
- `get_screen_size() -> tuple`: Get screen dimensions

#### Rich-Specific Methods
- `display_table(table_data: dict, title: str = None) -> None`: Display structured data as a table
- `display_progress(progress_value: float, description: str = "Progress") -> None`: Display progress bar (0-100)
- `display_panel(content: str, title: str = None, border_style: str = "blue") -> None`: Display content in bordered panel
- `display_tree(tree_data: dict, root_label: str = "Root") -> None`: Display hierarchical data as tree
- `display_code(code: str, language: str = "python", theme: str = "monokai") -> None`: Display syntax-highlighted code
- `display_markup(markup_text: str) -> None`: Display Rich markup formatting

## Performance Considerations

### Character vs Pixel Dimensions
The Rich backend operates in character mode, automatically converting pixel dimensions:
- Character width = screen_width / 8
- Character height = screen_height / 16

### Memory Usage
Rich backend typically uses less memory than Pillow for text-heavy content but may use more for complex layouts with many elements.

### Rendering Speed
- Simple text: Very fast (< 10ms)
- Tables and panels: Fast (10-50ms) 
- Complex trees and code: Moderate (50-100ms)

## Development Guidelines

### Feature Detection
Always check for Rich-specific features before using them:

```python
screen = api.hardware.screen
if hasattr(screen, 'display_table'):
    # Rich backend available
    screen.display_table(data)
else:
    # Fallback to basic text
    api.hardware.screen.display_text("Data not available")
```

### Graceful Degradation
Design apps to work with both backends:

```python
def show_data(api, data):
    screen = api.hardware.screen
    
    if hasattr(screen, 'display_table'):
        # Rich: Show structured table
        screen.display_table(data, "Results")
    else:
        # Pillow: Show formatted text
        text = "Results:\\n" + "\\n".join([f"{k}: {v}" for k, v in data.items()])
        screen.display_text(text, align="left")
```

### Best Practices
- Use Rich features for structured data (tables, trees)
- Use progress bars for long operations
- Use panels to highlight important information
- Use syntax highlighting for code display
- Test apps with both backends during development

## Hardware Output (Raspberry Pi)

### Console Redirection
On Raspberry Pi, Rich output can be redirected to the framebuffer for display on the physical HDMI screen. This requires additional configuration:

```python
# Future implementation: framebuffer redirection
console = Console(file=framebuffer_wrapper, force_terminal=True)
```

### Display Considerations
- Rich content appears as text on the physical display
- Colors are mapped to the display's color space
- Content is formatted for the target resolution
- Works in headless mode without SSH connection

## Troubleshooting

### Common Issues

1. **Rich Features Not Available**
   - Check `requirements.txt` includes `rich>=13.0.0`
   - Verify Rich is installed: `pip install rich`
   - Check screen backend configuration

2. **Display Not Appearing**
   - Verify `screen_backend` is set to "rich"
   - Check hardware initialization logs
   - Ensure Rich console is properly configured

3. **Performance Issues**
   - Reduce complexity of tables and trees
   - Use simpler markup formatting
   - Consider caching for repeated displays

### Debug Commands
```python
# Check Rich availability
try:
    import rich
    print(f"Rich version: {rich.__version__}")
except ImportError:
    print("Rich not available")

# Check backend type
screen = api.hardware.screen
backend_type = "rich" if hasattr(screen, 'display_table') else "pillow"
print(f"Backend: {backend_type}")
```

## Migration Guide

### From Pillow to Rich
1. Update `screen_backend` configuration to "rich"
2. Test existing apps - basic text display should work unchanged
3. Enhance apps with Rich-specific features where beneficial
4. Add feature detection for cross-backend compatibility

### App Modernization
- Replace complex text formatting with Rich markup
- Use tables instead of manually formatted text columns
- Add progress bars for loading operations
- Use panels for alerts and important information

## Examples

See the `rich_demo` app for comprehensive examples of all Rich features:
- Location: `boss/apps/rich_demo/`
- Demonstrates: tables, progress, panels, trees, code, markup
- Shows: fallback behavior for Pillow backend