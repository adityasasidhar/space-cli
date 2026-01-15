import os
import subprocess
import re
import shutil
from pathlib import Path


def list_files(path: str = ".") -> str:
    """List files in a directory."""
    try:
        files = os.listdir(path)
        return "\n".join(files)
    except Exception as e:
        return f"Error listing files: {e}"


def read_file(path: str) -> str:
    """Read the content of a file."""
    try:
        with open(path, "r") as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {e}"


def write_file(path: str, content: str) -> str:
    """
    Write content to a file, creating parent directories if needed.
    
    Args:
        path: Path to the file
        content: Content to write
    """
    try:
        # Create parent directories if they don't exist
        parent_dir = os.path.dirname(path)
        if parent_dir and not os.path.exists(parent_dir):
            os.makedirs(parent_dir, exist_ok=True)
        
        with open(path, "w") as f:
            f.write(content)
        return f"Successfully wrote to {path}"
    except PermissionError:
        return f"Error: Permission denied writing to {path}"
    except Exception as e:
        return f"Error writing file: {e}"


# Backup directory for undo support
BACKUP_DIR = os.path.expanduser("~/.space/backups")
os.makedirs(BACKUP_DIR, exist_ok=True)


def diff_preview(path: str, old_text: str, new_text: str) -> str:
    """
    Preview changes before applying them (unified diff format).
    
    Args:
        path: Path to the file
        old_text: Text to find
        new_text: Replacement text
    """
    import difflib
    
    try:
        if not os.path.exists(path):
            return f"Error: File '{path}' does not exist"
        
        with open(path, "r") as f:
            content = f.read()
        
        if old_text not in content:
            return f"Error: old_text not found in file"
        
        new_content = content.replace(old_text, new_text)
        
        diff = difflib.unified_diff(
            content.splitlines(keepends=True),
            new_content.splitlines(keepends=True),
            fromfile=f"a/{path}",
            tofile=f"b/{path}"
        )
        
        diff_text = "".join(diff)
        if not diff_text:
            return "No changes detected"
        
        return f"Preview of changes:\n{diff_text}"
    except Exception as e:
        return f"Error generating diff: {e}"


def edit_file(path: str, old_text: str, new_text: str) -> str:
    """
    Replace old_text with new_text in a file.
    Creates a backup for undo support.
    
    Args:
        path: Path to the file to edit
        old_text: Text to find and replace
        new_text: Replacement text
    """
    import time
    
    try:
        # Check if file exists
        if not os.path.exists(path):
            return f"Error: File '{path}' does not exist"
        
        # Check if file is readable
        if not os.access(path, os.R_OK):
            return f"Error: No read permission for '{path}'"
        
        with open(path, "r") as f:
            content = f.read()

        if old_text not in content:
            return f"Error: old_text not found in file. Make sure the text matches exactly."

        # Create backup before editing
        backup_name = f"{os.path.basename(path)}.{int(time.time())}.bak"
        backup_path = os.path.join(BACKUP_DIR, backup_name)
        with open(backup_path, "w") as f:
            f.write(content)
        
        # Store mapping for undo
        mapping_file = os.path.join(BACKUP_DIR, "undo_mapping.json")
        import json
        try:
            with open(mapping_file, "r") as f:
                mappings = json.load(f)
        except:
            mappings = {}
        
        mappings[os.path.abspath(path)] = backup_path
        with open(mapping_file, "w") as f:
            json.dump(mappings, f)

        new_content = content.replace(old_text, new_text)

        with open(path, "w") as f:
            f.write(new_content)

        return f"Successfully edited {path} (backup: {backup_name})"
    except PermissionError:
        return f"Error: Permission denied editing '{path}'"
    except Exception as e:
        return f"Error editing file: {e}"


def undo_edit(path: str) -> str:
    """
    Undo the last edit to a file by restoring from backup.
    
    Args:
        path: Path to the file to undo
    """
    import json
    
    try:
        abs_path = os.path.abspath(path)
        mapping_file = os.path.join(BACKUP_DIR, "undo_mapping.json")
        
        if not os.path.exists(mapping_file):
            return f"Error: No undo history found"
        
        with open(mapping_file, "r") as f:
            mappings = json.load(f)
        
        if abs_path not in mappings:
            return f"Error: No backup found for '{path}'"
        
        backup_path = mappings[abs_path]
        
        if not os.path.exists(backup_path):
            return f"Error: Backup file no longer exists"
        
        # Restore from backup
        with open(backup_path, "r") as f:
            backup_content = f.read()
        
        with open(path, "w") as f:
            f.write(backup_content)
        
        # Remove from mappings
        del mappings[abs_path]
        with open(mapping_file, "w") as f:
            json.dump(mappings, f)
        
        # Clean up backup file
        os.remove(backup_path)
        
        return f"Successfully undone changes to {path}"
    except Exception as e:
        return f"Error undoing edit: {e}"


def batch_edit(file_pattern: str, old_text: str, new_text: str, directory: str = ".") -> str:
    """
    Apply the same edit to multiple files matching a pattern.
    
    Args:
        file_pattern: Glob pattern for files (e.g., "*.py")
        old_text: Text to find and replace
        new_text: Replacement text
        directory: Directory to search in
    """
    try:
        search_path = Path(directory)
        edited_files = []
        skipped_files = []
        
        for file_path in search_path.rglob(file_pattern):
            if file_path.is_file():
                try:
                    with open(file_path, "r") as f:
                        content = f.read()
                    
                    if old_text in content:
                        result = edit_file(str(file_path), old_text, new_text)
                        if "Successfully" in result:
                            edited_files.append(str(file_path))
                        else:
                            skipped_files.append(f"{file_path}: {result}")
                except:
                    skipped_files.append(str(file_path))
        
        output = f"Batch edit complete:\n"
        output += f"  Edited: {len(edited_files)} files\n"
        
        if edited_files:
            output += "  Files modified:\n"
            for f in edited_files[:10]:
                output += f"    - {f}\n"
            if len(edited_files) > 10:
                output += f"    ... and {len(edited_files) - 10} more\n"
        
        if skipped_files:
            output += f"  Skipped: {len(skipped_files)} files\n"
        
        return output
    except Exception as e:
        return f"Error in batch edit: {e}"


def run_command(command: str, cwd: str = None) -> str:
    """
    Run a shell command using bash.
    
    Args:
        command: The shell command to execute
        cwd: Optional working directory (defaults to current directory)
    """
    try:
        # Validate working directory if provided
        if cwd and not os.path.isdir(cwd):
            return f"Error: Working directory '{cwd}' does not exist"
        
        result = subprocess.run(
            command,
            shell=True,
            executable='/bin/bash',  # Use bash instead of sh
            capture_output=True,
            text=True,
            timeout=60,
            cwd=cwd
        )
        
        output = ""
        if result.stdout:
            output += result.stdout
        if result.stderr:
            output += f"\nStderr: {result.stderr}"
        
        if not output.strip():
            return f"Command completed with exit code {result.returncode} (no output)"
        
        return output
    except subprocess.TimeoutExpired:
        return "Error: Command timed out after 60 seconds"
    except Exception as e:
        return f"Error running command: {e}"



# Search and Analysis Tools
def search_file(path: str, pattern: str, use_regex: bool = False) -> str:
    """Search for a pattern in a file."""
    try:
        with open(path, "r") as f:
            content = f.read()

        lines = content.split("\n")
        matches = []

        for i, line in enumerate(lines, 1):
            if use_regex:
                if re.search(pattern, line):
                    matches.append(f"Line {i}: {line}")
            else:
                if pattern in line:
                    matches.append(f"Line {i}: {line}")

        if matches:
            return "\n".join(matches)
        else:
            return f"No matches found for '{pattern}' in {path}"
    except Exception as e:
        return f"Error searching file: {e}"


def grep_search(directory: str, pattern: str, file_pattern: str = "*") -> str:
    """Search for a pattern across multiple files in a directory."""
    try:
        matches = []
        search_path = Path(directory)

        for file_path in search_path.rglob(file_pattern):
            if file_path.is_file():
                try:
                    with open(file_path, "r") as f:
                        for i, line in enumerate(f, 1):
                            if pattern in line:
                                matches.append(f"{file_path}:{i}: {line.strip()}")
                except:
                    continue

        if matches:
            return "\n".join(matches[:50])  # Limit to 50 matches
        else:
            return f"No matches found for '{pattern}' in {directory}"
    except Exception as e:
        return f"Error searching directory: {e}"


def find_files(directory: str, name_pattern: str) -> str:
    """Find files by name pattern."""
    try:
        search_path = Path(directory)
        matches = []

        for file_path in search_path.rglob(name_pattern):
            matches.append(str(file_path))

        if matches:
            return "\n".join(matches)
        else:
            return f"No files found matching '{name_pattern}' in {directory}"
    except Exception as e:
        return f"Error finding files: {e}"


# Advanced File Operations
def delete_file(path: str) -> str:
    """Delete a file."""
    try:
        os.remove(path)
        return f"Successfully deleted {path}"
    except Exception as e:
        return f"Error deleting file: {e}"


def create_directory(path: str) -> str:
    """Create a new directory."""
    try:
        os.makedirs(path, exist_ok=True)
        return f"Successfully created directory {path}"
    except Exception as e:
        return f"Error creating directory: {e}"


def move_file(source: str, destination: str) -> str:
    """Move or rename a file."""
    try:
        shutil.move(source, destination)
        return f"Successfully moved {source} to {destination}"
    except Exception as e:
        return f"Error moving file: {e}"


def copy_file(source: str, destination: str) -> str:
    """Copy a file."""
    try:
        shutil.copy2(source, destination)
        return f"Successfully copied {source} to {destination}"
    except Exception as e:
        return f"Error copying file: {e}"


def append_to_file(path: str, content: str) -> str:
    """Append content to a file."""
    try:
        with open(path, "a") as f:
            f.write(content)
        return f"Successfully appended to {path}"
    except Exception as e:
        return f"Error appending to file: {e}"


def get_file_info(path: str) -> str:
    """Get file metadata."""
    try:
        stat = os.stat(path)
        info = f"Path: {path}\n"
        info += f"Size: {stat.st_size} bytes\n"
        info += f"Modified: {stat.st_mtime}\n"
        info += f"Is Directory: {os.path.isdir(path)}\n"
        return info
    except Exception as e:
        return f"Error getting file info: {e}"


# Git Integration
def git_status() -> str:
    """Get git status."""
    return run_command("git status")


def git_diff(file_path: str = "") -> str:
    """Show git diff."""
    if file_path:
        return run_command(f"git diff {file_path}")
    return run_command("git diff")


def git_log(num_commits: int = 10) -> str:
    """View git commit history."""
    return run_command(f"git log -n {num_commits} --oneline")


def git_commit(message: str) -> str:
    """Commit staged changes."""
    return run_command(f'git commit -m "{message}"')


def git_add(file_path: str) -> str:
    """Stage a file for commit."""
    return run_command(f"git add {file_path}")


# Package Management
def install_package(package_name: str) -> str:
    """Install a Python package using pip."""
    return run_command(f"pip install {package_name}")


def list_installed_packages() -> str:
    """List installed Python packages."""
    return run_command("pip list")


# Code Quality Tools
def check_syntax(path: str) -> str:
    """
    Check Python file for syntax errors using ast.parse().
    Fast validation without external dependencies.
    """
    try:
        with open(path, "r") as f:
            code = f.read()

        import ast

        try:
            ast.parse(code)
            return f"✓ Syntax check passed for {path}"
        except SyntaxError as e:
            return f"✗ Syntax error in {path}:\n  Line {e.lineno}: {e.msg}\n  {e.text}"
    except Exception as e:
        return f"Error checking syntax: {e}"


def lint_file(path: str, fix: bool = False) -> str:
    """
    Lint a Python file using ruff.
    Checks for style issues, bugs, and errors.

    Args:
        path: Path to the Python file
        fix: If True, automatically fix issues where possible
    """
    try:
        if not os.path.exists(path):
            return f"Error: File {path} does not exist"

        # Run ruff check
        cmd = f"ruff check {path}"
        if fix:
            cmd += " --fix"

        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=30
        )

        output = result.stdout
        if result.stderr:
            output += f"\n{result.stderr}"

        if result.returncode == 0:
            if fix:
                return f"✓ Linting passed and fixes applied for {path}\n{output}"
            else:
                return f"✓ No linting issues found in {path}"
        else:
            return f"Linting issues found in {path}:\n{output}"
    except Exception as e:
        return f"Error linting file: {e}"


def format_file(path: str) -> str:
    """
    Format a Python file using ruff.
    Applies PEP 8 and best practice formatting.
    """
    try:
        if not os.path.exists(path):
            return f"Error: File {path} does not exist"

        # Run ruff format
        result = subprocess.run(
            f"ruff format {path}",
            shell=True,
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode == 0:
            return f"✓ Successfully formatted {path}"
        else:
            error_msg = result.stderr or result.stdout
            return f"Error formatting {path}:\n{error_msg}"
    except Exception as e:
        return f"Error formatting file: {e}"


# Code Execution Sandbox
def python_repl(code: str) -> str:
    """
    Execute Python code in a safe sandbox environment.
    Captures stdout/stderr and enforces a timeout.
    """
    import io
    import contextlib
    import multiprocessing

    def _exec_code(code_str, queue):
        # Capture stdout/stderr
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()

        try:
            with (
                contextlib.redirect_stdout(stdout_capture),
                contextlib.redirect_stderr(stderr_capture),
            ):
                # Create a restricted globals dictionary if needed,
                # but for now we trust the agent but sandbox the process
                exec(code_str, {"__name__": "__main__"})

            queue.put(
                {
                    "stdout": stdout_capture.getvalue(),
                    "stderr": stderr_capture.getvalue(),
                    "success": True,
                }
            )
        except Exception:
            import traceback

            queue.put(
                {
                    "stdout": stdout_capture.getvalue(),
                    "stderr": traceback.format_exc(),
                    "success": False,
                }
            )

    # Use multiprocessing to allow timeout and isolation
    queue = multiprocessing.Queue()
    process = multiprocessing.Process(target=_exec_code, args=(code, queue))

    try:
        process.start()
        process.join(timeout=5)  # 5 second timeout

        if process.is_alive():
            process.terminate()
            process.join()
            return "Error: Code execution timed out (limit: 5 seconds)"

        if not queue.empty():
            result = queue.get()
            output = ""
            if result["stdout"]:
                output += f"Output:\n{result['stdout']}\n"
            if result["stderr"]:
                output += f"Errors:\n{result['stderr']}\n"

            if not output:
                output = "Code executed successfully (no output)"

            return output
        else:
            return "Error: Process finished but returned no result"

    except Exception as e:
        return f"Error executing code: {e}"

def wait(seconds: int, message: str = "Waiting...") -> str:
    """
    Wait for a specified number of seconds.
    
    Args:
        seconds: Number of seconds to wait
        message: Optional message to display while waiting
    """
    import time
    from rich.console import Console
    console = Console()
    
    try:
        with console.status(f"[dim]{message}[/dim]", spinner="clock"):
            time.sleep(seconds)
        return f"Waited for {seconds} seconds"
    except Exception as e:
        return f"Error waiting: {e}"
