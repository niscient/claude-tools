#!/usr/bin/env python3
"""
export_claude_projects_and_markdown.py

Copies all Claude Code project logs from the default location to an output
directory, then converts every JSONL session file to Markdown.

If the output directory already exists, any files within it may be overwritten.

The output directory can be specified either via a settings.ini file in the same
directory as this script (with a line "output_claude_project_logs=<path>"), or as
a mandatory command-line argument if the settings file is absent or does not
contain that key.

Usage:
    python export_claude_projects_and_markdown.py [<output_claude_project_logs>]
"""

import os
import shutil
import subprocess
import sys

CLAUDE_PROJECTS_DIR = os.path.join(os.path.expanduser("~"), ".claude", "projects")
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TRANSLATE_SCRIPT = os.path.join(SCRIPT_DIR, "translate_claude_session_jsonl_to_md.py")
SETTINGS_FILE = os.path.join(SCRIPT_DIR, "settings.ini")
SETTINGS_KEY = "output_claude_project_logs"


def read_output_dir_from_settings():
    """Return the output dir from settings.ini, or None if not found."""
    if not os.path.isfile(SETTINGS_FILE):
        return None

    matches = []
    with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
        for lineno, line in enumerate(f, 1):
            stripped = line.strip()
            if stripped.startswith(f"{SETTINGS_KEY}="):
                value = stripped[len(SETTINGS_KEY) + 1:]
                matches.append((lineno, value))

    if len(matches) > 1:
        lines = ", ".join(str(lineno) for lineno, _ in matches)
        print(
            f"Error: settings.ini contains multiple '{SETTINGS_KEY}' entries "
            f"(lines {lines}).",
            file=sys.stderr,
        )
        sys.exit(1)

    if matches:
        return matches[0][1]

    return None


def parse_args():
    output_dir = read_output_dir_from_settings()

    if output_dir is not None:
        if len(sys.argv) != 1:
            print(
                f"Error: output directory is already set in settings.ini; "
                f"no arguments expected.\n"
                f"Usage: {sys.argv[0]}",
                file=sys.stderr,
            )
            sys.exit(1)
        return output_dir

    if len(sys.argv) != 2:
        print(
            f"Error: exactly 1 argument required (no '{SETTINGS_KEY}' found in settings.ini).\n"
            f"Usage: {sys.argv[0]} <output_claude_project_logs>",
            file=sys.stderr,
        )
        sys.exit(1)
    return sys.argv[1]


def copy_projects(output_dir):
    if os.path.isfile(output_dir):
        print(
            f"Error: output path already exists and is a file: {output_dir}",
            file=sys.stderr,
        )
        sys.exit(1)

    if not os.path.isdir(CLAUDE_PROJECTS_DIR):
        print(
            f"Error: Claude projects directory not found: {CLAUDE_PROJECTS_DIR}",
            file=sys.stderr,
        )
        sys.exit(1)

    if not os.listdir(CLAUDE_PROJECTS_DIR):
        print(
            f"Error: Claude projects directory is empty: {CLAUDE_PROJECTS_DIR}",
            file=sys.stderr,
        )
        sys.exit(1)

    print(f"Copying {CLAUDE_PROJECTS_DIR} -> {output_dir} ...")
    # Walk source and copy every file, overwriting existing ones.
    for dirpath, dirnames, filenames in os.walk(CLAUDE_PROJECTS_DIR):
        rel = os.path.relpath(dirpath, CLAUDE_PROJECTS_DIR)
        dest_dir = os.path.join(output_dir, rel)
        try:
            os.makedirs(dest_dir, exist_ok=True)
        except OSError as e:
            print(f"Error: could not create directory {dest_dir}: {e}", file=sys.stderr)
            sys.exit(1)

        for filename in filenames:
            src = os.path.join(dirpath, filename)
            dst = os.path.join(dest_dir, filename)
            try:
                shutil.copy2(src, dst)
            except OSError as e:
                print(f"Error: could not copy {src} -> {dst}: {e}", file=sys.stderr)
                sys.exit(1)

    print("Copy complete.")


def find_jsonl_files(root):
    for dirpath, _, filenames in os.walk(root):
        for filename in filenames:
            if filename.endswith(".jsonl"):
                yield os.path.join(dirpath, filename)


def translate_jsonl_files(output_dir):
    jsonl_files = list(find_jsonl_files(output_dir))
    if not jsonl_files:
        print("No JSONL files found.")
        return

    print(f"Translating {len(jsonl_files)} JSONL file(s) to Markdown ...")
    for jsonl_path in jsonl_files:
        md_path = os.path.splitext(jsonl_path)[0] + ".md"
        print(f"  {jsonl_path} -> {md_path}")
        result = subprocess.run(
            [sys.executable, TRANSLATE_SCRIPT, "--force", jsonl_path, md_path],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            stderr_msg = result.stderr.strip() or "(no stderr output)"
            print(
                f"Error: translation failed for {jsonl_path}:\n{stderr_msg}",
                file=sys.stderr,
            )
            sys.exit(1)

    print("All translations complete.")


def main():
    output_dir = parse_args()
    copy_projects(output_dir)
    translate_jsonl_files(output_dir)


if __name__ == "__main__":
    main()
