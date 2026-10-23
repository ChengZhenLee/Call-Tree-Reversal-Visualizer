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


# Draw the trees for the current checkpoint setting, titled with the costs
def draw_current_setting(checkpointable, root, prefix=""):
    checkpointed = [n.name for n in checkpointable if n.checkpoint]
    title = prefix + "Checkpointed: " + (", ".join(checkpointed) or "none")
    title = title.replace("_", r"\_")
    title += f" \quad Operation cost: {calculate_operation_cost(checkpointable, root)}"
    title += f" \quad Memory cost: {calculate_memory_cost(checkpointable, root)}"

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
        parts.append(draw_current_setting(checkpointable, root, f"{name}: {status}"))

    return parts


# what to draw:
#   "enumerate": every possible combination of checkpoints
#   "heuristic": only the result of each heuristic above, under the memory limit
MODES = {
    "enumerate": enumerate_all,
    "heuristic": run_heuristics,
}
