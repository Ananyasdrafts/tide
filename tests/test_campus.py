"""Campus graph and calm routing."""

import pytest

from cairn.campus import Campus, Edge, sample_campus


def test_neighbors_and_edges():
    c = sample_campus()
    assert "lobby" in c.nodes
    names = {n for n, _ in c.neighbors("lobby")}
    assert names == {"entrance", "cafeteria", "courtyard"}
    assert c.edge_between("lobby", "cafeteria").sensory == 0.9
    assert c.edge_between("lobby", "nowhere") is None


def test_shortest_route_ignores_sensory_when_weight_zero():
    c = sample_campus()
    # distance only: cafeteria way (10+15+10=35) beats courtyard way (10+18+14=42)
    assert c.route("entrance", "hall_A", sensory_weight=0.0) == ["entrance", "lobby", "cafeteria", "hall_A"]


def test_calm_route_avoids_busy_segments():
    c = sample_campus()
    # with a strong sensory penalty, it takes the quieter courtyard way
    route = c.route("entrance", "hall_A", sensory_weight=3.0)
    assert route == ["entrance", "lobby", "courtyard", "hall_A"]
    assert c.path_sensory(route) < c.path_sensory(["entrance", "lobby", "cafeteria", "hall_A"])


def test_route_cost_and_unknown_nodes():
    c = sample_campus()
    cost = c.route_cost(["entrance", "lobby"], sensory_weight=0.0)
    assert cost == 10.0
    with pytest.raises(KeyError):
        c.route("entrance", "mars")


def test_no_path_raises():
    c = Campus([Edge("a", "b", 1, 0.1), Edge("c", "d", 1, 0.1)])
    with pytest.raises(ValueError):
        c.route("a", "d")
