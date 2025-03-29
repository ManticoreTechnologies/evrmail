import typer
from datetime import datetime
from evrmail.utils.inbox import load_all_messages, delete_message_by_path
from rich.console import Console
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static
from textual.containers import VerticalScroll
from textual.reactive import reactive
from textual.screen import ModalScreen
from textual import events
from rich.text import Text

inbox_app = typer.Typer()
console = Console()

def parse_date(ts):
    if isinstance(ts, int):
        return datetime.fromtimestamp(ts)
    try:
        return datetime.strptime(ts, "%Y-%m-%dT%H:%M:%S.%fZ")
    except Exception:
        return datetime.fromtimestamp(0)  # fallback

class InboxItem(Static):
    def __init__(self, msg, index: int):
        super().__init__()
        self.msg = msg
        self.index = index
        self.selected = reactive(False)

    def render(self) -> Text:
        status = "[bold green]\u2713[/]" if self.msg.get("read") else "[bold red]\u2022[/]"
        content = self.msg.get("content", {})
        subj = content.get("subject", "(No Subject)")
        from_ = self.msg.get("from", "Unknown")
        to_ = self.msg.get("to", "Unknown")
        ts = self.msg.get("timestamp") or self.msg.get("received_at", "")
        date = parse_date(ts).strftime("%Y-%m-%d %H:%M")

        line = f"{status} [cyan]{from_}[/] → [magenta]{to_}[/] — [white]{subj}[/] [dim]({date})[/]"
        return Text.from_markup(line, style="on #444" if self.selected else "")


def reload_inbox(app):
    app.inbox = load_all_messages()
    app.items = [InboxItem(msg, i) for i, msg in enumerate(app.inbox)]
    app.selected_index = min(app.selected_index, len(app.items) - 1) if app.items else 0
    container = app.query_one("#inbox")
    container.remove_children()
    for item in app.items:
        container.mount(item)
    app.update_selection()

@inbox_app.command("list")
def inbox():
    """Read your inbox."""
    inbox = load_all_messages()
    for message in inbox:
        console.log(message)

@inbox_app.command("unread")
def unread():
    """List all unread messages."""
    inbox = load_all_messages()
    for message in inbox:
        if not message.get("read"):
            console.rule("Unread Message")
            console.print(f"From: {message.get('from')}")
            console.print(f"To: {message.get('to')}")
            console.print(f"Subject: {message.get('subject')}")
            console.print(f"Date: {parse_date(message['timestamp']).strftime('%Y-%m-%d %H:%M:%S')}")
            console.print(f"Body: {message.get('content', '')}")
            console.rule()

@inbox_app.command("open")
def interactive():
    """Open an interactive inbox viewer."""

    class MessageModal(ModalScreen):
        def __init__(self, msg):
            super().__init__()
            self.msg = msg

        def compose(self) -> ComposeResult:
            from_ = self.msg.get("from", "Unknown")
            to_ = self.msg.get("to", "Unknown")
            subject = self.msg.get("content", {}).get("subject", "(No Subject)")
            date = parse_date(self.msg.get("timestamp", "")) \
                .strftime("%Y-%m-%d %H:%M:%S")

            content = self.msg.get("content", {})
            body_text = content.get("content", "(No content)")

            body = Text.from_markup(
                f"[bold]From:[/bold] {from_}\n"
                f"[bold]To:[/bold] {to_}\n"
                f"[bold]Subject:[/bold] {subject}\n"
                f"[bold]Date:[/bold] {date}\n\n"
                f"{body_text}",
                style="white on black"
            )

            yield Static(body, expand=True)

        def on_key(self, event: events.Key) -> None:
            if event.key in ("escape", "enter"):
                self.app.pop_screen()


    class InboxApp(App):
        CSS_PATH = None
        BINDINGS = [
            ("q", "quit", "Quit"),
            ("up", "cursor_up", "Up"),
            ("down", "cursor_down", "Down"),
            ("enter", "open_msg", "Open"),
            ("d", "delete_msg", "Delete"),
        ]

        selected_index = reactive(0)

        def compose(self) -> ComposeResult:
            self.inbox = load_all_messages()
            yield Header()
            with VerticalScroll(id="inbox") as self.scroll:
                self.items = [InboxItem(msg, i) for i, msg in enumerate(self.inbox)]
                for item in self.items:
                    yield item
            yield Footer()

        def on_mount(self):
            self.update_selection()

        def update_selection(self):
            for i, item in enumerate(self.items):
                item.selected = (i == self.selected_index)
                item.refresh()

        def action_cursor_up(self):
            if self.selected_index > 0:
                self.selected_index -= 1
                self.update_selection()

        def action_cursor_down(self):
            if self.selected_index < len(self.items) - 1:
                self.selected_index += 1
                self.update_selection()

        def action_open_msg(self):
            msg = self.inbox[self.selected_index]
            self.push_screen(MessageModal(msg))

        def action_delete_msg(self):
            msg = self.inbox[self.selected_index]
            delete_message_by_path(msg.get("__path"))
            reload_inbox(self)

    InboxApp().run()
