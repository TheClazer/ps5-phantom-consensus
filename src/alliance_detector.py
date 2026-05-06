"""
Alliance detection via bidirectional trust graph + connected components.

Edge exists ONLY if score(A→B) >= threshold AND score(B→A) >= threshold.
This is the False Friend fix: asymmetric trust never forms an alliance.
"""
from __future__ import annotations
from src.models import RelationshipMatrix


def detect_alliances(
    matrix: RelationshipMatrix,
    safe_rep_ids: list[str],
    alliance_min_threshold: float,
) -> list[list[str]]:
    """
    Returns sorted list of alliances (each alliance is a sorted list of rep_ids).
    Only includes alliances with >= 2 members.
    """
    if len(safe_rep_ids) < 2:
        return []

    # Build adjacency list (undirected, bidirectional check)
    adj: dict[str, set[str]] = {rid: set() for rid in safe_rep_ids}

    for i, a in enumerate(safe_rep_ids):
        for b in safe_rep_ids[i + 1 :]:
            score_ab = matrix.get_score(a, b)
            score_ba = matrix.get_score(b, a)
            if score_ab >= alliance_min_threshold and score_ba >= alliance_min_threshold:
                adj[a].add(b)
                adj[b].add(a)

    # Connected components via BFS (no external dependency)
    visited: set[str] = set()
    alliances: list[list[str]] = []

    for start in safe_rep_ids:
        if start in visited:
            continue
        component: list[str] = []
        queue = [start]
        while queue:
            node = queue.pop(0)
            if node in visited:
                continue
            visited.add(node)
            component.append(node)
            queue.extend(adj[node] - visited)

        if len(component) >= 2:
            alliances.append(sorted(component))

    return sorted(alliances)
