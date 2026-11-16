# Call Tree Reversal Visualizer

Given a call tree of functions, this tool draws the forward and backward
(adjoint) passes for every possible choice of checkpointed functions, and
reports the operation cost and memory cost of each choice. The output is a
single LaTeX file.

## Requirements

- Python 3
- numpy, for `--mode experiment` only (`pip install numpy`)

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
| `-m`, `--mode` | `enumerate`: every combination of checkpoints; `heuristic`: only the result of each greedy heuristic under the memory limit; `profile`: only the result of each profiling strategy under the memory limit; `dp`: the dynamic programming schedule for the `checkpoints` limit (evolution programs only); `random`: one random tree, its optimum, every heuristic and every profiling strategy; `experiment`: random trees compared against the optimum, written to a CSV | `enumerate` |
| `-i`, `--input` | input json file (not used by `random` or `experiment`) | `input.json` |
| `-o`, `--output` | output file | `output.tex`, or `results.csv` for `experiment` |
| `-t`, `--trees` | `experiment` only: trees per combination of settings | `10` |

Random mode also takes `--nodes`, `--depth`, `--width`, `--max-children`,
`--max-segment-cost`, `--seed` and `--alpha` (see Random mode below).

For example: `python main.py --mode heuristic`.

### Example inputs

| File | Use with | What it is |
|---|---|---|
| `heuristic_example.json` | `--mode heuristic` | A small call tree with a memory limit of 160, for the greedy heuristics. |
| `profiling_example.json` | `--mode profile` | The same call tree and memory limit, for the profiling strategies. |
| `dp_example.json` | `--mode dp` | An evolution program: a root with six leaf children and 3 checkpoints. |

For example:

```
python main.py --mode heuristic --input heuristic_example.json
python main.py --mode profile --input profiling_example.json
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

### Profile mode

Draws one picture per profiling strategy, using the `memory` limit. Profiling
starts with everything checkpointed (if even that exceeds the limit, it fails)
and then removes checkpoints one at a time. In each round it tries removing every
remaining checkpoint, drops the ones that would push the memory cost over the
limit, and lets the strategy pick among the rest. It stops when no checkpoint can
be removed. The strategies differ in how they pick:

- **Most runtime decrease**: the removal that leaves the lowest operation cost.
- **Least memory usage**: the removal that leaves the lowest memory cost.

A title marked "(over memory limit)" means that even checkpointing every function
could not meet the limit.

### Dynamic programming mode

Only for *evolution* programs: a root with no work of its own (every `cost`
entry is 0) whose children are all leaves. Any other input stops with an error.

Treats the children as a chain of steps `1..n` and finds the checkpoint
schedule with the least recomputation for the `checkpoints` limit, which counts
the stored start state, so a limit of 3 gives two checkpointed functions. A
checkpoint at split `s` is drawn as child `s` being checkpointed, so the last
child is never checkpointed. The splits are fixed positions, each saved once.

The title shows the DP's own costs rather than the call tree ones. Each step is
recorded once when it is reversed, so the operation cost is the sum of all step
costs plus the advancing the schedule does. Steps are reversed one at a time and
stored states are not counted, so the peak memory is the largest single step,
whatever the number of checkpoints. The title shows the checkpoint limit, the
`memory` limit and the peak memory, and is marked "(over memory limit)" when the
largest step does not fit.

### Random mode

```
python main.py --mode random --nodes 8 --depth 0.5 --width -0.5 --alpha 0.3
```

Generates one random call tree instead of reading an input file, finds the
cheapest checkpoint choice under the memory limit by trying every combination
(the optimum), and draws it followed by the result of every heuristic and
profiling strategy. Each strategy's title shows its cost ratio to the optimum, or "(over memory
limit)". The first line of the output lists the settings and the memory range.

| Flag | Meaning | Default |
|---|---|---|
| `--nodes` | number of functions, including the root | `8` |
| `--depth` | from -1 (favours shallow parents: wide trees) to 1 (favours deep parents: chains) | `0` |
| `--width` | from -1 (favours parents with few children: thin trees) to 1 (favours parents with many: hubs and stars) | `0` |
| `--max-children` | most children per function | no limit |
| `--max-segment-cost` | each cost segment is drawn from 0 to this | `10` |
| `--max-snapshot-cost` | each snapshot (except the root's, which is 0) is drawn from 0 to this | same as `--max-segment-cost` |
| `--seed` | rebuilds the same tree with the same settings | random, printed |
| `--alpha` | memory limit between the lowest (0) and highest (1) memory any choice reaches | `0.5` |

To look at a tree from the experiment CSV, pass its `seed`, `nodes`,
`depthSetting`, `widthSetting`, `maxChildren`, `maxSegmentCost`,
`maxSnapshotCost` and `alpha`.

### Experiment mode

```
python main.py --mode experiment --trees 10 --output results.csv
```

Generates random call trees instead of reading an input file. It makes one
tree for every combination of the settings at the top of
`src/tree_generator.py`, `--trees` times with different seeds:

- depth and width settings from -1 to 1, which favour deep or shallow parents
  and parents with many or few children
- number of nodes, limit on children per node, largest segment cost and
  largest snapshot cost

For each tree it tries every checkpoint combination to find the lowest
(`minMemory`) and highest (`maxMemory`) memory cost. For each `alpha` it sets
the memory limit to `minMemory + alpha * (maxMemory - minMemory)`, finds the
cheapest combination that fits (the optimum) and runs every heuristic and every
profiling strategy.

The CSV has one row per tree, alpha and strategy (a heuristic or a profiling
strategy, named in the `strategy` column), with the settings, the tree's
measured shape, the limit, the optimum and the strategy's result.
`costRatio` is the strategy's operation cost divided by the optimum's (blank
when it is over the limit), and `isOptimal` says whether it matched the
optimum. A tree can be rebuilt from its `seed` and settings.

Trying every combination doubles in time with each extra node: about 1 to 2 s
for a 16-node tree, and roughly 15 s or more at 20 nodes. The default settings
(up to 16 nodes, `--trees 10`) take about 15 hours. Trees are generated
smallest first, so a run stopped early still has complete results for the
smaller sizes. The last tree of a stopped run may have fewer rows than the
others, so drop it before analysing.

## Input format

```json
{
    "functions": {
        "f": { "cost": [10, 10, 0], "snapshot": 0,  "children": ["g", "s"] },
        "g": { "cost": [50, 50],    "snapshot": 10, "children": ["h"] },
        "s": { "cost": [20],        "snapshot": 5,  "children": [] },
        "h": { "cost": [50],        "snapshot": 5,  "children": [] }
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
- `snapshot` is the memory needed to store the function's inputs when it is
  checkpointed. Saving and loading it each cost this much work too. It is
  optional and defaults to 0. The dp mode ignores it.
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

- **Operation cost**: the cost of the whole program plus, for each checkpointed function, one re-run and saving and loading its snapshot (`2 * snapshot`).
- **Memory cost**: the maximum amount of memory used at any point in time. This includes any regrow phase due to checkpointing, and the snapshot held for each checkpointed function in place of its tape.

## Project layout

```
main.py             entry point and command line options
input.json          the call tree (a blank template to fill in)
heuristic_example.json, profiling_example.json, dp_example.json   example inputs for the heuristic, profile and dp modes
run_tool.sh/.bat    launchers for Linux/macOS and Windows
src/
  classes.py        function and visual node classes
  parser.py         reads the json, builds the forward/backward trees
  cost.py           operation and memory cost
  heuristics.py     greedy checkpointing heuristics
  profiling.py      profiling: start fully checkpointed and remove checkpoints by a strategy
  brute_force.py    tries every checkpoint combination, finds the optimum under a memory limit
  tree_generator.py random call trees and the experiment CSV
  dp.py             dynamic programming checkpoint schedule for evolution programs
  modes.py          the modes: enumerate all, run the heuristics, run the profiling strategies, the dynamic programming schedule, or the experiment
  latex.py          draws the trees as LaTeX/TikZ
```
