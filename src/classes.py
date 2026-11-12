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
    # snapshot: memory needed to store this function's inputs when it is
    # checkpointed. Saving and loading it each cost this much again
    def __init__(self, name, costs=None, snapshot=0):
        self.snapshot = snapshot
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

    # Memory this node holds when it reaches childNode during the reversal: its
    # own segments up to the call, plus everything the earlier children left
    # behind. Those are reversed after childNode, so they are still held
    def calculate_memory_before_child(self, childNode):
        memory_cost = 0

        for i, child in enumerate(self.children):
            memory_cost += self.costs[i]
            if child == childNode:
                break
            memory_cost += child.calculate_memory_held()

        return memory_cost

    def calculate_total_cost(self):
        total_cost = sum(self.costs)
        for child in self.children:
            total_cost += child.calculate_total_cost()

        return total_cost

    # Memory this node leaves held in its caller after it returns: its snapshot
    # when checkpointed, otherwise its whole tape
    def calculate_memory_held(self):
        if self.checkpoint:
            return self.snapshot
        return self.calculate_memory_own_run_cost()

    # Memory cost of this node's own run. A checkpointed subtree below it is
    # left out, but its snapshot is held instead
    def calculate_memory_own_run_cost(self):
        memory_cost = sum(self.costs)
        for child in self.children:
            memory_cost += child.calculate_memory_held()

        return memory_cost

    # Memory cost already held by all the ancestors when this node is reversed
    def calculate_memory_ancestor_cost(self):
        memory_cost = 0
        node = self
        while node.parent:
            memory_cost += node.parent.calculate_memory_before_child(node)
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
