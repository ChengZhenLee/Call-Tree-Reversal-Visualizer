# Call Tree Reversal Visualizer

Given a call tree of functions, this tool draws the forward and backward
(adjoint) passes for every possible choice of checkpointed functions, and
reports the operation cost and memory cost of each choice. The output is a
single LaTeX file.

## Requirements

- Python 3

The tool itself only writes a plain-text LaTeX file (`output.tex` by default) and does not need
LaTeX installed. To view the pictures you need something that can compile
LaTeX, but this does not have to be a local install (see Usage).

## Usage

1. Fill in `input.json` (format below). It starts as a blank template with a
   single empty function, and is the file the tool reads by default. The
   examples below show filled-in inputs.
2. Run the tool from the project folder:
   - Linux / macOS: `./run_tool.sh`
   - Windows: double-click `run_tool.bat`
   - Anywhere: `python main.py`

   Add options after the command to change the mode, input or output file
   (see below), e.g. `./run_tool.sh -i my_tree.json -o my_tree.tex`.
3. View the result by compiling the output file (`output.tex` unless you chose
   another with `-o`), either:
   - locally with `pdflatex output.tex` (needs the `tikz`, `amsmath`,
     `geometry` and `adjustbox` packages), or
   - online, with nothing to install: upload or paste the file into a LaTeX
     editor such as Overleaf.

Options (also accepted by the launchers):

| Flag | Meaning | Default |
|---|---|---|
| `-m`, `--mode` | `enumerate`: every combination of checkpoints; `heuristic`: only the result of each greedy heuristic under the memory limit; `dp`: the dynamic programming schedule for the `checkpoints` limit (evolution programs only) | `enumerate` |
| `-i`, `--input` | input json file | `input.json` |
| `-o`, `--output` | output latex file | `output.tex` |

For example: `python main.py --mode heuristic`.

### Example inputs

| File | Use with | What it is |
|---|---|---|
| `heuristics_example.json` | `--mode heuristic` | A small call tree with a memory limit of 160, for the greedy heuristics. |
| `dp_example.json` | `--mode dp` | An evolution program: a root with six leaf children and 3 checkpoints. |

For example:

```
python main.py --mode heuristic --input heuristics_example.json
python main.py --mode dp --input dp_example.json
```

### Enumerate mode

Draws every combination of checkpointed functions (the root is never
checkpointed), so a tree with `n` non-root functions gives `2^n` pictures.

### Heuristic mode

Draws one picture per greedy heuristic, using the `memory` limit. Each
heuristic orders the functions by their own-run memory cost, increasing or
decreasing:

- **Greedy checkpointing**: starts with no checkpoints and adds a checkpoint
  whenever it lowers the memory cost, until the limit is met.
- **Greedy checkpoint removal**: starts with everything checkpointed and removes
  checkpoints until removing the next one would exceed the limit.

A title marked "(over memory limit)" means the heuristic could not meet the
limit.

### Dynamic programming mode

Only for *evolution* programs: a root with no work of its own (every `cost`
entry is 0) whose children are all leaves. Any other input stops with an error.

Treats the children as a chain of steps `1..n` and finds the checkpoint
schedule with the least recomputation for the `checkpoints` limit, which counts
the stored start state, so a limit of 3 gives two checkpointed functions. A
checkpoint at split `s` is drawn as child `s` being checkpointed, so the last
child is never checkpointed. The splits are fixed positions, each saved once.

## Input format

```json
{
    "functions": {
        "f": { "cost": [10, 10, 0], "children": ["g", "s"] },
        "g": { "cost": [50, 50],    "children": ["h"] },
        "s": { "cost": [20],        "children": [] },
        "h": { "cost": [50],        "children": [] }
    },
    "limits": {
        "memory": 120,
        "checkpoints": 3
    }
}
```

- `limits.checkpoints` is only used by `--mode dp`.
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
main.py             entry point and command line options
input.json          the call tree (a blank template to fill in)
heuristics_example.json, dp_example.json   example inputs for the heuristic and dp modes
run_tool.sh/.bat    launchers for Linux/macOS and Windows
src/
  classes.py        function and visual node classes
  parser.py         reads the json, builds the forward/backward trees
  cost.py           operation and memory cost
  heuristics.py     greedy checkpointing heuristics
  dp.py             dynamic programming checkpoint schedule for evolution programs
  modes.py          what to draw: enumerate all, run the heuristics or the dynamic programming schedule
  latex.py          draws the trees as LaTeX/TikZ
```
