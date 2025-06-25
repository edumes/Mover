from pathlib import Path
from typing import Optional
from textual import on, work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.reactive import reactive
from textual.widgets import Button, Footer, Header, Input, Static
from .widgets import PathSelector, CustomDirectoryTree, ConfirmationScreen
from .logic import move_content

class FileMoverApp(App):
    CSS_PATH = "styles.css"
    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit"),
        Binding("f1", "toggle_dark", "Toggle theme"),
        Binding("f2", "swap_paths", "Swap paths"),
    ]
    source_path: Optional[Path] = None
    target_path: Optional[Path] = None
    status_message = reactive("Ready")
    progress_percentage = reactive(0.0)
    moving = False

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Container(id="main-container"):
            with Horizontal():
                with Vertical(classes="panel"):
                    yield PathSelector("Source Directory:", id="source-selector")
                    yield CustomDirectoryTree("", id="source-tree")
                with Vertical(classes="panel"):
                    yield PathSelector("Target Directory:", id="target-selector")
                    yield CustomDirectoryTree("", id="target-tree")
            yield Static("", id="status-bar")
            with Horizontal(id="action-buttons"):
                yield Button("Move Content", id="move-button", variant="primary")
                yield Button("Clear", id="clear-button")
        yield Footer()

    def on_mount(self) -> None:
        self.title = "Mover"
        self.sub_title = "Select source and target paths"

    def update_status(self, message: str, is_error: bool = False) -> None:
        self.status_message = message
        status_bar = self.query_one("#status-bar", Static)
        status_bar.update(message)
        status_bar.set_class(is_error, "error")
        status_bar.set_class(self.moving, "processing")

    def update_progress(self, percentage: float, moved: int = 0, total: int = 0) -> None:
        self.progress_percentage = percentage
        if total > 0 and moved < total:
            self.update_status(f"Moving {moved} of {total} files...", is_error=False)
        elif moved == total and total > 0:
            self.update_status(f"Movido {moved}/{total} arquivos!", is_error=False)

    @on(Input.Changed, "#source-selector #path-input")
    def handle_source_input_changed(self, event: Input.Changed) -> None:
        if event.value:
            try:
                new_path = Path(event.value)
                if new_path.is_dir():
                    self.source_path = new_path
                    tree = self.query_one("#source-tree", CustomDirectoryTree)
                    tree.path = new_path
                    tree.reset()
                    tree.root.data = new_path
                    tree.root.label = f"📁 {new_path.name}"
                    tree.load_directory(tree.root, new_path)
                    self.update_status("Source path updated")
                else:
                    self.update_status("Invalid source directory", is_error=True)
            except Exception as e:
                self.update_status(f"Error: {str(e)}", is_error=True)

    @on(Input.Changed, "#target-selector #path-input")
    def handle_target_input_changed(self, event: Input.Changed) -> None:
        if event.value:
            try:
                new_path = Path(event.value)
                if new_path.is_dir():
                    self.target_path = new_path
                    tree = self.query_one("#target-tree", CustomDirectoryTree)
                    tree.path = new_path
                    tree.reset()
                    tree.root.data = new_path
                    tree.root.label = f"📁 {new_path.name}"
                    tree.load_directory(tree.root, new_path)
                    self.update_status("Target path updated")
                else:
                    self.update_status("Invalid target directory", is_error=True)
            except Exception as e:
                self.update_status(f"Error: {str(e)}", is_error=True)

    # @on(Button.Pressed, "#source-selector #browse-button")
    # def handle_source_browse(self) -> None:
    #     tree = self.query_one("#source-tree", CustomDirectoryTree)
    #     if tree.cursor_node and tree.cursor_node.data:
    #         self.source_path = tree.cursor_node.data
    #         self.query_one("#source-selector", PathSelector).update_tree(self.source_path)
    #         self.update_status("Source selected")

    # @on(Button.Pressed, "#target-selector #browse-button")
    # def handle_target_browse(self) -> None:
    #     tree = self.query_one("#target-tree", CustomDirectoryTree)
    #     if tree.cursor_node and tree.cursor_node.data:
    #         self.target_path = tree.cursor_node.data
    #         self.query_one("#target-selector", PathSelector).update_tree(self.target_path)
    #         self.update_status("Target selected")

    @on(Button.Pressed, "#clear-button")
    def clear_inputs(self) -> None:
        self.source_path = None
        self.target_path = None
        self.query_one("#source-selector", PathSelector).query_one(Input).value = ""
        self.query_one("#target-selector", PathSelector).query_one(Input).value = ""
        source_tree = self.query_one("#source-tree", CustomDirectoryTree)
        source_tree.reset()
        target_tree = self.query_one("#target-tree", CustomDirectoryTree)
        target_tree.reset()
        self.update_progress(0.0)
        self.update_status("Selections cleared")

    @on(Button.Pressed, "#exit-button")
    def exit_app(self) -> None:
        self.action_quit()

    @on(Button.Pressed, "#move-button")
    def initiate_move(self) -> None:
        if self.moving:
            self.update_status("Another operation is in progress", is_error=True)
            return
        if not self.source_path:
            self.update_status("Error: No source directory selected", is_error=True)
            return
        if not self.target_path:
            self.update_status("Error: No target directory selected", is_error=True)
            return
        if self.source_path == self.target_path:
            self.update_status("Error: Source and target are the same", is_error=True)
            return
        if not self.source_path.is_dir():
            self.update_status("Error: Source is not a directory", is_error=True)
            return
        if not self.target_path.is_dir():
            self.app.push_screen(
                ConfirmationScreen(
                    self.source_path,
                    self.target_path,
                    f"Target directory doesn't exist:\n{self.target_path}\n\nCreate it?"
                ),
                self.create_target_directory
            )
            return
        if not self.source_path.exists() or not self.source_path.is_dir():
            self.update_status("Error: Source directory does not exist", is_error=True)
            return
        if not self.target_path.exists():
            self.update_status("Error: Target directory does not exist", is_error=True)
            return
        self.app.push_screen(
            ConfirmationScreen(self.source_path, self.target_path),
            self.process_move_confirmation,
        )

    async def create_target_directory(self, confirm: bool) -> None:
        if not confirm:
            self.update_status("Operation canceled")
            return
        try:
            self.target_path.mkdir(parents=True, exist_ok=True)
            tree = self.query_one("#target-tree", CustomDirectoryTree)
            tree.path = self.target_path
            tree.reset()
            tree.root.data = self.target_path
            tree.root.label = f"📁 {self.target_path.name}"
            tree.load_directory(tree.root, self.target_path)
            self.update_status(f"Created target directory: {self.target_path}")
            self.app.push_screen(
                ConfirmationScreen(self.source_path, self.target_path),
                self.process_move_confirmation,
            )
        except Exception as e:
            self.update_status(f"Error creating directory: {str(e)}", is_error=True)

    async def process_move_confirmation(self, confirm: bool) -> None:
        if not confirm:
            self.update_status("Operation canceled")
            return
        self.move_content_threaded()

    @work(thread=True)
    def move_content_threaded(self) -> None:
        try:
            self.moving = True
            self.call_from_thread(self.update_progress, 0.0, 0, 0)
            def progress_callback(progress, moved, total):
                self.call_from_thread(self.update_progress, progress, moved, total)
            def status_callback(message, is_error):
                self.call_from_thread(self.update_status, message, is_error)
            move_content(self.source_path, self.target_path, progress_callback, status_callback)
        except Exception as e:
            self.call_from_thread(self.update_status, f"Error: {str(e)}", True)
        finally:
            self.moving = False
            self.call_from_thread(self.update_progress, 0.0, 0, 0)
            self.call_from_thread(self.refresh_trees)

    def refresh_trees(self) -> None:
        source_tree = self.query_one("#source-tree", CustomDirectoryTree)
        source_tree.reset()
        if self.source_path and self.source_path.is_dir():
            source_tree.path = self.source_path
            source_tree.root.data = self.source_path
            source_tree.root.label = f"📁 {self.source_path.name}"
            source_tree.load_directory(source_tree.root, self.source_path)
        target_tree = self.query_one("#target-tree", CustomDirectoryTree)
        target_tree.reset()
        if self.target_path and self.target_path.is_dir():
            target_tree.path = self.target_path
            target_tree.root.data = self.target_path
            target_tree.root.label = f"📁 {self.target_path.name}"
            target_tree.load_directory(target_tree.root, self.target_path)

    def action_swap_paths(self) -> None:
        if self.source_path and self.target_path:
            self.source_path, self.target_path = self.target_path, self.source_path
            self.query_one("#source-selector", PathSelector).update_tree(self.source_path)
            self.query_one("#target-selector", PathSelector).update_tree(self.target_path)
            source_tree = self.query_one("#source-tree", CustomDirectoryTree)
            source_tree.reset()
            if self.source_path and self.source_path.is_dir():
                source_tree.path = self.source_path
                source_tree.root.data = self.source_path
                source_tree.root.label = f"📁 {self.source_path.name}"
                source_tree.load_directory(source_tree.root, self.source_path)
            target_tree = self.query_one("#target-tree", CustomDirectoryTree)
            target_tree.reset()
            if self.target_path and self.target_path.is_dir():
                target_tree.path = self.target_path
                target_tree.root.data = self.target_path
                target_tree.root.label = f"📁 {self.target_path.name}"
                target_tree.load_directory(target_tree.root, self.target_path)
            self.update_status("Source and target swapped")
        else:
            self.update_status("Both paths must be set to swap", is_error=True)

    def action_toggle_dark(self) -> None:
        self.dark = not self.dark

    def on_unmount(self) -> None:
        try:
            source_tree = self.query_one("#source-tree", CustomDirectoryTree)
            if source_tree:
                source_tree.cancel_loading = True
        except:
            pass
        try:
            target_tree = self.query_one("#target-tree", CustomDirectoryTree)
            if target_tree:
                target_tree.cancel_loading = True
        except:
            pass
        self.moving = False 