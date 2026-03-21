import queue
import numpy as np
import math

"""
TODO:
    use bezier curves for more natural looking lines
    handle shapes without ends
"""

class PixelNode:
    def __init__(self, pos):
        self.pos: tuple[int, int] = pos
        self.neighbours: list[PixelNode] = []
        self.is_end = False
        self.cluster: set[PixelNode] = set()
        self.cluster.add(self)
        self.dom = self

    def px_dom(self):
        max_len = max([len(px.neighbours) for px in self.cluster])
        candidates = [px for px in self.cluster if len(px.neighbours) == max_len]

        if len(candidates) == 1:
            return candidates[0]

        min_x = min([px.pos[0] for px in candidates])
        candidates = [px for px in self.cluster if px.pos[0] == min_x]

        if len(candidates) == 1:
            return candidates[0]

        min_y = min([px.pos[1] for px in candidates])
        candidates = [px for px in self.cluster if px.pos[1] == min_y]
        return candidates[0]

    def merge_clusters(self, other: PixelNode):
        if self.cluster is not other.cluster:
            union = other.cluster.union(self.cluster)

            self.cluster = union
            other.cluster = union

            for node in self.cluster:
                node.cluster = union

    def __str__(self):
        return f"pos: {self.pos}"


class PixelGraph:
    # acts as a set of pixels and associates each with its node
    def __init__(self, skeleton: np.ndarray):
        self.pixels_tuple: dict[tuple[int, int], PixelNode] = {}
        self.pixels: set[PixelNode] = set()
        self.segment_ends: set[PixelNode] = set()

        self.skeleton = skeleton
        for y in range(skeleton.shape[0]):
            for x in range(skeleton.shape[1]):
                self.add_pixel((x,y))
        self.set_neighbours()

    def add_pixel(self, pos: tuple[int, int]):
        x, y = pos

        if pos in self.pixels or not self.skeleton[y, x]:
            return

        node = PixelNode(pos)
        self.pixels_tuple[(x, y)] = node
        self.pixels.add(node)


    def set_neighbours(self):
        for pixel in self.pixels:
            x, y = pixel.pos
            for dx in [-1, 0, 1]:
                if x+dx >= self.skeleton.shape[1] or x+dx < 0:
                    continue
                for dy in [-1, 0, 1]:
                    if dx == dy == 0:
                        continue
                    if y+dy >= self.skeleton.shape[0] or y+dy < 0:
                        continue

                    neighbour = self.pixels_tuple.get((x+dx, y+dy))

                    if neighbour in self.pixels:
                        pixel.neighbours.append(self.pixels_tuple[x+dx, y+dy])
            pixel.is_end = len(pixel.neighbours) != 2
            if pixel.is_end:
                self.segment_ends.add(pixel)

    def do_clustering(self):
        for px in self.segment_ends:
            if len(px.neighbours) > 3:
                for n in px.neighbours:
                    if len(n.neighbours) > 3:
                        px.merge_clusters(n)
        new_ends = set()
        for px in self.segment_ends:
            dominant = px.px_dom()
            px.dom = dominant
            for n in px.cluster:
                n.dom = dominant
            new_ends.add(dominant)
            if px is not dominant:
                self.pixels.discard(px)
        self.segment_ends = new_ends


def ends_to_segments(graph: PixelGraph, ends: list[PixelNode]) -> list[list[tuple[int, int]]]:
    segments = []
    # Track visited edges to avoid traversing the same path twice
    # Store as frozenset({node1, node2}) for undirected uniqueness
    visited_edges = set()

    for start_node in ends:
        graph.pixels.discard(start_node)
        for neighbor in start_node.neighbours:
            graph.pixels.discard(neighbor)
            edge = frozenset({start_node, neighbor})

            if edge not in visited_edges:
                # Start a new segment
                current_segment = [start_node.dom.pos, neighbor.dom.pos]
                visited_edges.add(edge)

                prev_node = start_node
                curr_node = neighbor

                # Walk the path until we hit another junction or endpoint
                while not curr_node.is_end:
                    graph.pixels.discard(curr_node)
                    # Since it's not an end, it has exactly 2 neighbors.
                    # Pick the one we didn't just come from.
                    potential = [n for n in curr_node.neighbours if n != prev_node]
                    if len(potential) > 0:
                        next_node = potential[0]
                    else:
                        break

                    edge = frozenset({curr_node, next_node})
                    if edge in visited_edges:
                        break # Should not happen in a clean skeleton

                    current_segment.append(next_node.dom.pos)
                    visited_edges.add(edge)

                    prev_node = curr_node
                    curr_node = next_node

                segments.append(current_segment)

    return segments


def distance_point_to_line(point, start, end):
    """Calculates the perpendicular distance from a point to a line."""
    if start == end:
        return math.dist(point, start)

    x0, y0 = point
    x1, y1 = start
    x2, y2 = end

    numerator = abs((y2 - y1) * x0 - (x2 - x1) * y0 + x2 * y1 - y2 * x1)
    denominator = math.sqrt((y2 - y1)**2 + (x2 - x1)**2)
    return numerator / denominator

def simplify_segment(points, epsilon):
    """Ramer-Douglas-Peucker simplification."""
    if len(points) < 3:
        return points

    # Find the point with the maximum distance
    dmax = 0
    index = 0
    start = points[0]
    end = points[-1]

    for i in range(1, len(points) - 1):
        d = distance_point_to_line(points[i], start, end)
        if d > dmax:
            index = i
            dmax = d

    # If max distance is greater than epsilon, recursively simplify
    if dmax > epsilon:
        # Recursive call
        left_side = simplify_segment(points[:index+1], epsilon)
        right_side = simplify_segment(points[index:], epsilon)

        # Combine results (drop the duplicate middle point)
        return left_side[:-1] + right_side
    else:
        return [start, end]

# handle parts of image without ends or junctions
def odd_pixels(graph: PixelGraph):
    ends = []
    for px in list(graph.pixels):
        if px not in graph.pixels:
            continue
        graph.pixels.discard(px)
        ends.append(px)
        q = queue.Queue()
        q.put(px)
        while not q.empty:
            node = q.get_nowait()
            for neighbour in node.neighbours:
                if neighbour in graph.pixels:
                    continue
                q.put(neighbour)
                graph.pixels.discard(neighbour)

    return ends


def vectorise(skeleton: np.ndarray, epsilon: float = 0.8):

    graph = PixelGraph(skeleton)
    segments = ends_to_segments(graph, graph.segment_ends)
    if len(graph.pixels) > 0:
        odd = odd_pixels(graph)
        segments += ends_to_segments(graph, odd)
    simple_segments = [simplify_segment(seg, epsilon) for seg in segments]

    seg_lines = []
    for seg in simple_segments:
        last = None
        current_segment = []

        for px in seg:
            if last is None:
                last = px
                continue
            current_segment.append((last, px))
            last = px
        seg_lines.append(current_segment)

    return graph, seg_lines
