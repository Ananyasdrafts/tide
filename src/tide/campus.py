"""The campus as a graph, and calm routing over it.

A campus is locations (nodes) joined by paths (edges). Each path has a distance and a
sensory load (how loud, crowded, and visually busy it is, on a 0..1 scale). Routing
minimises distance plus a penalty on sensory load, so Tide can prefer a calmer way even
when it is a little longer. The penalty weight is how much the person wants to trade
distance for calm.
"""

from __future__ import annotations

import heapq
from dataclasses import dataclass, field

INF = float("inf")


@dataclass(frozen=True)
class Edge:
    a: str
    b: str
    distance: float
    sensory: float  # 0..1 sensory load of this segment

    def other(self, node: str) -> str:
        return self.b if node == self.a else self.a


@dataclass
class Campus:
    edges: list[Edge] = field(default_factory=list)

    def __post_init__(self) -> None:
        self._adj: dict[str, list[Edge]] = {}
        for e in self.edges:
            self._adj.setdefault(e.a, []).append(e)
            self._adj.setdefault(e.b, []).append(e)

    @property
    def nodes(self) -> set[str]:
        return set(self._adj)

    def neighbors(self, node: str) -> list[tuple[str, Edge]]:
        return [(e.other(node), e) for e in self._adj.get(node, [])]

    def edge_between(self, a: str, b: str) -> Edge | None:
        for e in self._adj.get(a, []):
            if e.other(a) == b:
                return e
        return None

    @staticmethod
    def edge_cost(e: Edge, sensory_weight: float) -> float:
        """Distance, inflated by the sensory load. Higher weight = avoid busy paths more."""
        return e.distance * (1.0 + sensory_weight * e.sensory)

    def route(self, start: str, goal: str, sensory_weight: float = 1.0) -> list[str]:
        """Least-cost path from start to goal as a list of nodes (Dijkstra)."""
        if start not in self._adj or goal not in self._adj:
            raise KeyError(f"unknown node: {start if start not in self._adj else goal}")
        dist: dict[str, float] = {start: 0.0}
        prev: dict[str, str] = {}
        pq: list[tuple[float, str]] = [(0.0, start)]
        while pq:
            d, u = heapq.heappop(pq)
            if u == goal:
                break
            if d > dist.get(u, INF):
                continue
            for v, e in self.neighbors(u):
                nd = d + self.edge_cost(e, sensory_weight)
                if nd < dist.get(v, INF):
                    dist[v] = nd
                    prev[v] = u
                    heapq.heappush(pq, (nd, v))
        if goal not in dist:
            raise ValueError(f"no path from {start} to {goal}")
        path = [goal]
        while path[-1] != start:
            path.append(prev[path[-1]])
        return path[::-1]

    def route_cost(self, path: list[str], sensory_weight: float = 1.0) -> float:
        total = 0.0
        for a, b in zip(path, path[1:]):
            e = self.edge_between(a, b)
            if e is None:
                raise ValueError(f"no edge between {a} and {b}")
            total += self.edge_cost(e, sensory_weight)
        return total

    def path_sensory(self, path: list[str]) -> float:
        """Distance-weighted mean sensory load along a path (how calm the route is)."""
        load, dist = 0.0, 0.0
        for a, b in zip(path, path[1:]):
            e = self.edge_between(a, b)
            load += e.sensory * e.distance
            dist += e.distance
        return load / dist if dist else 0.0


def sample_campus() -> Campus:
    """A small example campus: from the entrance to a lecture hall, a busy short way through
    the cafeteria, and a calmer slightly-longer way through the courtyard."""
    return Campus([
        Edge("entrance", "lobby", 10, 0.3),
        Edge("lobby", "cafeteria", 15, 0.9),   # loud, crowded
        Edge("cafeteria", "hall_A", 10, 0.5),
        Edge("lobby", "courtyard", 18, 0.1),    # quiet, longer
        Edge("courtyard", "hall_A", 14, 0.2),
        Edge("hall_A", "hall_B", 8, 0.3),
    ])
