import random

from .dp import dp_checkpointing, dp_costs, check_evolution
from .cost import calculate_operation_cost, calculate_memory_cost
from .heuristics import HEURISTICS, run_heuristic
from .latex import draw_tree, latex_header, latex_footer
from .parser import (parse_json, parse_functions, permute, perform_checkpointing,
                     generate_forward_tree, generate_backward_tree)


# Draw the trees for the current checkpoint setting, titled with the costs.
# stats is a list of (label, value) pairs shown after the checkpoints, and
# defaults to the call tree operation and memory cost
def draw_current_setting(checkpointable, root, prefix="", stats=None):
    if stats is None:
        stats = [("Operation cost", calculate_operation_cost(checkpointable, root)),
                 ("Memory cost", calculate_memory_cost(checkpointable, root))]

    checkpointed = [n.name for n in checkpointable if n.checkpoint]
    title = prefix + "Checkpointed: " + (", ".join(checkpointed) or "none")
    title = title.replace("_", r"\_")
    title += "".join(rf" \quad {label}: {value}" for label, value in stats)

    trees = [generate_forward_tree(root), generate_backward_tree(root)]
    return draw_tree(trees, title)


# Every combination of checkpoints
def enumerate_all(checkpointable, root, limits):
    parts = []
    for combination in permute(len(checkpointable)):
        perform_checkpointing(checkpointable, combination)
        parts.append(draw_current_setting(checkpointable, root))

    return parts


# One picture per heuristic, each starting from no checkpoints
def run_heuristics(checkpointable, root, limits):
    parts = []
    for name, heuristic in HEURISTICS.items():
        feasible, memory, cost, _ = run_heuristic(heuristic, checkpointable, root, limits["memory"])

        status = "" if feasible else "(over memory limit) "
        stats = [("Operation cost", cost),
                 ("Memory cost", memory),
                 ("Memory limit", limits["memory"])]
        parts.append(draw_current_setting(checkpointable, root, f"{name}: {status}", stats))

    return parts


# The dynamic programming schedule for the number of checkpoints in the input,
# for evolution programs
def run_dp(checkpointable, root, limits):
    if not check_evolution(checkpointable, root):
        raise ValueError("dp mode needs an evolution program: a root with no cost of its own "
                         "whose children are all leaves")

    checkpoints = limits.get("checkpoints")
    if not isinstance(checkpoints, int) or checkpoints < 1:
        raise ValueError('dp mode needs a "checkpoints" entry in "limits": a whole number of at least 1')

    visualTable = dp_checkpointing(root, checkpoints)

    # The call tree cost functions don't describe the DP schedule, so use its own costs
    operationCost, peakMemory = dp_costs(root, visualTable, checkpoints)
    stats = [("Operation cost", operationCost), ("Checkpoint limit", checkpoints)]

    status = ""
    if "memory" in limits:
        stats.append(("Memory limit", limits["memory"]))
        if peakMemory > limits["memory"]:
            status = "(over memory limit) "
    stats.append(("Peak memory", peakMemory))

    return [draw_current_setting(checkpointable, root, f"DP: {status}", stats)]


# Write the pictures to one LaTeX file
def write_latex(outputName, parts):
    with open(outputName, 'w') as outFile:
        outFile.write("\n".join([latex_header()] + parts + [latex_footer()]))


# Turn a drawing function (checkpointable, root, limits) -> LaTeX parts into a
# mode: read the call tree from the input json and write the pictures to one
# LaTeX file
def latex_mode(draw):
    def run(inputName, outputName, options):
        functionsJson, limits = parse_json(inputName)
        nodes, root = parse_functions(functionsJson)

        # the root is never checkpointed
        checkpointable = [n for n in nodes if n is not root]

        write_latex(outputName, draw(checkpointable, root, limits))

    return run


# Generate one random tree, find its optimum by brute force under the memory
# limit set by alpha, and draw the optimum next to every heuristic. Ignores the
# input file
def run_random(inputName, outputName, options):
    from .brute_force import brute_force, find_optimum
    from .tree_generator import generate_tree, scale_bias, DEPTH_RANGE, WIDTH_RANGE

    n, depth, width = options["nodes"], options["depth"], options["width"]
    maxChildren, maxSegmentCost, alpha = options["maxChildren"], options["maxSegmentCost"], options["alpha"]
    if n < 2:
        raise ValueError("random mode needs at least 2 nodes")
    if not (-1 <= depth <= 1 and -1 <= width <= 1):
        raise ValueError("the depth and width settings must be between -1 and 1")
    if not 0 <= alpha <= 1:
        raise ValueError("alpha must be between 0 and 1")
    if maxChildren is not None and maxChildren < 1:
        raise ValueError("the child limit must be at least 1")
    if maxSegmentCost < 1:
        raise ValueError("the largest cost must be at least 1")

    # Pick a seed when none is given, and show it so the tree can be rebuilt
    seed = options["seed"]
    if seed is None:
        seed = random.randrange(2**32)
    print(f"Seed: {seed}")

    root, nodes = generate_tree(
        n,
        depthBias=scale_bias(depth, DEPTH_RANGE),
        widthBias=scale_bias(width, WIDTH_RANGE),
        maxChildren=maxChildren,
        maxSegmentCost=maxSegmentCost,
        rng=random.Random(seed),
    )

    # The root is never checkpointed. generate_tree puts it first
    checkpointable = nodes[1:]

    minMem, maxMem, results = brute_force(checkpointable, root)
    limit = minMem + alpha * (maxMem - minMem)
    optMemory, optCost, optCombination = find_optimum(results, limit)

    settings = [("Seed", seed), ("Nodes", n), ("Depth", depth), ("Width", width),
                ("Child limit", "none" if maxChildren is None else maxChildren),
                ("Largest segment cost", maxSegmentCost), ("Alpha", alpha),
                ("Memory range", f"{minMem}--{maxMem}"), ("Memory limit", f"{limit:g}")]
    parts = [r"\subsection*{Random tree}" + "\n"
             + r" \quad ".join(f"{label}: {value}" for label, value in settings) + "\n" + r"\bigskip" + "\n"]

    perform_checkpointing(checkpointable, optCombination)
    parts.append(draw_current_setting(checkpointable, root, "Optimum: ",
                                      [("Operation cost", optCost), ("Memory cost", optMemory)]))

    for name, heuristic in HEURISTICS.items():
        feasible, memory, cost, _ = run_heuristic(heuristic, checkpointable, root, limit)

        status = "" if feasible else "(over memory limit) "
        stats = [("Operation cost", cost), ("Memory cost", memory)]
        if feasible:
            stats.append(("Cost ratio", f"{cost / optCost:.2f}"))
        parts.append(draw_current_setting(checkpointable, root, f"{name}: {status}", stats))

    write_latex(outputName, parts)


# Generate random trees, compare the heuristics with the optimum and write a CSV.
# Ignores the input file. Imported here so the other modes run without numpy
def run_experiment(inputName, outputName, options):
    from .tree_generator import generate_random_trees
    generate_random_trees(outputName, options["trees"])


# Every mode takes (inputName, outputName, options), where options holds the
# command line settings:
#   "enumerate": every possible combination of checkpoints
#   "heuristic": only the result of each heuristic above, under the memory limit
#   "dp": the dynamic programming schedule for the "checkpoints" in the input (evolution programs only)
#   "random": one random tree, its optimum and every heuristic
#   "experiment": random trees compared against the optimum, written to a CSV
MODES = {
    "enumerate": latex_mode(enumerate_all),
    "heuristic": latex_mode(run_heuristics),
    "dp": latex_mode(run_dp),
    "random": run_random,
    "experiment": run_experiment,
}
