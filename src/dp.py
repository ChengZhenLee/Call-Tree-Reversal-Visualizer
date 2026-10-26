def dp_checkpointing(root, checkpoints):
    children = root.children
    mappedNodes = {}

    # Map the sequence number to the cost of that step
    for i, child in enumerate(children):
        mappedNodes[i + 1] = sum(child.costs)

    table = {}  # (f, t, c): (cost, s)
    schedule = []
    build_table(0, len(children), checkpoints, table, mappedNodes)
    get_schedule(0, len(children), checkpoints, table, schedule)

    visualTable = create_visual_table(table, checkpoints)

    # Position 0 is the root, so the children are numbered from 1 and the
    # checkpoint at split s is child s
    for i, child in enumerate(children, start=1):
        child.set_checkpoint(i in schedule)

    return visualTable


# table[(f, t, c)]: (minimum recompute cost of steps f+1..t, split point s) when
# c checkpoints are available, counting the one at f. s is f when the interval
# is not split
def build_table(f, t, checkpoints, table, mappedNodes):
    # this interval has already been built
    if (f, t, 1) in table:
        return

    # interval of step size 1
    if (t - f) <= 1:
        for c in range(1, checkpoints + 1):
            table[(f, t, c)] = (0, f)
        return

    # Solve every sub-interval first
    for s in range(f + 1, t):
        build_table(f, s, checkpoints, table, mappedNodes)
        build_table(s, t, checkpoints, table, mappedNodes)

    for c in range(1, checkpoints + 1):
        # Only f is stored: re-run from f to reach each step
        if c == 1:
            table[(f, t, c)] = (table[(f, t - 1, c)][0] + sum(mappedNodes[i] for i in range(f + 1, t)), f)
            continue

        # Enough checkpoints to store every state in between
        if c >= t - f - 1:
            table[(f, t, c)] = (sum(mappedNodes[i] for i in range(f + 1, t)), f)
            continue

        # Advance to s and checkpoint it, solve [s, t] with one fewer
        # checkpoint, then solve [f, s] with the one at s freed
        best = None
        bestS = None
        for s in range(f + 1, t):
            cur = (sum(mappedNodes[i] for i in range(f + 1, s + 1))
                   + table[(s, t, c - 1)][0] + table[(f, s, c)][0])
            if best is None or cur < best:
                best = cur
                bestS = s

        table[(f, t, c)] = (best, bestS)


def get_schedule(f, t, c, table, schedule):
    # Enough checkpoints to store every state in between
    if c >= t - f - 1:
        schedule.extend(range(f + 1, t - 1))
        return schedule

    # Only f is stored
    if c == 1:
        return schedule

    s = table[(f, t, c)][1]
    schedule.append(s)
    get_schedule(s, t, c - 1, table, schedule)
    get_schedule(f, s, c, table, schedule)

    return schedule


def create_visual_table(table, checkpoints):
    visual_table = {}

    for (f, t, c), (cost, s) in table.items():
        if (f, t) not in visual_table:
            visual_table[(f, t)] = [None] * checkpoints
        visual_table[(f, t)][c - 1] = (cost, s)

    return visual_table


def check_evolution(nodes, root):
    return all(node.parent is root and len(node.children) == 0 for node in nodes) and sum(root.costs) == 0