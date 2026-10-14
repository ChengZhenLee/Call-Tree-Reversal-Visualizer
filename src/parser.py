import json
from itertools import product
from .classes import funcNode, visualNode, ArrowMode


# Parse the json into the appropriate classes
def parse_json(fileName):
    with open(fileName, 'r') as inFile:
        functionsJson = json.load(inFile)["functions"]

    return functionsJson


# Populate the function classes with parent and children
def parse_functions(functionsJson):
    # Create all nodes, stored as a dictionary
    nodes = {
        name: funcNode(name, desc["cost"])
        for name, desc in functionsJson.items()
    }

    # link parents and children
    for name, desc in functionsJson.items():
        parent = nodes[name]
        for childName in desc["children"]:
            child = nodes[childName]
            parent.add_child(child)
            child.set_parent(parent)

    # There should only be one root
    root = [n for n in nodes.values() if not n.parent][0]
    return nodes.values(), root


# returns all combinations of checkpoint setting
def permute(size):
    return list(product([True, False], repeat=size))


# checkpoint the functions depending on the permutations
def perform_checkpointing(nodes, combination):
    for index, node in enumerate(nodes):
        node.set_checkpoint(combination[index])


# Generate a visual nodes
def generate_visual_node(funcNode, modes):
    node = visualNode(funcNode)

    for mode in modes:
        node.add_arrow_mode(mode)

    return node


# Recursively generate the node tree
# returns the forward node and backward node
def generate_visual_tree(curNode, primal=False):
    pass


# Generate the forward pass branch
def generate_forward_tree(curNode, primal=False, backward=False):
    forwardNode = visualNode(curNode)
    checkpoint = curNode.checkpoint

    # backward=True means this node is being reloaded in the backward pass;
    # it runs adjoint forward, so its children are not primal
    if backward:
        forwardNode.add_arrow_mode(ArrowMode.load)
        forwardNode.add_arrow_mode(ArrowMode.adjointForward)
        childPrimal = False

    elif primal:
        forwardNode.add_arrow_mode(ArrowMode.primalForward)
        childPrimal = True

    elif checkpoint:
        forwardNode.add_arrow_mode(ArrowMode.save)
        forwardNode.add_arrow_mode(ArrowMode.primalForward)
        childPrimal = True

    else:
        forwardNode.add_arrow_mode(ArrowMode.adjointForward)
        childPrimal = False

    # descendants follow the normal forward rules
    forwardNode.add_children([
        generate_forward_tree(child, childPrimal)
        for child in curNode.children
    ])

    return forwardNode


# Generate the backward pass branch
def generate_backward_tree(curNode):
    backwardNode = visualNode(curNode)
    backwardNode.add_arrow_mode(ArrowMode.adjointBackward)

    # reverse the sequence of children
    funcChildren = curNode.children[::-1]
    children = []

    # Create the children's visual nodes
    for child in funcChildren:
        if child.checkpoint and not child.children:
            merged = visualNode(child)
            merged.add_arrow_mode(ArrowMode.load)
            merged.add_arrow_mode(ArrowMode.adjointForward)
            merged.add_arrow_mode(ArrowMode.adjointBackward)
            children.append(merged)
        else:
            if child.checkpoint:
                children.append(generate_forward_tree(child, primal=False, backward=True))
            children.append(generate_backward_tree(child))

    backwardNode.add_children(children)

    return backwardNode