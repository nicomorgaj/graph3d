import unittest

import numpy as np

from graph3d.layout import compute_layout, group_communities
from graph3d.loader import build_areas, load_graph

from .helpers import TempDir, make_graph, write_graph


def prepare(**kwargs):
    with TempDir() as tmp:
        graph = load_graph(write_graph(tmp, make_graph(**kwargs)))
    areas, node_area = build_areas(graph)
    node_comm, names, comm_area = group_communities(graph, node_area)
    return graph, areas, node_area, node_comm, names, comm_area


class GroupCommunitiesTest(unittest.TestCase):
    def test_uses_the_communities_of_the_graph(self):
        _, _, _, node_comm, names, comm_area = prepare()
        self.assertEqual(len(set(node_comm.tolist())), 6)
        self.assertEqual(len(names), 6)
        self.assertEqual(len(comm_area), 6)

    def test_every_area_becomes_a_community_when_the_graph_has_none(self):
        _, areas, _, node_comm, _, _ = prepare(communities=False)
        self.assertEqual(len(set(node_comm.tolist())), len(areas))

    def test_community_name_is_its_most_connected_node(self):
        graph, _, _, node_comm, names, _ = prepare()
        for community, name in enumerate(names):
            members = [i for i, c in enumerate(node_comm) if c == community]
            labels = {graph.nodes[i]["label"] for i in members}
            self.assertIn(name, labels)


class ComputeLayoutTest(unittest.TestCase):
    def layout(self, seed=7, **kwargs):
        graph, areas, _, node_comm, _, comm_area = prepare(**kwargs)
        return compute_layout(len(graph.nodes), graph.edges, node_comm, comm_area, len(areas), seed=seed), node_comm

    def test_returns_finite_3d_positions_for_every_node(self):
        (positions, radius), _ = self.layout()
        self.assertEqual(positions.shape, (60, 3))
        self.assertTrue(np.isfinite(positions).all())
        self.assertGreater(radius, 0)

    def test_same_seed_gives_the_same_drawing(self):
        (a, _), _ = self.layout(seed=11)
        (b, _), _ = self.layout(seed=11)
        np.testing.assert_allclose(a, b)

    def test_different_seed_changes_the_drawing(self):
        (a, _), _ = self.layout(seed=1)
        (b, _), _ = self.layout(seed=2)
        self.assertFalse(np.allclose(a, b))

    def test_nodes_of_a_community_are_closer_than_random_pairs(self):
        (positions, _), node_comm = self.layout()
        rng = np.random.default_rng(0)
        same, other = [], []
        for _ in range(600):
            i, j = rng.integers(0, 60, 2)
            if i == j:
                continue
            distance = np.linalg.norm(positions[i] - positions[j])
            (same if node_comm[i] == node_comm[j] else other).append(distance)
        self.assertLess(np.mean(same), np.mean(other))

    def test_handles_degenerate_graphs(self):
        one = compute_layout(1, [], np.array([0]), [0], 1)
        self.assertEqual(one[0].shape, (1, 3))
        two = compute_layout(2, [], np.array([0, 1]), [0, 0], 1)
        self.assertTrue(np.isfinite(two[0]).all())
        empty = compute_layout(0, [], np.array([], dtype=np.int64), [], 1)
        self.assertEqual(empty[0].shape, (0, 3))


if __name__ == "__main__":
    unittest.main()
