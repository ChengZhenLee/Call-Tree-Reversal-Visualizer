import argparse

from src.latex import latex_header, latex_footer
from src.modes import MODES
from src.parser import parse_json, parse_functions


def main(inputName="input.json", outputName="output.tex", mode="enumerate"):
    # read the input.json file
    functionsJson, limits = parse_json(inputName)

    # parse the loaded data into classes
    nodes, root = parse_functions(functionsJson)

    # the root is never checkpointed
    checkpointable = [n for n in nodes if n is not root]

    # build the trees for the chosen mode and write them all to a single latex file
    parts = [latex_header()]
    parts += MODES[mode](checkpointable, root, limits)
    parts.append(latex_footer())

    # Write to the output file
    with open(outputName, 'w') as outFile:
        outFile.write("\n".join(parts))

    return 0


if __name__ == "__main__":
    argParser = argparse.ArgumentParser(description="Draw call tree reversals for checkpointing choices.")
    argParser.add_argument("-m", "--mode", choices=list(MODES), default="enumerate",
                           help="enumerate: every combination of checkpoints; "
                                "heuristic: the result of each heuristic under the memory limit "
                                "(default: %(default)s)")
    argParser.add_argument("-i", "--input", default="input.json",
                           help="input json file (default: %(default)s)")
    argParser.add_argument("-o", "--output", default="output.tex",
                           help="output latex file (default: %(default)s)")
    args = argParser.parse_args()

    raise SystemExit(main(args.input, args.output, args.mode))
