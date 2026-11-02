from .dp import dp_checkpointing, dp_costs, check_evolution
from .cost import calculate_operation_cost, calculate_memory_cost
from .heuristics import greedyCheckpointing, greedyCheckpointRemoval
from .latex import draw_tree
from .parser import permute, perform_checkpointing, generate_forward_tree, generate_backward_tree

# name shown in the title -> heuristic taking (nodes, root, maxMemory)
HEURISTICS = {
    "Greedy checkpointing increasing": lambda nodes, root, maxMem:
        greedyCheckpointing(nodes, root, maxMem, increasing=True),
    "Greedy checkpointing decreasing": lambda nodes, root, maxMem:
        greedyCheckpointing(nodes, root, maxMem, increasing=False),
    "Greedy checkpoint removal increasing": lambda nodes, root, maxMem:
        greedyCheckpointRemoval(nodes, root, maxMem, increasing=True),
    "Greedy checkpoint removal decreasing": lambda nodes, root, maxMem:
        greedyCheckpointRemoval(nodes, root, maxMem, increasing=False),
}


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
        perform_checkpointing(checkpointable, [False] * len(checkpointable))
        feasible = heuristic(checkpointable, root, limits["memory"])

        status = "" if feasible else "(over memory limit) "
        stats = [("Operation cost", calculate_operation_cost(checkpointable, root)),
                 ("Memory cost", calculate_memory_cost(checkpointable, root)),
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


# what to draw:
#   "enumerate": every possible combination of checkpoints
#   "heuristic": only the result of each heuristic above, under the memory limit
#   "dp": the dynamic programming schedule for the "checkpoints" in the input (evolution programs only)
MODES = {
    "enumerate": enumerate_all,
    "heuristic": run_heuristics,
    "dp": run_dp,
}
