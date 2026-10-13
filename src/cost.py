def calculate_operation_cost(nodes, root):
    cost = root.calculate_total_cost()
    for node in nodes:
        if node.checkpoint:
            cost += node.calculate_total_cost()

    return cost


def calculate_memory_cost(nodes, root):
    checkpointedNodes = [node for node in nodes if node.checkpoint]
    checkpointedNodes.append(root)

    return max(node.calculate_memory_own_run_cost() + node.calculate_memory_ancestor_cost()
               for node in checkpointedNodes)