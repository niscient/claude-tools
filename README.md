# Claude Session Backup Tools

These tools allow you to make quick backups of your Claude Code chat sessions to a designated output directory, and translate all chat sessions into human-readable Markdown (`.md`) files. This is useful for archiving conversations, searching past sessions, or simply keeping a local record of your Claude interactions. Tested on Windows, in theory works on Mac and Linux.

---

## Tool 1: `export_claude_projects_and_markdown.py`

This is the primary tool. It copies your entire `~/.claude/projects` directory (aka `%userprofile%/.claude/settings.json` on Windows) to a configured output directory, then automatically converts every `.jsonl` session file it finds into a `.md` transcript.

**Steps it performs:**
1. Copies `~/.claude/projects` (recursively) to the output directory
2. Finds all `.jsonl` files in the output
3. Runs the translator on each `.jsonl` file, to produce a `.md` file alongside it

**Configuration via `settings.ini`:**

The recommended way to configure the output path is to set it in `settings.ini` (located in the same directory as the script):

```ini
output_claude_project_logs=C:\path\to\your\output\directory
```

With this in place, run the tool with no arguments:

```
python export_claude_projects_and_markdown.py
```

**Alternatively**, pass the output directory directly on the command line:

```
python export_claude_projects_and_markdown.py <output_directory>
```

Note: do not provide both a command-line argument and a `settings.ini` entry at the same time — the script will exit with an error.

---

## Tool 2: `translate_claude_session_jsonl_to_md.py`

Converts a single Claude Code session file (`.jsonl`) into a readable Markdown transcript. This is called automatically by the export tool, but can also be run on its own if you want to convert a specific session file.

**Usage:**

```
python translate_claude_session_jsonl_to_md.py [--force] <input.jsonl> <output.md>
```

**Arguments:**

- `<input.jsonl>` — path to the session file to convert (must end in `.jsonl`)
- `<output.md>` — path where the Markdown output will be written
- `--force` (optional) — overwrite the output file without prompting if it already exists; without this flag, the script will ask interactively

**Output includes:**
- Session metadata (session ID, working directory, git branch, Claude Code version)
- Timestamped user and assistant messages
- Tool calls with parameters
- Tool results in code blocks
- Thinking blocks as blockquotes

---

## Preventing Auto-Deletion of Session Files

By default, Claude Code deletes old session files after **30 days**. If you do not change this setting, your session history will be periodically wiped and there will be nothing left to export.

To prevent this, set `cleanupPeriodDays` to a large value in `~/.claude/settings.json` (aka `%userprofile%/.claude/settings.json` on Windows), e.g.:

```json
{
  "cleanupPeriodDays": 99999
}
```

This tells Claude Code to retain session files effectively indefinitely (or at least for a few hundred years, by which time your code will no doubt still be running strong).

For more context on this behavior, see:
- [GitHub issue #4172 — Claude Code deletes old sessions](https://github.com/anthropics/claude-code/issues/4172)
- [Claude Code settings documentation](https://code.claude.com/docs/en/settings)
