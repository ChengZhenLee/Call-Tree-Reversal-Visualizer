import sys

from src.cost import calculate_operation_cost, calculate_memory_cost
from src.latex import latex_header, latex_footer, draw_tree
from src.parser import (parse_json, parse_functions, permute, perform_checkpointing,
                        generate_forward_tree, generate_backward_tree)


def main(inputName="input.json", outputName="output.tex"):
    # read the input.json file
    functionsJson = parse_json(inputName)

    # parse the loaded data into classes
    nodes, root = parse_functions(functionsJson)

    # the root is never checkpointed
    checkpointable = [n for n in nodes if n is not root]

    # for each combination of the checkpoints, build the trees
    # and write them all to a single latex file
    parts = [latex_header()]
    for combination in permute(len(checkpointable)):
        perform_checkpointing(checkpointable, combination)

        checkpointed = [n.name for n in checkpointable if n.checkpoint]
        title = "Checkpointed: " + (", ".join(checkpointed) or "none")
        title = title.replace("_", r"\_")
        title += f" \\quad Operation cost: {calculate_operation_cost(checkpointable, root)}"
        title += f" \\quad Memory cost: {calculate_memory_cost(checkpointable, root)}"

        trees = [generate_forward_tree(root), generate_backward_tree(root)]
        parts.append(draw_tree(trees, title))

    parts.append(latex_footer())

    # Write to the output file
    with open(outputName, 'w') as outFile:
        outFile.write("\n".join(parts))

    return 0


if __name__ == "__main__":
    main()