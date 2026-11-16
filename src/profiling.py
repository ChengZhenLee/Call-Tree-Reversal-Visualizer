from .cost import calculate_memory_cost, calculate_operation_cost
from .parser import perform_checkpointing


def profile(nodes ,root, maxMem, strategy):
    for node in nodes:
        node.checkpoint = True

    if calculate_memory_cost(nodes, root) > maxMem:
        perform_checkpointing(nodes, [False] * len(nodes))
        return False

    inhibitable = list(nodes)

    while inhibitable:
        candidates = []
        costs = [] # (operation_cost, memory_cost)
        for node in inhibitable:
            node.checkpoint = False
            mem = calculate_memory_cost(nodes, root)
            if mem <= maxMem:
                candidates.append(node)
                costs.append((calculate_operation_cost(nodes, root), mem))
            node.checkpoint = True

        if not candidates:
            break

        inhibitedNode = strategy(costs, candidates)
        inhibitedNode.checkpoint = False
        inhibitable.remove(inhibitedNode)

    return True


def mostRuntimeDecrease(costs, candidates):
    inhibitedIndex = min(range(len(costs)), key=lambda i: costs[i][0])
    return candidates[inhibitedIndex]


def leastMemoryUsage(costs, candidates):
    inhibitedIndex = min(range(len(costs)), key=lambda i: costs[i][1])
    return candidates[inhibitedIndex]


# name -> strategy taking (costs, candidates)
STRATEGIES = {
    "Most runtime decrease": mostRuntimeDecrease,
    "Least memory usage": leastMemoryUsage,
}


# Run one strategy and leave its checkpoints set.
# Returns (feasible, memory, operation cost, combination)
def run_profile(strategy, nodes, root, maxMem):
    feasible = profile(nodes, root, maxMem, strategy)

    return (feasible,
            calculate_memory_cost(nodes, root),
            calculate_operation_cost(nodes, root),
            tuple(node.checkpoint for node in nodes))