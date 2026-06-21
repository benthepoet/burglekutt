"""Load assembly export format directories from formats/."""

import json
import os

_DEFAULTS = {
    "name": "Default",
    "byte_keyword": "BYTE",
    "hex_prefix": ">",
    "indent": "    ",
    "comment_prefix": ";",
    "labels": {
        "patterns": "PATTERNS",
        "colors": "COLORS",
        "metas": "METAS",
        "metas_end": "METASEND",
        "supers": "SUPERS",
        "supers_end": "SUPERSEND",
    },
}


def repo_root():
    """Return the repository root (parent of src/)."""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def formats_dir():
    """Return the path to the formats/ directory."""
    return os.path.join(repo_root(), "formats")


def list_formats():
    """Return sorted format directory names."""
    root = formats_dir()
    if not os.path.isdir(root):
        return []
    names = []
    for entry in sorted(os.listdir(root)):
        path = os.path.join(root, entry)
        if os.path.isdir(path) and os.path.isfile(os.path.join(path, "format.json")):
            names.append(entry)
    return names


def load_format(name="ti99_default"):
    """Load format.json and *.tpl templates for the named dialect."""
    fmt_dir = os.path.join(formats_dir(), name)
    config_path = os.path.join(fmt_dir, "format.json")
    if not os.path.isfile(config_path):
        raise FileNotFoundError("format not found: {}".format(name))

    with open(config_path, "r", encoding="utf-8") as handle:
        config = json.load(handle)

    fmt = dict(_DEFAULTS)
    fmt.update(config)
    labels = dict(_DEFAULTS["labels"])
    labels.update(config.get("labels", {}))
    fmt["labels"] = labels
    fmt["id"] = name

    templates = {}
    for filename in sorted(os.listdir(fmt_dir)):
        if filename.endswith(".tpl"):
            key = filename[:-4]
            tpl_path = os.path.join(fmt_dir, filename)
            with open(tpl_path, "r", encoding="utf-8") as handle:
                templates[key] = handle.read()
    fmt["templates"] = templates
    return fmt