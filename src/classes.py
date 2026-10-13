from enum import Enum


class ArrowMode(Enum):
    adjointForward = 1
    adjointBackward = 2
    primalForward = 3
    primalBackward = 4
    save = 5
    load = 6


class VisualMode(Enum):
    forward = 1
    backward = 2


class funcNode:
    def __init__(self, name, costs=None):
        self.name = name
        self.parent = None
        self.children = []
        self.costs = costs or []
        self.cumulative_cost = []
        self.checkpoint = False

    def set_parent(self, node):
        self.parent = node

    def add_child(self, node):
        self.children.append(node)

    def calculate_cumulative_cost(self, childNode):
        cumulative_cost = 0

        for i in range(len(self.children)):
            cumulative_cost += self.costs[i]
            if self.children[i] == childNode:
                break

        return cumulative_cost

    def calculate_total_cost(self):
        total_cost = sum(self.costs)
        for child in self.children:
            total_cost += child.calculate_total_cost()

        return total_cost

    # Memory cost of this node's own run, leaving out every checkpointed
    # subtree below it
    def calculate_memory_own_run_cost(self):
        memory_cost = sum(self.costs)
        for child in self.children:
            if not child.checkpoint:
                memory_cost += child.calculate_memory_own_run_cost()

        return memory_cost

    # Memory cost already held by all the ancestors before they call down to this node
    def calculate_memory_ancestor_cost(self):
        memory_cost = 0
        node = self
        while node.parent:
            memory_cost += node.parent.calculate_cumulative_cost(node)
            node = node.parent

        return memory_cost

    def set_checkpoint(self, checkpoint):
        self.checkpoint = checkpoint

            
class visualNode:
    def __init__(self, funcNode):
        self.name = funcNode.name
        self.arrowModes = []
        self.parent = None
        self.children = []

    def set_parent(self, node):
        self.parent = node

    def add_child(self, node):
        self.children.append(node)

    def add_children(self, nodes):
        for node in nodes:
            self.add_child(node)

    def add_arrow_mode(self, arrowMode):
        self.arrowModes.append(arrowMode)
