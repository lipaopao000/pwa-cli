"""
Rich console output enhancements for PWA CLI.
"""

from typing import Any, Dict, List, Optional

from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskID,
    TextColumn,
    TimeElapsedColumn,
)
from rich.table import Table
from rich.tree import Tree

# Global console instance
console = Console()


def print_success(message: str) -> None:
    """Print a success message."""
    console.print(f"[bold green]✓[/bold green] {message}")


def print_error(message: str) -> None:
    """Print an error message."""
    console.print(f"[bold red]✗[/bold red] {message}")


def print_warning(message: str) -> None:
    """Print a warning message."""
    console.print(f"[bold yellow]⚠[/bold yellow] {message}")


def print_info(message: str) -> None:
    """Print an info message."""
    console.print(f"[bold cyan]ℹ[/bold cyan] {message}")


def print_header(title: str, subtitle: Optional[str] = None) -> None:
    """Print a formatted header."""
    if subtitle:
        console.print(Panel(f"[bold]{title}[/bold]\n[dim]{subtitle}[/dim]", border_style="blue"))
    else:
        console.print(Panel(f"[bold]{title}[/bold]", border_style="blue"))


def print_section(title: str) -> None:
    """Print a section divider."""
    console.print(f"\n[bold blue]{'─' * 10} {title} {'─' * 10}[/bold blue]")


def print_table(
    title: str,
    columns: List[str],
    rows: List[List[Any]],
    show_header: bool = True,
    show_lines: bool = False,
) -> None:
    """
    Print a formatted table.

    Args:
        title: Table title
        columns: List of column names
        rows: List of row data
        show_header: Whether to show column headers
        show_lines: Whether to show row lines
    """
    table = Table(title=title, show_header=show_header, show_lines=show_lines)

    # Add columns
    for col in columns:
        table.add_column(col, style="cyan")

    # Add rows
    for row in rows:
        table.add_row(*[str(cell) for cell in row])

    console.print(table)


def print_dict(data: Dict[str, Any], title: Optional[str] = None) -> None:
    """
    Print a dictionary as a formatted table.

    Args:
        data: Dictionary to print
        title: Optional table title
    """
    table = Table(title=title, show_header=True)
    table.add_column("Key", style="cyan")
    table.add_column("Value", style="green")

    for key, value in data.items():
        table.add_row(str(key), str(value))

    console.print(table)


def print_tree(title: str, data: Dict[str, Any]) -> None:
    """
    Print a dictionary as a tree structure.

    Args:
        title: Tree root title
        data: Dictionary to display as tree
    """
    tree = Tree(f"[bold]{title}[/bold]")

    def add_node(parent: Tree, items: Dict[str, Any]) -> None:
        for key, value in items.items():
            if isinstance(value, dict):
                branch = parent.add(f"[cyan]{key}[/cyan]")
                add_node(branch, value)
            elif isinstance(value, list):
                branch = parent.add(f"[cyan]{key}[/cyan]")
                for item in value:
                    if isinstance(item, dict):
                        add_node(branch, item)
                    else:
                        branch.add(f"[green]{item}[/green]")
            else:
                parent.add(f"[cyan]{key}[/cyan]: [green]{value}[/green]")

    add_node(tree, data)
    console.print(tree)


def create_progress() -> Progress:
    """
    Create a progress bar with spinner.

    Returns:
        Progress instance
    """
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console,
    )


def print_status(message: str, status: str = "working") -> None:
    """
    Print a status message with spinner.

    Args:
        message: Status message
        status: Status type (working, done, failed)
    """
    if status == "working":
        console.print(f"[bold yellow]⟳[/bold yellow] {message}")
    elif status == "done":
        console.print(f"[bold green]✓[/bold green] {message}")
    elif status == "failed":
        console.print(f"[bold red]✗[/bold red] {message}")


def print_list(items: List[str], title: Optional[str] = None, numbered: bool = False) -> None:
    """
    Print a formatted list.

    Args:
        items: List of items to print
        title: Optional list title
        numbered: Whether to number the items
    """
    if title:
        console.print(f"\n[bold]{title}[/bold]")

    for i, item in enumerate(items, 1):
        if numbered:
            console.print(f"  [cyan]{i}.[/cyan] {item}")
        else:
            console.print(f"  [cyan]•[/cyan] {item}")


def print_panel(content: str, title: Optional[str] = None, style: str = "blue") -> None:
    """
    Print content in a panel.

    Args:
        content: Content to display
        title: Optional panel title
        style: Border style color
    """
    console.print(Panel(content, title=title, border_style=style))


def print_rule(title: Optional[str] = None, style: str = "blue") -> None:
    """
    Print a horizontal rule.

    Args:
        title: Optional title for the rule
        style: Rule style color
    """
    console.rule(title, style=style)


def confirm(message: str, default: bool = False) -> bool:
    """
    Ask for user confirmation.

    Args:
        message: Confirmation message
        default: Default value if user just presses Enter

    Returns:
        True if confirmed, False otherwise
    """
    default_str = "Y/n" if default else "y/N"
    response = console.input(f"{message} [{default_str}]: ").strip().lower()

    if not response:
        return default

    return response in ("y", "yes")
