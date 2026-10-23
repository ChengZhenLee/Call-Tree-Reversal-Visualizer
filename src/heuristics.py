from .cost import calculate_memory_cost
from .parser import perform_checkpointing


def greedyCheckpointing(nodes, root, maxMem, increasing=True):
    ordered = sorted(nodes, key=lambda n: n.calculate_memory_own_run_cost(), reverse=not increasing)

    for node in ordered:
        before = calculate_memory_cost(nodes, root)
        if before <= maxMem:
            break
        node.set_checkpoint(True)
        if calculate_memory_cost(nodes, root) >= before:
            node.set_checkpoint(False)

    return calculate_memory_cost(nodes, root) <= maxMem



def greedyCheckpointRemoval(nodes, root, maxMem, increasing=True):
    perform_checkpointing(nodes, [True] * len(nodes))

    if calculate_memory_cost(nodes, root) > maxMem:
        perform_checkpointing(nodes, [False] * len(nodes))
        return False

    ordered = sorted(nodes, key=lambda n: n.calculate_memory_own_run_cost(), reverse=not increasing)
    
    for node in ordered:
        node.set_checkpoint(False)
        if calculate_memory_cost(nodes, root) > maxMem:
            node.set_checkpoint(True)
            break

    return True
