import csv
import itertools
import math
import random
from .brute_force import brute_force, find_optimum
from .heuristics import HEURISTICS, run_heuristic
from .classes import funcNode


DEPTH_RANGE = (-5.0, 3.0)
WIDTH_RANGE = (-5.0, 2.0)
# The brute force roughly quadruples every 2 nodes: about 0.8 s per tree at 16
# and 15 s at 20, so larger sizes make a full run take a day or more
NODE_COUNTS = [8, 12, 16]
# 0 leaves no parent to attach to, and 1 always gives a chain
CHILD_LIMITS = [2, 3, 4, 5, None]
MAX_COSTS = [1, 10, 20, 50, 100]
ALPHAS = [0, 0.25, 0.5, 0.75, 1.0]


def scale_bias(u, rawRange):
    low, high = rawRange
    return u * high if u >= 0 else -u * low


def generate_tree(n, depthBias=0.0, widthBias = 0.0, maxChildren=None, maxCost=10, rng=None):
    rng = rng or random.Random()
    root = funcNode("0")
    nodes = [root]
    depth = {root: 0}

    # Shape: attach each new node to an existing one.
    # depthBias > 0 favours deep parents, < 0 favours shallow ones
    for i in range(1, n):
        candidates = [x for x in nodes
                      if maxChildren is None or len(x.children) < maxChildren]
        scores = [depthBias * depth[x] + widthBias * math.log(len(x.children) + 1) for x in candidates]
        top = max(scores)
        weights = [math.exp(s - top) for s in scores]
        parent = rng.choices(candidates, weights)[0]

        child = funcNode(str(i))
        parent.add_child(child)
        child.set_parent(parent)
        depth[child] = depth[parent] + 1
        nodes.append(child)

    # Costs: one segment before, between and after the children
    for x in nodes:
        x.costs = [rng.randint(1, maxCost) for _ in range(len(x.children) + 1)]

    return root, nodes


# Shape measurements of a generated tree, for the analysis
def measure_tree(root, nodes):
    depth = {root: 0}
    for node in nodes:
        for child in node.children:
            depth[child] = depth[node] + 1

    return {
        "maxDepth": max(depth.values()),
        "maxChildrenFound": max(len(node.children) for node in nodes),
        "leaves": sum(1 for node in nodes if not node.children),
    }


# Names of the checkpointed nodes in a combination, separated by spaces
def checkpointed_names(nodes, combination):
    return " ".join(node.name for node, checkpoint in zip(nodes, combination) if checkpoint)


CSV_COLUMNS = [
    # tree settings
    "seed", "nodes", "depthSetting", "widthSetting", "maxChildren", "maxCost",
    # tree measurements
    "maxDepth", "maxChildrenFound", "leaves",
    # memory limit
    "minMemory", "maxMemory", "alpha", "memoryLimit",
    # optimum
    "optimumMemory", "optimumCost", "optimumCheckpoints",
    # heuristic
    "heuristic", "feasible", "memory", "cost", "checkpoints", "costRatio", "isOptimal",
]


# Generate a tree for every combination of settings, find the optimum by brute
# force and run every heuristic, for each alpha. Writes one CSV row per
# (tree, alpha, heuristic)
def generate_random_trees(outputName="results.csv", treesPerSetting=10):
    # Imported here so the random mode runs without numpy
    import numpy as np

    depthSettings = np.linspace(-1, 1, 5)
    widthSettings = np.linspace(-1, 1, 5)

    total = (treesPerSetting * len(depthSettings) * len(widthSettings)
             * len(NODE_COUNTS) * len(CHILD_LIMITS) * len(MAX_COSTS))
    done = 0

    with open(outputName, "w", newline="") as outFile:
        writer = csv.DictWriter(outFile, fieldnames=CSV_COLUMNS)
        writer.writeheader()

        # Smallest trees first, so a run stopped early still has complete
        # results for the smaller sizes
        for n in NODE_COUNTS:
            for seed, depthSetting, widthSetting, maxChildren, maxCost in itertools.product(
                    range(treesPerSetting), depthSettings, widthSettings, CHILD_LIMITS, MAX_COSTS):
                done += 1
                print(f"\rTree {done}/{total}", end="", flush=True)

                rng = random.Random(seed)
                root, nodes = generate_tree(
                    n,
                    depthBias=scale_bias(depthSetting, DEPTH_RANGE),
                    widthBias=scale_bias(widthSetting, WIDTH_RANGE),
                    maxChildren=maxChildren,
                    maxCost=maxCost,
                    rng=rng,
                )

                # The root is never checkpointed. generate_tree puts it first
                checkpointable = nodes[1:]

                # Brute force once per tree, then reuse the results for every alpha
                minMem, maxMem, results = brute_force(checkpointable, root)

                treeRow = {
                    "seed": seed, "nodes": n,
                    "depthSetting": depthSetting, "widthSetting": widthSetting,
                    "maxChildren": "none" if maxChildren is None else maxChildren,
                    "maxCost": maxCost,
                    **measure_tree(root, nodes),
                    "minMemory": minMem, "maxMemory": maxMem,
                }

                for alpha in ALPHAS:
                    # The limit is never below minMem, so the optimum always exists
                    limit = minMem + alpha * (maxMem - minMem)
                    optMemory, optCost, optCombination = find_optimum(results, limit)

                    for name, heuristic in HEURISTICS.items():
                        feasible, memory, cost, combination = run_heuristic(
                            heuristic, checkpointable, root, limit)

                        writer.writerow({
                            **treeRow,
                            "alpha": alpha, "memoryLimit": limit,
                            "optimumMemory": optMemory, "optimumCost": optCost,
                            "optimumCheckpoints": checkpointed_names(checkpointable, optCombination),
                            "heuristic": name, "feasible": feasible,
                            "memory": memory, "cost": cost,
                            "checkpoints": checkpointed_names(checkpointable, combination),
                            "costRatio": cost / optCost if feasible else "",
                            "isOptimal": feasible and cost == optCost,
                        })

    print("Results generated")