"""
Rich Backend Development Test Script

This script helps developers test and validate Rich backend functionality
without requiring the full BOSS system. Useful for development and debugging.
"""

import sys
import time
from typing import Dict, Any

def test_rich_import():
    """Test if Rich library is available and get version info."""
    try:
        import rich
        from rich.console import Console
        from rich.table import Table
        from rich.progress import Progress
        from rich.panel import Panel
        from rich.tree import Tree
        from rich.syntax import Syntax
        
        print(f"✅ Rich library available - version {rich.__version__}")
        return True
    except ImportError as e:
        print(f"❌ Rich library not available: {e}")
        print("Install with: pip install rich>=13.0.0")
        return False

def test_basic_features():
    """Test basic Rich console features."""
    print("\n🧪 Testing Basic Rich Features:")
    
    try:
        from rich.console import Console
        console = Console()
        
        # Test basic console output
        console.print("✅ Basic console output works", style="green")
        console.print("✅ Styled text works", style="bold blue")
        console.print("✅ Markup works: [red]Red text[/red] and [bold]bold text[/bold]")
        
        return True
    except Exception as e:
        print(f"❌ Basic features failed: {e}")
        return False

def test_rich_features():
    """Test Rich-specific enhanced features."""
    print("\n🧪 Testing Rich Enhanced Features:")
    
    try:
        from rich.console import Console
        from rich.table import Table
        from rich.panel import Panel
        from rich.tree import Tree
        from rich.syntax import Syntax
        
        console = Console()
        
        # Test table
        table = Table(title="Test Table")
        table.add_column("Component", style="cyan")
        table.add_column("Status", style="green")
        table.add_row("Rich Backend", "Working")
        table.add_row("Console Output", "OK")
        console.print(table)
        print("✅ Table display works")
        
        # Test panel
        panel = Panel("This is a test panel with borders", title="Test Panel", border_style="blue")
        console.print(panel)
        print("✅ Panel display works")
        
        # Test tree
        tree = Tree("Test Tree")
        branch = tree.add("Branch 1")
        branch.add("Leaf 1")
        branch.add("Leaf 2")
        tree.add("Branch 2")
        console.print(tree)
        print("✅ Tree display works")
        
        # Test syntax highlighting
        code = '''def hello_boss():
    """Test function for BOSS."""
    print("Hello from BOSS Rich backend!")
    return {"status": "success"}'''
        
        syntax = Syntax(code, "python", theme="monokai", line_numbers=True)
        console.print(syntax)
        print("✅ Syntax highlighting works")
        
        return True
        
    except Exception as e:
        print(f"❌ Enhanced features failed: {e}")
        return False

def test_boss_integration():
    """Test Rich integration with BOSS-like API patterns."""
    print("\n🧪 Testing BOSS Integration Patterns:")
    
    try:
        # Simulate BOSS screen interface
        class MockBOSSScreen:
            def __init__(self):
                from rich.console import Console
                self.console = Console()
                self._available = True
            
            def display_text(self, text, color="white", background="black", align="center"):
                from rich.text import Text
                styled_text = Text(text, style=f"{color} on {background}")
                self.console.clear()
                self.console.print(styled_text, justify=align)
            
            def display_table(self, data, title=None):
                from rich.table import Table
                table = Table(title=title)
                
                if data:
                    # Add columns from first row
                    first_row = next(iter(data.values()))
                    if isinstance(first_row, dict):
                        for col_name in first_row.keys():
                            table.add_column(str(col_name), style="cyan")
                        
                        # Add rows
                        for row_name, row_data in data.items():
                            table.add_row(str(row_name), *[str(val) for val in row_data.values()])
                
                self.console.clear()
                self.console.print(table)
            
            def display_markup(self, markup):
                self.console.clear()
                self.console.print(markup)
        
        # Test the mock screen
        screen = MockBOSSScreen()
        
        # Test basic text
        screen.display_text("Hello BOSS!", "green", "black", "center")
        print("✅ BOSS-style text display works")
        
        # Test table
        test_data = {
            "CPU": {"Usage": "45%", "Temp": "62°C"},
            "Memory": {"Used": "2.1GB", "Free": "1.9GB"}
        }
        screen.display_table(test_data, "System Status")
        print("✅ BOSS-style table display works")
        
        # Test markup
        screen.display_markup("[bold green]✅ BOSS Rich Integration Success![/bold green]")
        print("✅ BOSS-style markup display works")
        
        return True
        
    except Exception as e:
        print(f"❌ BOSS integration failed: {e}")
        return False

def test_performance():
    """Test Rich performance characteristics."""
    print("\n⚡ Testing Rich Performance:")
    
    try:
        from rich.console import Console
        from rich.table import Table
        import time
        
        console = Console()
        
        # Test simple text performance
        start_time = time.time()
        for i in range(100):
            console.clear()
            console.print(f"Performance test iteration {i}", style="green")
        text_time = time.time() - start_time
        
        print(f"✅ 100 text displays: {text_time:.3f}s ({text_time*10:.1f}ms avg)")
        
        # Test table performance
        start_time = time.time()
        for i in range(10):
            table = Table(title=f"Performance Test {i}")
            table.add_column("Iteration", style="cyan")
            table.add_column("Status", style="green")
            for j in range(5):
                table.add_row(str(j), "OK")
            console.clear()
            console.print(table)
        table_time = time.time() - start_time
        
        print(f"✅ 10 table displays: {table_time:.3f}s ({table_time*100:.1f}ms avg)")
        
        return True
        
    except Exception as e:
        print(f"❌ Performance test failed: {e}")
        return False

def main():
    """Run all Rich backend tests."""
    print("🚀 BOSS Rich Backend Development Tester")
    print("=" * 50)
    
    all_passed = True
    
    # Run tests
    tests = [
        ("Rich Import", test_rich_import),
        ("Basic Features", test_basic_features),
        ("Rich Features", test_rich_features),
        ("BOSS Integration", test_boss_integration),
        ("Performance", test_performance)
    ]
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            if not result:
                all_passed = False
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 All Rich backend tests passed!")
        print("✅ Rich backend is ready for BOSS development")
    else:
        print("⚠️  Some tests failed - check output above")
        print("💡 See docs/rich_display_backend.md for troubleshooting")
    
    print("\n📖 Next steps:")
    print("- Review docs/rich_display_backend.md for usage examples")
    print("- Check boss/apps/rich_demo/ for feature demonstrations")
    print("- Test with actual BOSS system: python -m boss.main")

if __name__ == "__main__":
    main()