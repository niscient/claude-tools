#!/usr/bin/env python3
"""
translate_claude_session_jsonl_to_md.py

Converts a Claude Code session JSONL file into a readable Markdown transcript.

Usage:
    python translate_claude_session_jsonl_to_md.py [--force] <input.jsonl> <output.md>

Options:
    --force    If the output file already exists, overwrite it without prompting.
"""

import json
import os
import sys
from datetime import datetime


def parse_args():
    args = sys.argv[1:]
    force = "--force" in args
    args = [a for a in args if a != "--force"]

    if len(args) != 2:
        print(
            "Error: exactly 2 arguments required.\n"
            f"Usage: {sys.argv[0]} [--force] <input.jsonl> <output.md>",
            file=sys.stderr,
        )
        sys.exit(1)

    input_path = args[0]
    output_path = args[1]

    if not os.path.isfile(input_path):
        print(f"Error: input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    if not input_path.lower().endswith(".jsonl"):
        print(
            f"Error: input file must be a .jsonl file: {input_path}",
            file=sys.stderr,
        )
        sys.exit(1)

    if os.path.exists(output_path) and not force:
        answer = input(f"Output file already exists: {output_path}\nOverwrite? [y/N] ").strip().lower()
        if answer not in ("y", "yes"):
            print("Aborted.")
            sys.exit(0)

    return input_path, output_path


def load_jsonl(path):
    records = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return records


def format_timestamp(ts_str):
    if not ts_str:
        return ""
    try:
        dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        return dt.strftime("%H:%M:%S UTC")
    except (ValueError, TypeError):
        return ts_str


def extract_text_from_content(content):
    """Recursively extract readable text from message content (string or list of blocks)."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if not isinstance(block, dict):
                continue
            btype = block.get("type", "")

            if btype == "text" and block.get("text"):
                parts.append(block["text"])

            elif btype == "tool_use":
                name = block.get("name", "unknown_tool")
                inp = block.get("input", {})
                parts.append(f"**Tool Call: `{name}`**")
                if isinstance(inp, dict):
                    for k, v in inp.items():
                        parts.append(f"- `{k}`: `{str(v)}`")

            elif btype == "tool_result":
                inner = block.get("content", "")
                text = extract_text_from_content(inner)
                if text:
                    parts.append(f"**Tool Result:**\n```\n{text}\n```")

            elif btype == "thinking" and block.get("thinking"):
                parts.append(f"> **Thinking:** {block['thinking']}")

        return "\n\n".join(parts)
    return str(content)


def extract_metadata(records):
    meta = {
        "session_id": None,
        "title": None,
        "git_branch": None,
        "cwd": None,
        "entrypoint": None,
        "version": None,
    }
    for obj in records:
        if not meta["session_id"] and obj.get("sessionId"):
            meta["session_id"] = obj["sessionId"]
        if obj.get("type") == "ai-title" and obj.get("aiTitle"):
            meta["title"] = obj["aiTitle"]
        if not meta["git_branch"] and obj.get("gitBranch"):
            meta["git_branch"] = obj["gitBranch"]
        if not meta["cwd"] and obj.get("cwd"):
            meta["cwd"] = obj["cwd"]
        if not meta["entrypoint"] and obj.get("entrypoint"):
            meta["entrypoint"] = obj["entrypoint"]
        if not meta["version"] and obj.get("version"):
            meta["version"] = obj["version"]
    return meta


def is_skippable(obj, content_str):
    """Return True for meta/infrastructure messages that shouldn't appear in the transcript."""
    if obj.get("isMeta"):
        return True
    if "<command-name>/export</command-name>" in content_str:
        return True
    if "<local-command-stdout>" in content_str and "exported to" in content_str:
        return True
    return False


def build_markdown(records):
    meta = extract_metadata(records)
    md = []

    # Header
    md.append(f"# {meta['title'] or 'Claude Code Session'}\n")
    md.append(f"**Session ID:** `{meta['session_id']}`  ")
    if meta["cwd"]:
        md.append(f"**Working Directory:** `{meta['cwd']}`  ")
    if meta["git_branch"]:
        md.append(f"**Git Branch:** `{meta['git_branch']}`  ")
    if meta["entrypoint"]:
        md.append(f"**Entrypoint:** {meta['entrypoint']}  ")
    if meta["version"]:
        md.append(f"**Claude Code Version:** {meta['version']}  ")
    md.append("")
    md.append("---\n")

    # Conversation messages
    for obj in records:
        if obj.get("type") not in ("user", "assistant"):
            continue

        message = obj.get("message", {})
        role = message.get("role", obj["type"])
        content = message.get("content", "")
        ts = format_timestamp(obj.get("timestamp", ""))

        content_str = str(content)
        if is_skippable(obj, content_str):
            continue

        text = extract_text_from_content(content)
        if not text or not text.strip():
            continue

        # Clean up IDE context tags for readability
        text = text.replace("<ide_opened_file>", "\U0001f4c2 *IDE Context:* ").replace(
            "</ide_opened_file>", ""
        )

        if role == "user":
            md.append(f"## \U0001f9d1 User \u2014 `{ts}`\n")
            md.append(text)
            md.append("")
        elif role == "assistant":
            model = message.get("model", "")
            model_tag = f" ({model})" if model else ""
            md.append(f"## \U0001f916 Assistant{model_tag} \u2014 `{ts}`\n")
            md.append(text)
            md.append("")

    return "\n".join(md)


def main():
    input_path, output_path = parse_args()
    records = load_jsonl(input_path)

    if not records:
        print("Error: no valid JSON records found in input file.", file=sys.stderr)
        sys.exit(1)

    markdown = build_markdown(records)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(markdown)

    msg_counts = {
        "user": sum(
            1
            for r in records
            if r.get("type") == "user"
            and not is_skippable(r, str(r.get("message", {}).get("content", "")))
        ),
        "assistant": sum(1 for r in records if r.get("type") == "assistant"),
    }

    print(f"Done. Wrote {len(markdown):,} chars to {output_path}")
    print(f"  {msg_counts['user']} user messages, {msg_counts['assistant']} assistant messages")


if __name__ == "__main__":
    main()
