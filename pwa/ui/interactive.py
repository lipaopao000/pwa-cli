"""
Interactive menu with arrow key navigation and number shortcuts using InquirerPy
"""

import sys
from typing import List, Optional, Tuple, Callable, Dict
from dataclasses import dataclass

try:
    from InquirerPy import inquirer
    from InquirerPy.base.control import Choice
    from InquirerPy.separator import Separator
    from prompt_toolkit.keys import Keys
    from prompt_toolkit.key_binding import KeyBindings
    INQUIRER_AVAILABLE = True
except ImportError:
    INQUIRER_AVAILABLE = False

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
    """Interactive menu with arrow key navigation and number shortcuts using InquirerPy"""
    
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
        self._number_to_key = {}  # Map number to option key
    
    def show(self) -> Optional[str]:
        """
        Show menu and return selected option key
        
        Returns:
            Selected option key or None
        """
        if INQUIRER_AVAILABLE:
            return self._show_with_inquirer()
        else:
            return self._show_fallback()
    
    def _build_number_mapping(self, choices: List) -> Dict[str, str]:
        """Build mapping from number keys to option keys"""
        mapping = {}
        for i, choice in enumerate(choices, 1):
            if hasattr(choice, 'value') and choice.value:
                mapping[str(i)] = choice.value
        return mapping
    
    def _show_with_inquirer(self) -> Optional[str]:
        """Show menu using InquirerPy with number shortcuts"""
        try:
            # Build choices
            choices = []
            
            # Add menu options
            for i, opt in enumerate(self.options, 1):
                name = f"{i}. {opt.label}"
                if opt.description:
                    name += f" - {opt.description}"
                choices.append(Choice(value=opt.key, name=name))
            
            # Add separator before back/quit
            if self.show_back or self.show_quit:
                choices.append(Separator())
            
            # Add back option
            if self.show_back:
                # Use '0' as shortcut for Back if it's a submenu
                choices.append(Choice(value='back', name='0. 返回上级菜单'))
            
            # Add quit option
            if self.show_quit:
                # Use '0' as shortcut for Quit if it's the main menu (no back option)
                if not self.show_back:
                    choices.append(Choice(value='quit', name='0. 退出'))
                else:
                    quit_num = len(self.options) + 2
                    choices.append(Choice(value='quit', name=f'{quit_num}. 退出'))
            
            # Build number to key mapping
            self._number_to_key = {}
            # Map menu options (1-9)
            for i, opt in enumerate(self.options, 1):
                self._number_to_key[str(i)] = opt.key
            
            # Map 0 to Back or Quit
            if self.show_back:
                self._number_to_key['0'] = 'back'
            elif self.show_quit:
                self._number_to_key['0'] = 'quit'
            
            # Create prompt instance
            prompt = inquirer.select(
                message=self.title,
                choices=choices,
                default=choices[0].value if choices else None,
                pointer="❯",
                instruction="(使用 ↑↓ 箭头键或输入数字选择，Enter 确认)",
            )
            
            # Register number key bindings
            for num in '1234567890':
                if num in self._number_to_key:
                    def make_handler(n):
                        @prompt.register_kb(n)
                        def _(event):
                            # Find the choice with the corresponding value
                            for i, choice in enumerate(prompt.content_control.choices):
                                # InquirerPy choices are stored as dicts internally
                                choice_value = choice.get('value') if isinstance(choice, dict) else getattr(choice, 'value', None)
                                if choice_value == self._number_to_key[n]:
                                    prompt.content_control.selected_choice_index = i
                                    prompt._handle_enter(event)
                                    break
                    make_handler(num)
            
            # Run the prompt
            result = prompt.execute()
            return result
            
        except KeyboardInterrupt:
            return 'quit'
        except Exception as e:
            # If InquirerPy fails, fall back to traditional menu
            print(f"{Colors.YELLOW}⚠️  交互式菜单出错，切换到传统模式{Colors.RESET}")
            print(f"{Colors.DIM}错误: {str(e)}{Colors.RESET}\n")
            return self._show_fallback()
    
    def _show_fallback(self) -> Optional[str]:
        """Fallback menu without arrow key support"""
        print(f"\n{Colors.BLUE}{'=' * 60}{Colors.RESET}")
        print(f"{Colors.BOLD}{self.title}{Colors.RESET}")
        print(f"{Colors.BLUE}{'=' * 60}{Colors.RESET}\n")
        
        # Build option list
        option_list = []
        for i, opt in enumerate(self.options, 1):
            display = f"{i}. {opt.label}"
            if opt.description:
                display += f" - {opt.description}"
            option_list.append((opt.key, display))
            print(f"  {display}")
        
        # Add separator
        if self.show_back or self.show_quit:
            print()
        
        # Add back option
        if self.show_back:
            back_num = 0
            back_display = f"{back_num}. 返回上级菜单"
            option_list.append(('back', back_display))
            print(f"  {back_display}")
        
        # Add quit option
        if self.show_quit:
            if not self.show_back:
                quit_num = 0
            else:
                quit_num = len(self.options) + 2
            quit_display = f"{quit_num}. 退出"
            option_list.append(('quit', quit_display))
            print(f"  {quit_display}")
        
        print()
        choice = input(f"{Colors.GREEN}请选择: {Colors.RESET}").strip()
        
        # Support both number and key input
        if choice.isdigit():
            # Special handling for fallback 0
            if choice == '0':
                if self.show_back:
                    return 'back'
                elif self.show_quit:
                    return 'quit'
            
            idx = int(choice) - 1
            if 0 <= idx < len(self.options):
                return self.options[idx].key
            
            # Handle non-0 quit
            if self.show_quit and self.show_back:
                if int(choice) == len(self.options) + 2:
                    return 'quit'
        else:
            # Try to match by key
            for key, _ in option_list:
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
        if INQUIRER_AVAILABLE:
            try:
                print(f"\n{Colors.YELLOW}{title}{Colors.RESET}")
                print(f"{text}\n")
                
                result = inquirer.confirm(
                    message="确认?",
                    default=False,
                ).execute()
                
                return result
            except KeyboardInterrupt:
                return False
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


# Check if InquirerPy is available
def check_interactive_support() -> bool:
    """Check if interactive features are available"""
    return INQUIRER_AVAILABLE


def print_interactive_status():
    """Print interactive feature status"""
    if INQUIRER_AVAILABLE:
        print(f"{Colors.GREEN}✅ 交互式导航已启用 (InquirerPy){Colors.RESET}")
        print(f"{Colors.DIM}   提示: 使用 ↑↓ 箭头键或输入数字选择，Enter 确认{Colors.RESET}")
    else:
        print(f"{Colors.YELLOW}⚠️  交互式导航不可用 (使用数字选择){Colors.RESET}")
        print(f"{Colors.DIM}   提示: 运行 'pip install InquirerPy' 启用箭头键导航{Colors.RESET}")
