def calculate_operation_cost(nodes, root):
    cost = root.calculate_total_cost()
    for node in nodes:
        if node.checkpoint:
            # re-run of the subtree, plus saving and loading its snapshot
            cost += node.calculate_total_cost() + node.snapshot * 2

    return cost


def calculate_memory_cost(nodes, root):
    checkpointedNodes = [node for node in nodes if node.checkpoint]
    checkpointedNodes.append(root)

    return max(node.calculate_memory_own_run_cost() + node.calculate_memory_ancestor_cost()
               for node in checkpointedNodes)