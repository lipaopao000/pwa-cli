"""
Interactive menu with arrow key navigation
"""

import sys
from typing import List, Optional, Tuple, Callable
from dataclasses import dataclass

try:
    from prompt_toolkit import prompt
    from prompt_toolkit.shortcuts import radiolist_dialog, button_dialog
    from prompt_toolkit.styles import Style
    PROMPT_TOOLKIT_AVAILABLE = True
except ImportError:
    PROMPT_TOOLKIT_AVAILABLE = False

from .colors import Colors


@dataclass
class MenuOption:
    """Menu option"""
    key: str
    label: str
    description: str = ""
    action: Optional[Callable] = None
    submenu: Optional['InteractiveMenu'] = None


class InteractiveMenu:
    """Interactive menu with arrow key navigation"""
    
    def __init__(self, title: str, options: List[MenuOption], 
                 show_back: bool = False, show_quit: bool = True):
        """
        Initialize interactive menu
        
        Args:
            title: Menu title
            options: List of menu options
            show_back: Show "Back" option
            show_quit: Show "Quit" option
        """
        self.title = title
        self.options = options
        self.show_back = show_back
        self.show_quit = show_quit
        
        # Build option list with numbers
        self.option_list = []
        for i, opt in enumerate(options, 1):
            # Include number in the label for display
            display_label = f"{i}. {opt.label}"
            if opt.description:
                display_label += f" - {opt.description}"
            self.option_list.append((opt.key, display_label))
        
        if show_back:
            back_num = len(options) + 1
            self.option_list.append(('back', f'{back_num}. 返回上级菜单'))
        
        if show_quit:
            quit_num = len(options) + (1 if show_back else 0) + 1
            self.option_list.append(('quit', f'{quit_num}. 退出'))
    
    def show(self) -> Optional[str]:
        """
        Show menu and return selected option key
        
        Returns:
            Selected option key or None
        """
        if PROMPT_TOOLKIT_AVAILABLE:
            return self._show_with_prompt_toolkit()
        else:
            return self._show_fallback()
    
    def _show_with_prompt_toolkit(self) -> Optional[str]:
        """Show menu using prompt_toolkit"""
        try:
            # Show radio list dialog
            result = radiolist_dialog(
                title=self.title,
                text="使用 ↑/↓ 箭头键选择，Enter 确认",
                values=self.option_list,
            ).run()
            
            return result
        except Exception as e:
            # If prompt_toolkit fails, fall back to traditional menu
            print(f"{Colors.YELLOW}⚠️  交互式菜单出错，切换到传统模式{Colors.RESET}")
            print(f"{Colors.DIM}错误: {str(e)}{Colors.RESET}\n")
            return self._show_fallback()
    
    def _show_fallback(self) -> Optional[str]:
        """Fallback menu without arrow key support"""
        print(f"\n{Colors.BLUE}{'=' * 60}{Colors.RESET}")
        print(f"{Colors.BOLD}{self.title}{Colors.RESET}")
        print(f"{Colors.BLUE}{'=' * 60}{Colors.RESET}\n")
        
        # Display options with numbers
        for i, (key, label) in enumerate(self.option_list, 1):
            # Extract just the label part (remove number if already present)
            if '. ' in label:
                label_parts = label.split('. ', 1)
                if len(label_parts) > 1:
                    label = label_parts[1]
            print(f"  {i}. {label}")
        
        print()
        choice = input(f"{Colors.GREEN}请选择 (1-{len(self.option_list)}): {Colors.RESET}").strip()
        
        # Support both number and key input
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(self.option_list):
                return self.option_list[idx][0]
        else:
            # Try to match by key
            for key, _ in self.option_list:
                if key == choice:
                    return key
        
        return None
    
    def run(self, context: dict = None) -> bool:
        """
        Run menu loop
        
        Args:
            context: Context dictionary to pass to actions
            
        Returns:
            True to continue, False to quit
        """
        if context is None:
            context = {}
        
        while True:
            selected_key = self.show()
            
            if selected_key is None:
                print(f"{Colors.YELLOW}无效选择，请重试{Colors.RESET}")
                continue
            
            if selected_key == 'quit':
                return False
            
            if selected_key == 'back':
                return True
            
            # Find selected option
            selected_option = None
            for opt in self.options:
                if opt.key == selected_key:
                    selected_option = opt
                    break
            
            if selected_option is None:
                print(f"{Colors.YELLOW}无效选择，请重试{Colors.RESET}")
                continue
            
            # Execute action or show submenu
            if selected_option.submenu:
                should_continue = selected_option.submenu.run(context)
                if not should_continue:
                    return False
            elif selected_option.action:
                try:
                    selected_option.action(context)
                except KeyboardInterrupt:
                    print(f"\n{Colors.YELLOW}操作已取消{Colors.RESET}")
                except Exception as e:
                    print(f"\n{Colors.RED}错误: {str(e)}{Colors.RESET}")
                    import traceback
                    traceback.print_exc()
                    input(f"\n{Colors.DIM}按 Enter 继续...{Colors.RESET}")


class ConfirmDialog:
    """Confirmation dialog"""
    
    @staticmethod
    def show(title: str, text: str) -> bool:
        """
        Show confirmation dialog
        
        Args:
            title: Dialog title
            text: Dialog text
            
        Returns:
            True if confirmed, False otherwise
        """
        if PROMPT_TOOLKIT_AVAILABLE:
            try:
                result = button_dialog(
                    title=title,
                    text=text,
                    buttons=[
                        ('yes', '是'),
                        ('no', '否'),
                    ],
                ).run()
                return result == 'yes'
            except Exception:
                pass
        
        # Fallback
        print(f"\n{Colors.YELLOW}{title}{Colors.RESET}")
        print(f"{text}\n")
        choice = input(f"{Colors.GREEN}确认? (y/n): {Colors.RESET}").strip().lower()
        return choice in ['y', 'yes', '是']


class MessageDialog:
    """Message dialog"""
    
    @staticmethod
    def show(title: str, text: str):
        """
        Show message dialog
        
        Args:
            title: Dialog title
            text: Dialog text
        """
        if PROMPT_TOOLKIT_AVAILABLE:
            try:
                button_dialog(
                    title=title,
                    text=text,
                    buttons=[
                        ('ok', '确定'),
                    ],
                ).run()
                return
            except Exception:
                pass
        
        # Fallback
        print(f"\n{Colors.BLUE}{title}{Colors.RESET}")
        print(f"{text}\n")
        input(f"{Colors.DIM}按 Enter 继续...{Colors.RESET}")


def create_simple_menu(title: str, options: List[Tuple[str, str]], 
                      show_back: bool = False, show_quit: bool = True) -> InteractiveMenu:
    """
    Create a simple interactive menu
    
    Args:
        title: Menu title
        options: List of (key, label) tuples
        show_back: Show "Back" option
        show_quit: Show "Quit" option
        
    Returns:
        InteractiveMenu instance
    """
    menu_options = [
        MenuOption(key=key, label=label)
        for key, label in options
    ]
    
    return InteractiveMenu(
        title=title,
        options=menu_options,
        show_back=show_back,
        show_quit=show_quit
    )


# Check if prompt_toolkit is available
def check_interactive_support() -> bool:
    """Check if interactive features are available"""
    return PROMPT_TOOLKIT_AVAILABLE


def print_interactive_status():
    """Print interactive feature status"""
    if PROMPT_TOOLKIT_AVAILABLE:
        print(f"{Colors.GREEN}✅ 交互式导航已启用 (使用箭头键){Colors.RESET}")
    else:
        print(f"{Colors.YELLOW}⚠️  交互式导航不可用 (使用数字选择){Colors.RESET}")
        print(f"{Colors.DIM}   提示: 运行 'pip install prompt_toolkit' 启用箭头键导航{Colors.RESET}")
