# Call Tree Reversal Visualizer

Given a call tree of functions, this tool draws the forward and backward
(adjoint) passes for every possible choice of checkpointed functions, and
reports the operation cost and memory cost of each choice. The output is a
single LaTeX file.

## Requirements

- Python 3

The tool itself only writes a plain-text `output.tex` file and does not need
LaTeX installed. To view the pictures you need something that can compile
LaTeX, but this does not have to be a local install (see Usage).

## Usage

1. Edit `input.json` (format below).
2. Run the tool from the project folder:
   - Linux / macOS: `./run_tool.sh`
   - Windows: double-click `run_tool.bat`
   - Anywhere: `python main.py`
3. View the result by compiling `output.tex`, either:
   - locally with `pdflatex output.tex` (needs the `tikz`, `amsmath`,
     `geometry` and `adjustbox` packages), or
   - online, with nothing to install: upload or paste `output.tex` into a
     LaTeX editor such as Overleaf.

The tool always reads `input.json` and writes `output.tex` in the folder it
is run from.

## Input format

```json
{
    "functions": {
        "f": { "cost": [10, 10, 0], "children": ["g", "s"] },
        "g": { "cost": [50, 50],    "children": ["h"] },
        "s": { "cost": [20],        "children": [] },
        "h": { "cost": [50],        "children": [] }
    }
}
```

- `children` lists the functions called, in call order.
- `cost` is the work done between calls, so it has one more entry than
  `children`: the work before the first call, between calls, and after the
  last call.
- The functions must form a tree with exactly one root (a function nobody
  calls). The root is never checkpointed. A function may be called from only
  one place.

## Reading the output

Each combination of checkpointed functions gets its own picture, titled with
the checkpointed functions and the two costs. The forward pass is on the left
and the backward pass on the right.

| Symbol | Meaning |
|---|---|
| arrow **below** the name (`f` with → or ←) | adjoint run, forward or backward |
| arrow **above** the name | primal run (no tape), forward or backward |
| ↓ to the left of the name | checkpoint saved |
| ↑ to the left of the name | checkpoint loaded |

## Costs

- **Operation cost**: the cost of the whole program plus one re-run of each checkpointed function.
- **Memory cost**: the maximum amount of memory used at any point in time. This includes any regrow phase due to checkpointing.
- **Note**: the operation and memory costs of loading and saving input or outputs during checkpointing are not considered.

## Project layout

```
main.py             entry point
input.json          the call tree
run_tool.sh/.bat    launchers for Linux/macOS and Windows
src/
  classes.py        function and visual node classes
  parser.py         reads the json, builds the forward/backward trees
  cost.py           operation and memory cost
  latex.py          draws the trees as LaTeX/TikZ
```
