"""
Interactive menu system for PWA CLI
"""

import sys
from typing import Any, Callable, Dict, List, Optional

from .colors import Colors


class MenuItem:
    """Represents a single menu item"""

    def __init__(self, key: str, title: str, action: Callable, description: str = ""):
        self.key = key
        self.title = title
        self.action = action
        self.description = description

    def execute(self, context: Dict[str, Any] = None):
        """Execute the menu item's action"""
        if context is None:
            context = {}
        return self.action(context)


class Menu:
    """Interactive menu system"""

    def __init__(self, title: str, items: List[MenuItem] = None):
        self.title = title
        self.items = items or []
        self.running = True

    def add_item(self, item: MenuItem):
        """Add a menu item"""
        self.items.append(item)

    def add_separator(self):
        """Add a visual separator"""
        self.items.append(None)

    def display(self):
        """Display the menu"""
        self._clear_screen()
        self._print_header()
        self._print_items()
        self._print_footer()

    def _clear_screen(self):
        """Clear the terminal screen"""
        print("\033[2J\033[H", end="")

    def _print_header(self):
        """Print menu header"""
        width = 60
        print("╔" + "═" * (width - 2) + "╗")
        title_text = f"  {self.title}  "
        padding = (width - len(title_text) - 2) // 2
        print(
            "║"
            + " " * padding
            + Colors.highlight(title_text)
            + " " * (width - padding - len(title_text) - 2)
            + "║"
        )
        print("╠" + "═" * (width - 2) + "╣")

    def _print_items(self):
        """Print menu items"""
        width = 60
        for item in self.items:
            if item is None:
                # Separator
                print("║" + "─" * (width - 2) + "║")
            else:
                # Menu item
                item_text = f"  {item.key}. {item.title}"
                padding = width - len(item_text) - 2
                print("║" + item_text + " " * padding + "║")

    def _print_footer(self):
        """Print menu footer"""
        width = 60
        print("╚" + "═" * (width - 2) + "╝")

    def get_input(self, prompt: str = "请选择") -> str:
        """Get user input"""
        try:
            return input(f"\n{Colors.info(prompt)}: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n")
            return "0"

    def run(self, context: Dict[str, Any] = None):
        """Run the menu loop"""
        if context is None:
            context = {}

        self.running = True

        while self.running:
            self.display()
            choice = self.get_input()

            if choice == "0":
                self.running = False
                continue

            # Find and execute the selected item
            found = False
            for item in self.items:
                if item and item.key == choice:
                    found = True
                    try:
                        result = item.execute(context)
                        if result == "exit":
                            self.running = False
                        elif result == "back":
                            self.running = False
                        else:
                            self._pause()
                    except Exception as e:
                        from .colors import print_error

                        print_error(f"执行失败: {str(e)}")
                        self._pause()
                    break

            if not found and choice != "0":
                from .colors import print_warning

                print_warning(f"无效的选择: {choice}")
                self._pause()

    def _pause(self):
        """Pause and wait for user to press Enter"""
        try:
            input(f"\n{Colors.info('按 Enter 继续')}...")
        except (KeyboardInterrupt, EOFError):
            pass


class MenuBuilder:
    """Builder for creating menus"""

    def __init__(self, title: str):
        self.menu = Menu(title)

    def add_item(self, key: str, title: str, action: Callable, description: str = ""):
        """Add a menu item"""
        self.menu.add_item(MenuItem(key, title, action, description))
        return self

    def add_separator(self):
        """Add a separator"""
        self.menu.add_separator()
        return self

    def add_exit(self, key: str = "0", title: str = "退出"):
        """Add exit item"""

        def exit_action(ctx):
            return "exit"

        self.menu.add_item(MenuItem(key, title, exit_action))
        return self

    def add_back(self, key: str = "0", title: str = "返回上级菜单"):
        """Add back item"""

        def back_action(ctx):
            return "back"

        self.menu.add_item(MenuItem(key, title, back_action))
        return self

    def build(self) -> Menu:
        """Build and return the menu"""
        return self.menu


def create_submenu(title: str, parent_context: Dict[str, Any] = None) -> Menu:
    """Create a submenu that returns to parent when done"""
    menu = Menu(title)
    if parent_context is None:
        parent_context = {}
    return menu
