from .parser import permute, perform_checkpointing
from .cost import calculate_memory_cost, calculate_operation_cost


# Try every checkpoint combination of the nodes (leave the root out) and record
# (memory, operation cost, combination) for each one.
# Returns the lowest memory, the highest memory and every result, so the optimum
# for any memory limit can be found without running this again
def brute_force(nodes, root):
    results = []
    for combination in permute(len(nodes)):
        perform_checkpointing(nodes, combination)
        results.append((calculate_memory_cost(nodes, root),
                        calculate_operation_cost(nodes, root),
                        combination))

    # Reset tree checkpointing
    perform_checkpointing(nodes, [False] * len(nodes))

    minMem = min(memory for memory, _, _ in results)
    maxMem = max(memory for memory, _, _ in results)
    return minMem, maxMem, results


# The cheapest combination that fits in the memory limit, as
# (memory, operation cost, combination) like the results, or None when nothing fits.
# Ties on cost go to the one using less memory
def find_optimum(results, memoryLimit):
    feasible = [r for r in results if r[0] <= memoryLimit]
    if not feasible:
        return None

    return min(feasible, key=lambda r: (r[1], r[0]))
