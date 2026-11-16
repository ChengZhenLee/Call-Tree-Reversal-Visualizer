import argparse

from src.modes import MODES

# Settings used by the random and experiment modes, and their defaults
DEFAULT_OPTIONS = {
    "trees": 10,
    "nodes": 8,
    "depth": 0.0,
    "width": 0.0,
    "maxChildren": None,
    "maxSegmentCost": 10,
    "maxSnapshotCost": None,
    "seed": None,
    "alpha": 0.5,
}


def main(inputName="input.json", outputName="output.tex", mode="enumerate", **options):
    MODES[mode](inputName, outputName, {**DEFAULT_OPTIONS, **options})

    print(f"Wrote {outputName}")
    return 0


if __name__ == "__main__":
    argParser = argparse.ArgumentParser(description="Draw call tree reversals for checkpointing choices.")
    argParser.add_argument("-m", "--mode", choices=list(MODES), default="enumerate",
                           help="enumerate: every combination of checkpoints; "
                                "heuristic: the result of each heuristic under the memory limit; "
                                "profile: the result of each profiling strategy under the memory limit; "
                                "dp: the dynamic programming schedule for the number of checkpoints in the input "
                                "(evolution programs only); "
                                "random: one random tree, its optimum, every heuristic and every "
                                "profiling strategy (ignores --input); "
                                "experiment: generate random trees, compare the strategies with the optimum "
                                "and write a CSV (needs numpy, ignores --input) "
                                "(default: %(default)s)")
    argParser.add_argument("-i", "--input", default="input.json",
                           help="input json file (default: %(default)s)")
    argParser.add_argument("-o", "--output", default=None,
                           help="output file (default: output.tex, or results.csv for experiment)")

    randomArgs = argParser.add_argument_group("random mode")
    randomArgs.add_argument("--nodes", type=int, default=DEFAULT_OPTIONS["nodes"],
                            help="number of functions, including the root (default: %(default)s)")
    randomArgs.add_argument("--depth", type=float, default=DEFAULT_OPTIONS["depth"],
                            help="-1 favours shallow parents (wide trees), 1 deep parents (chains) "
                                 "(default: %(default)s)")
    randomArgs.add_argument("--width", type=float, default=DEFAULT_OPTIONS["width"],
                            help="-1 favours parents with few children (thin trees), "
                                 "1 parents with many (hubs, stars) (default: %(default)s)")
    randomArgs.add_argument("--max-children", dest="maxChildren", type=int, default=DEFAULT_OPTIONS["maxChildren"],
                            help="most children per function (default: no limit)")
    randomArgs.add_argument("--max-segment-cost", dest="maxSegmentCost", type=int, default=DEFAULT_OPTIONS["maxSegmentCost"],
                            help="largest cost of a segment, each is drawn from 0 to this (default: %(default)s)")
    randomArgs.add_argument("--max-snapshot-cost", dest="maxSnapshotCost", type=int, default=DEFAULT_OPTIONS["maxSnapshotCost"],
                            help="largest snapshot cost, each is drawn from 0 to this "
                                 "(default: same as --max-segment-cost)")
    randomArgs.add_argument("--seed", type=int, default=DEFAULT_OPTIONS["seed"],
                            help="seed to rebuild a tree (default: random, printed)")
    randomArgs.add_argument("--alpha", type=float, default=DEFAULT_OPTIONS["alpha"],
                            help="memory limit between the lowest (0) and highest (1) possible memory "
                                 "(default: %(default)s)")

    experimentArgs = argParser.add_argument_group("experiment mode")
    experimentArgs.add_argument("-t", "--trees", type=int, default=DEFAULT_OPTIONS["trees"],
                                help="trees (seeds) per combination of settings (default: %(default)s)")
    args = argParser.parse_args()

    output = args.output or ("results.csv" if args.mode == "experiment" else "output.tex")
    options = {name: getattr(args, name) for name in DEFAULT_OPTIONS}
    raise SystemExit(main(args.input, output, args.mode, **options))
