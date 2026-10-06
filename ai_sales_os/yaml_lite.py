"""Minimal YAML subset parser (stdlib only).

Supports the constructs used by ICP config files:
  - top-level mapping keys
  - scalar values: strings (plain or quoted), ints, floats, booleans, null
  - nested mappings via indentation
  - lists via "- " items at one indent level

Anything beyond this raises ValueError; callers may use JSON instead.
"""

from __future__ import annotations

import re


def _parse_scalar(text: str):
    text = text.strip()
    if text == "" or text == "~" or text.lower() == "null":
        return None
    if text.lower() in ("true", "yes", "on"):
        return True
    if text.lower() in ("false", "no", "off"):
        return False
    if (text.startswith('"') and text.endswith('"')) or (
        text.startswith("'") and text.endswith("'")
    ):
        return text[1:-1]
    if re.fullmatch(r"[+-]?\d+", text):
        return int(text)
    if re.fullmatch(r"[+-]?\d*\.\d+([eE][+-]?\d+)?", text):
        return float(text)
    return text


def load(text: str) -> dict:
    """Parse a small YAML-subset document into a dict."""
    lines = []
    for lineno, raw in enumerate(text.splitlines(), start=1):
        if "\t" in raw:
            raise ValueError(
                f"Tabs are not supported for indentation (line {lineno}); "
                "use spaces"
            )
        # strip comments (a "#" not inside quotes starts a comment)
        stripped = _strip_comment(raw)
        if stripped.strip() == "":
            continue
        indent = len(stripped) - len(stripped.lstrip(" "))
        lines.append((indent, stripped.strip()))

    if not lines:
        return {}

    result, _ = _parse_block(lines, 0, 0)
    if not isinstance(result, dict):
        raise ValueError("Top-level YAML must be a mapping")
    return result


def _strip_comment(line: str) -> str:
    in_single = in_double = False
    for i, ch in enumerate(line):
        if ch == "'" and not in_double:
            in_single = not in_single
        elif ch == '"' and not in_single:
            in_double = not in_double
        elif ch == "#" and not in_single and not in_double:
            # comment only if preceded by whitespace or at line start
            if i == 0 or line[i - 1] in " \t":
                return line[:i]
    return line


def _parse_block(lines, pos, indent):
    """Parse lines[pos:] belonging to a block at `indent`.

    Returns (value, next_pos). Value is a dict or list.
    """
    if pos >= len(lines):
        return {}, pos
    cur_indent, cur_text = lines[pos]

    if cur_text.startswith("- ") or cur_text == "-":
        return _parse_list(lines, pos, indent)

    mapping = {}
    while pos < len(lines):
        cur_indent, cur_text = lines[pos]
        if cur_indent < indent:
            break
        if cur_indent > indent:
            raise ValueError(f"Unexpected indent at line: {cur_text!r}")
        if cur_text.startswith("- "):
            raise ValueError(
                f"List item inside mapping block: {cur_text!r}"
            )
        if ":" not in cur_text:
            raise ValueError(f"Expected key: value at line: {cur_text!r}")
        key, _, rest = cur_text.partition(":")
        key = key.strip()
        if not key:
            raise ValueError(f"Empty key at line: {cur_text!r}")
        rest = rest.strip()
        pos += 1
        if rest == "":
            # nested block: peek ahead
            if pos < len(lines) and lines[pos][0] > indent:
                value, pos = _parse_block(lines, pos, lines[pos][0])
            else:
                value = None
        elif rest == "|" or rest == ">":
            raise ValueError("Block scalars are not supported by this parser")
        else:
            value = _parse_scalar(rest)
        mapping[key] = value
    return mapping, pos


def _parse_list(lines, pos, indent):
    items = []
    while pos < len(lines):
        cur_indent, cur_text = lines[pos]
        if cur_indent < indent or not cur_text.startswith("-"):
            break
        if cur_indent > indent:
            raise ValueError(f"Unexpected indent at line: {cur_text!r}")
        item_text = cur_text[1:].strip()
        pos += 1
        if _is_inline_mapping(item_text) and not _looks_scalar(item_text):
            # inline mapping "- key: value" (single pair; nested handled simply)
            key, _, rest = item_text.partition(":")
            sub = {key.strip(): _parse_scalar(rest)}
            # consume deeper-indented continuation lines as more keys
            while pos < len(lines) and lines[pos][0] > indent:
                k, _, r = lines[pos][1].partition(":")
                if not r and ":" not in lines[pos][1]:
                    raise ValueError(
                        f"Expected key: value at line: {lines[pos][1]!r}"
                    )
                sub[k.strip()] = _parse_scalar(r)
                pos += 1
            items.append(sub)
        elif item_text == "" and pos < len(lines) and lines[pos][0] > indent:
            value, pos = _parse_block(lines, pos, lines[pos][0])
            items.append(value)
        else:
            items.append(_parse_scalar(item_text))
    return items, pos


def _is_inline_mapping(text: str) -> bool:
    # "- key: value" / "- key:" is an inline mapping, but a bare colon inside
    # a scalar ("- http://x:8080/y", "- 12:30") is not — YAML only treats a
    # colon as a mapping separator when followed by space or end of line.
    t = text.strip()
    return t.endswith(":") or ": " in t


def _looks_scalar(text: str) -> bool:
    # Heuristic: quoted strings or pure scalars are not inline mappings
    t = text.strip()
    if (t.startswith('"') and t.endswith('"')) or (
        t.startswith("'") and t.endswith("'")
    ):
        return True
    return False
