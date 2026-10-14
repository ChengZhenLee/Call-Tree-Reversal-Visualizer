from .classes import ArrowMode

COL_SPACING = "1.0cm"
ROW_SPACING = "1.0cm"

# arrow of a node, decided by its running mode (the first matching mode wins);
# adjoint arrows go below the name, primal arrows above
RUNNING_MODES = {
    ArrowMode.adjointForward:  r"\underrightarrow",
    ArrowMode.adjointBackward: r"\underleftarrow",
    ArrowMode.primalForward:   r"\overrightarrow",
    ArrowMode.primalBackward:  r"\overleftarrow",
}

# adjoint forward and backward in one node, below the name
MERGED_ARROW = r"\underleftrightarrow"

# shown to the left of the name
MARKERS = {
    ArrowMode.save: r"\downarrow",
    ArrowMode.load: r"\uparrow",
}


# Have a function that initializes the latex file with the appropriate headers
def latex_header():
    return "\n".join([
        r"\documentclass{article}",
        r"\usepackage[landscape,margin=1cm]{geometry}",
        r"\usepackage{tikz}",
        r"\usepackage[export]{adjustbox}",
        r"\usepackage{amsmath}",
        r"\pagestyle{empty}",
        r"\setlength{\parindent}{0pt}",
        r"\begin{document}",
        "",
    ])


def latex_footer():
    return "\\end{document}\n"


# Assign a (column, depth) to every visual node.
# Leaves take consecutive columns; a parent sits above its first child.
def _layout(root, counter):
    placed = []

    def place(node, depth, parentIndex):
        index = len(placed)
        entry = {"node": node, "depth": depth, "parent": parentIndex, "col": None}
        placed.append(entry)

        if not node.children:
            entry["col"] = counter[0]
            counter[0] += 1
        else:
            for child in node.children:
                place(child, depth + 1, index)
            entry["col"] = placed[index + 1]["col"]

    place(root, 0, None)
    return placed


def _label(node):
    arrow = r"\overrightarrow"
    # a merged node (reload immediately followed by its reversal) gets a double arrow
    if (ArrowMode.adjointForward in node.arrowModes
            and ArrowMode.adjointBackward in node.arrowModes):
        arrow = MERGED_ARROW
    else:
        for mode in node.arrowModes:
            if mode in RUNNING_MODES:
                arrow = RUNNING_MODES[mode]
                break

    markers = "".join(MARKERS[m] for m in node.arrowModes if m in MARKERS)
    name = node.name.replace("_", r"\_")
    text = markers + f"{arrow}{{\\mathit{{{name}}}}}"

    return f"$ {text} $"


# Have a function that draws the tree in latex
# trees: visual roots laid out left to right (forward tree, then backward tree)
def draw_tree(trees, title):
    counter = [0]
    lines = [f"\\subsection*{{{title}}}", r"\adjustbox{max width=\linewidth}{",
             r"\begin{tikzpicture}[",
             f"  x={COL_SPACING}, y=-{ROW_SPACING},",
             r"  every node/.style={inner sep=2pt}]"]

    for treeId, root in enumerate(trees):
        placed = _layout(root, counter)

        for index, entry in enumerate(placed):
            lines.append(
                f"  \\node (n{treeId}_{index}) at "
                f"({entry['col']}, {entry['depth']}) {{{_label(entry['node'])}}};")

    lines += [r"\end{tikzpicture}", "}", r"\bigskip", ""]
    return "\n".join(lines)
