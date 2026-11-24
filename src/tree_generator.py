import csv
import itertools
import math
import random
from functools import partial
from .brute_force import brute_force, find_optimum
from .heuristics import HEURISTICS, run_heuristic
from .profiling import STRATEGIES as PROFILING_STRATEGIES, run_profile
from .classes import funcNode

# name -> function taking (nodes, root, maxMem) and returning
# (feasible, memory, operation cost, combination), for every heuristic and
# every profiling strategy
STRATEGIES = {
    **{name: partial(run_heuristic, heuristic) for name, heuristic in HEURISTICS.items()},
    **{name: partial(run_profile, strategy) for name, strategy in PROFILING_STRATEGIES.items()},
}


DEPTH_RANGE = (-5.0, 3.0)
WIDTH_RANGE = (-5.0, 2.0)
# The brute force roughly quadruples every 2 nodes: about 0.8 s per tree at 16
# and 15 s at 20, so larger sizes make a full run take a day or more
NODE_COUNTS = [8, 12, 16]
# 0 leaves no parent to attach to, and 1 always gives a chain
CHILD_LIMITS = [2, 3, 4, 5, None]
MAX_SEGMENT_COSTS = [1, 10, 20, 50, 100]
MAX_SNAPSHOT_COSTS = [1, 10, 20, 50, 100]
ALPHAS = [0, 0.25, 0.5, 0.75, 1.0]


def scale_bias(u, rawRange):
    low, high = rawRange
    return u * high if u >= 0 else -u * low


# maxSnapshotCost defaults to maxSegmentCost
def generate_tree(n, depthBias=0.0, widthBias = 0.0, maxChildren=None, maxSegmentCost=10,
                  maxSnapshotCost=None, rng=None):
    rng = rng or random.Random()
    if maxSnapshotCost is None:
        maxSnapshotCost = maxSegmentCost
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
        x.costs = [rng.randint(0, maxSegmentCost) for _ in range(len(x.children) + 1)]

    # Snapshots: drawn after the costs, so a seed gives the same shape and
    # costs as before. The root is never checkpointed, so it keeps 0
    for x in nodes[1:]:
        x.snapshot = rng.randint(0, maxSnapshotCost)

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
    "seed", "nodes", "depthSetting", "widthSetting", "maxChildren", "maxSegmentCost", "maxSnapshotCost",
    # tree measurements
    "maxDepth", "maxChildrenFound", "leaves",
    # memory limit
    "minMemory", "maxMemory", "alpha", "memoryLimit",
    # optimum
    "optimumMemory", "optimumCost", "optimumCheckpoints",
    # strategy (a heuristic or a profiling strategy)
    "strategy", "feasible", "memory", "cost", "checkpoints", "costRatio", "isOptimal",
]


# Generate one tree, find its optimum by brute force and run every heuristic
# and profiling strategy, for each alpha. Returns the CSV rows for that tree.
# Top level so worker processes can run it
def experiment_rows(settings):
    n, seed, depthSetting, widthSetting, maxChildren, maxSegmentCost, maxSnapshotCost = settings

    rng = random.Random(seed)
    root, nodes = generate_tree(
        n,
        depthBias=scale_bias(depthSetting, DEPTH_RANGE),
        widthBias=scale_bias(widthSetting, WIDTH_RANGE),
        maxChildren=maxChildren,
        maxSegmentCost=maxSegmentCost,
        maxSnapshotCost=maxSnapshotCost,
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
        "maxSegmentCost": maxSegmentCost,
        "maxSnapshotCost": maxSnapshotCost,
        **measure_tree(root, nodes),
        "minMemory": minMem, "maxMemory": maxMem,
    }

    rows = []
    for alpha in ALPHAS:
        # The limit is never below minMem, so the optimum always exists
        limit = round(minMem + alpha * (maxMem - minMem))
        optMemory, optCost, optCombination = find_optimum(results, limit)

        for name, run in STRATEGIES.items():
            feasible, memory, cost, combination = run(checkpointable, root, limit)

            rows.append({
                **treeRow,
                "alpha": alpha, "memoryLimit": limit,
                "optimumMemory": optMemory, "optimumCost": optCost,
                "optimumCheckpoints": checkpointed_names(checkpointable, optCombination),
                "strategy": name, "feasible": feasible,
                "memory": memory, "cost": cost,
                "checkpoints": checkpointed_names(checkpointable, combination),
                "costRatio": cost / optCost if feasible else "",
                "isOptimal": feasible and cost == optCost,
            })

    return rows


# Generate a tree for every combination of settings and write one CSV row per
# (tree, alpha, strategy). jobs is the number of worker processes (None: one
# per core, 1: run in this process). The rows come out in the same order
# whatever the number of jobs
def generate_random_trees(outputName="results.csv", treesPerSetting=10, jobs=None):
    # Imported here so the random mode runs without numpy
    import numpy as np

    # Plain floats, so the CSV and the workers get the same values as before
    depthSettings = [float(x) for x in np.linspace(-1, 1, 5)]
    widthSettings = [float(x) for x in np.linspace(-1, 1, 5)]

    # Smallest trees first, so a run stopped early still has complete
    # results for the smaller sizes
    tasks = [(n, *rest) for n in NODE_COUNTS
             for rest in itertools.product(
                 range(treesPerSetting), depthSettings, widthSettings, CHILD_LIMITS,
                 MAX_SEGMENT_COSTS, MAX_SNAPSHOT_COSTS)]
    total = len(tasks)

    with open(outputName, "w", newline="") as outFile:
        writer = csv.DictWriter(outFile, fieldnames=CSV_COLUMNS)
        writer.writeheader()

        def write_all(rowLists):
            for done, rows in enumerate(rowLists, 1):
                writer.writerows(rows)
                print(f"\rTree {done}/{total}", end="", flush=True)

        if jobs == 1:
            write_all(map(experiment_rows, tasks))
        else:
            from multiprocessing import Pool
            with Pool(jobs) as pool:
                # Small chunks keep the large trees at the end spread over the workers
                write_all(pool.imap(experiment_rows, tasks, chunksize=4))

    print("\nResults generated")
