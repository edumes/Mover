from pathlib import Path
from typing import Optional, Dict
from textual import on, work
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Input, Label, Static, Tree
from textual.widgets.tree import TreeNode
from textual.screen import ModalScreen
from .utils import format_size

class PathSelector(Container):
    def __init__(self, title: str, id: str) -> None:
        super().__init__(id=id)
        self.title = title
        self.path: Optional[Path] = None
    def compose(self):
        yield Label(self.title, classes="path-title")
        yield Input("", placeholder="Enter path...", id="path-input")
        # yield Button("Browse", id="browse-button", variant="primary")
    def update_tree(self, path: Path) -> None:
        self.path = path
        self.query_one(Input).value = str(path)

class CustomDirectoryTree(Tree):
    def __init__(self, path: str, id: str) -> None:
        super().__init__(label=Path(path).name if path else "No Path", id=id)
        self.path = Path(path) if path else None
        self.sizes: Dict[Path, int] = {}
        self.loading = False
        self.cancel_loading = False
    def on_mount(self) -> None:
        if self.path and self.path.is_dir():
            self.root.data = self.path
            self.root.label = f"📁 {self.path.name}"
            self.load_directory(self.root, self.path)
    def load_directory(self, node: TreeNode, path: Path) -> None:
        if self.loading or self.cancel_loading:
            return
        self.loading = True
        self.cancel_loading = False
        try:
            if node.children and node.children[0].label == "...":
                node.children.clear()
            try:
                dir_entries = list(path.iterdir())
            except Exception as e:
                node.add_leaf(f"⚠️ Error: {str(e)}", None)
                return
            dir_entries.sort(key=lambda e: (not e.is_dir(), e.name.lower()))
            for entry in dir_entries:
                if self.cancel_loading:
                    break
                entry_path = Path(entry)
                if entry.is_dir():
                    child = node.add(f"📁 {entry.name}", data=entry_path, allow_expand=True)
                    child.add_leaf("...", None)
                else:
                    try:
                        size = entry.stat().st_size
                        self.sizes[entry_path] = size
                        node.add_leaf(f"📄 {entry.name} ({format_size(size)})", entry_path)
                    except:
                        node.add_leaf(f"📄 {entry.name} [Error]", None)
            if not self.cancel_loading:
                self.calculate_folder_size(path)
        finally:
            self.loading = False
    @work(thread=True)
    def calculate_folder_size(self, path: Path) -> None:
        if self.cancel_loading:
            return
        total_size = 0
        try:
            for entry in path.iterdir():
                if self.cancel_loading:
                    return
                if entry.is_file():
                    total_size += entry.stat().st_size
                elif entry.is_dir():
                    try:
                        for sub_entry in entry.iterdir():
                            if sub_entry.is_file():
                                total_size += sub_entry.stat().st_size
                    except:
                        pass
        except:
            return
        self.sizes[path] = total_size
        if not self.cancel_loading:
            self.call_from_thread(self.update_folder_label, path, total_size)
    def update_folder_label(self, path: Path, size: int) -> None:
        if self.cancel_loading:
            return
        for node_id, node in self.nodes.items():
            if hasattr(node, 'data') and node.data == path:
                node.label = f"📁 {path.name} ({format_size(size)})"
                break
        self.refresh()
    def on_tree_node_expanded(self, event: Tree.NodeExpanded) -> None:
        if (event.node.children and len(event.node.children) == 1 and event.node.children[0].label == "..."):
            self.load_directory(event.node, event.node.data)
    def reset(self) -> None:
        self.clear()
        self.cancel_loading = True
        self.loading = False
        self.path = None
        self.root.expand()

class ConfirmationScreen(ModalScreen):
    def __init__(self, source: Path, target: Path, message: Optional[str] = None) -> None:
        super().__init__()
        self.source = source
        self.target = target
        self.message = message or f"Confirm move all content from:\n{source}\n\nTo:\n{target}?"
    def compose(self):
        with Container(id="confirmation-dialog"):
            yield Label(self.message, classes="confirmation-message")
            with Horizontal(classes="dialog-buttons"):
                yield Button("Cancel", id="cancel-button", variant="error")
                yield Button("Confirm", id="confirm-button", variant="success")
    @on(Button.Pressed, "#cancel-button")
    def cancel_action(self) -> None:
        self.dismiss(False)
    @on(Button.Pressed, "#confirm-button")
    def confirm_action(self) -> None:
        self.dismiss(True) 