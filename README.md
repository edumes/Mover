# Mover

Mover is a TUI (Textual User Interface) application written in Python using [Textual](https://www.textualize.io/) that lets you move the contents of one directory to another in a visual, fast, and safe way, especially when dealing with folders containing thousands of files, a scenario where Windows Explorer often falters or crashes. It displays a real-time progress and status messages to keep you informed throughout the entire operation.

![{A93EFFE0-D869-4D9A-B4FB-6FC91E5BFA88}](https://github.com/user-attachments/assets/9ed65c86-042d-4136-be18-5e7cceaa1522)

## Features

* Visual selection of source and destination directories
* Tree view of directories
* Visual progress bar during the move
* Confirmation before destructive operations
* Light/dark theme support
* Responsive, modern interface

## Installation

1. **Clone the repository:**

   ```bash
   git clone <repository-url>
   cd Mover
   ```
2. **Create a virtual environment** (optional but recommended):

   ```bash
   python -m venv .venv
   source .venv/bin/activate   # Linux/macOS
   .venv\Scripts\activate      # Windows
   ```
3. **Install the dependencies:**

   ```bash
   pip install textual
   ```

## Usage

1. Run the application:

   ```bash
   python main.py
   ```
2. Use the fields to select the source and destination directories.
3. Navigate the directory trees to make your selection easier.
4. Click **Move Content** to start moving the files.
5. Follow the progress via the progress bar and status messages.

## Shortcuts

* `Ctrl+Q`: Quit
* `F1`: Toggle light/dark theme
* `F2`: Swap source and destination

## Dependencies

* [Textual](https://github.com/Textualize/textual)
* Python 3.8+

---
