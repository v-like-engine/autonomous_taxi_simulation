"""
Road detection and network analysis.
Detects roads, lanes, directions, and builds a routing graph.
"""

import cv2
import numpy as np
from typing import List, Dict, Tuple, Optional
from scipy import ndimage
from skimage.morphology import skeletonize
from .image_processor import ImageProcessor


class RoadDetector:
    """Detects roads and builds a road network graph."""

    def __init__(self, image_processor: ImageProcessor):
        """
        Initialize the road detector.

        Args:
            image_processor: ImageProcessor instance with loaded map
        """
        self.image_processor = image_processor
        self.road_data = {
            "network": [],
            "lanes": [],
            "intersections": [],
            "crosswalks": []
        }
        self.road_mask = None
        self.skeleton = None

    def detect_roads(self, image: np.ndarray) -> Dict:
        """
        Detect all roads in the map image.

        Args:
            image: Preprocessed map image

        Returns:
            Dictionary containing road network data
        """
        # Reset road data
        self.road_data = {
            "network": [],
            "lanes": [],
            "intersections": [],
            "crosswalks": []
        }

        # Extract road mask
        self.road_mask = self._extract_road_mask(image)

        # Extract road skeleton (centerlines)
        self.skeleton = self._extract_skeleton(self.road_mask)

        # Detect intersections
        intersections = self._detect_intersections(self.skeleton)
        self.road_data["intersections"] = intersections

        # Build road network graph
        network = self._build_road_network(self.skeleton, intersections)
        self.road_data["network"] = network

        # Detect lanes
        lanes = self._detect_lanes(self.road_mask, network)
        self.road_data["lanes"] = lanes

        # Detect crosswalks
        crosswalks = self._detect_crosswalks(image, intersections)
        self.road_data["crosswalks"] = crosswalks

        return self.road_data

    def _extract_road_mask(self, image: np.ndarray) -> np.ndarray:
        """
        Extract a binary mask of all roads.

        Args:
            image: Map image

        Returns:
            Binary mask of roads
        """
        # Extract different road types
        yellow_roads = self.image_processor.extract_color_mask(image, 'roads_yellow')
        white_roads = self.image_processor.extract_color_mask(image, 'roads_white')
        gray_roads = self.image_processor.extract_color_mask(image, 'roads_gray')

        # Combine all road types
        road_mask = self.image_processor.combine_masks([yellow_roads, white_roads, gray_roads])

        if road_mask is None:
            return np.zeros(image.shape[:2], dtype=np.uint8)

        # Clean up the mask
        kernel = np.ones((3, 3), np.uint8)
        road_mask = cv2.morphologyEx(road_mask, cv2.MORPH_CLOSE, kernel, iterations=2)
        road_mask = cv2.morphologyEx(road_mask, cv2.MORPH_OPEN, kernel, iterations=1)

        return road_mask

    def _extract_skeleton(self, road_mask: np.ndarray) -> np.ndarray:
        """
        Extract the skeleton (centerlines) of roads.

        Args:
            road_mask: Binary mask of roads

        Returns:
            Binary skeleton image
        """
        # Convert to binary (0 or 1)
        binary = (road_mask > 0).astype(np.uint8)

        # Apply skeletonization
        skeleton = skeletonize(binary)

        # Convert back to uint8
        skeleton = (skeleton * 255).astype(np.uint8)

        return skeleton

    def _detect_intersections(self, skeleton: np.ndarray) -> List[Dict]:
        """
        Detect road intersections.

        Args:
            skeleton: Road skeleton image

        Returns:
            List of intersection dictionaries
        """
        intersections = []

        # Create a kernel to detect intersection points
        # An intersection has more than 2 neighbors in the skeleton
        kernel = np.array([[1, 1, 1],
                          [1, 0, 1],
                          [1, 1, 1]], dtype=np.uint8)

        # Count neighbors for each skeleton pixel
        neighbor_count = cv2.filter2D(skeleton // 255, -1, kernel)

        # Intersection points have 3 or more neighbors
        intersection_mask = (neighbor_count >= 3) & (skeleton > 0)

        # Find intersection points
        y_coords, x_coords = np.where(intersection_mask)

        # Cluster nearby intersection points
        if len(x_coords) > 0:
            points = np.column_stack((x_coords, y_coords))

            # Use simple clustering: group points within 10 pixels
            clusters = self._cluster_points(points, max_distance=10)

            for cluster in clusters:
                # Calculate center of cluster
                center_x = int(np.mean([p[0] for p in cluster]))
                center_y = int(np.mean([p[1] for p in cluster]))

                intersections.append({
                    "position": [center_x, center_y],
                    "type": "intersection",
                    "connected_roads": []  # Will be filled when building network
                })

        return intersections

    def _cluster_points(self, points: np.ndarray, max_distance: float) -> List[List[Tuple]]:
        """
        Cluster points that are close together.

        Args:
            points: Array of (x, y) points
            max_distance: Maximum distance for points to be in same cluster

        Returns:
            List of clusters, where each cluster is a list of points
        """
        if len(points) == 0:
            return []

        clusters = []
        remaining = points.tolist()

        while remaining:
            # Start new cluster with first remaining point
            cluster = [remaining.pop(0)]

            # Find all points close to any point in the cluster
            changed = True
            while changed:
                changed = False
                to_remove = []

                for i, point in enumerate(remaining):
                    for cluster_point in cluster:
                        dist = np.sqrt((point[0] - cluster_point[0])**2 +
                                     (point[1] - cluster_point[1])**2)
                        if dist <= max_distance:
                            cluster.append(point)
                            to_remove.append(i)
                            changed = True
                            break

                # Remove points that were added to cluster
                for i in sorted(to_remove, reverse=True):
                    remaining.pop(i)

            clusters.append(cluster)

        return clusters

    def _build_road_network(self, skeleton: np.ndarray, intersections: List[Dict]) -> List[Dict]:
        """
        Build a road network graph from the skeleton.

        Args:
            skeleton: Road skeleton image
            intersections: List of detected intersections

        Returns:
            List of road segment dictionaries
        """
        network = []

        # Create a copy of skeleton to work with
        work_skeleton = skeleton.copy()

        # Mark intersection areas
        for intersection in intersections:
            x, y = intersection["position"]
            cv2.circle(work_skeleton, (x, y), 5, 0, -1)

        # Find connected components (road segments between intersections)
        num_labels, labels = cv2.connectedComponents(work_skeleton)

        for label in range(1, num_labels):
            # Extract this road segment
            segment_mask = (labels == label).astype(np.uint8) * 255

            # Find endpoints and path
            y_coords, x_coords = np.where(segment_mask > 0)

            if len(x_coords) < 5:  # Too short to be a road segment
                continue

            # Extract points along the path
            points = list(zip(x_coords, y_coords))

            # Sort points to form a continuous path
            if points:
                sorted_points = self._sort_path_points(points)

                # Get width at middle of segment
                mid_idx = len(sorted_points) // 2
                if mid_idx < len(sorted_points):
                    mid_point = sorted_points[mid_idx]
                    width = self._get_road_width_at_point(self.road_mask, mid_point)
                else:
                    width = 10  # default

                # Determine road type based on width
                if width > 20:
                    road_type = "highway"
                    lanes = max(2, width // 10)
                elif width > 12:
                    road_type = "main_road"
                    lanes = max(2, width // 8)
                else:
                    road_type = "minor_road"
                    lanes = 1

                # Detect direction (default to two-way for now)
                direction = "two-way"

                network.append({
                    "id": len(network),
                    "points": sorted_points,
                    "length": self._calculate_path_length(sorted_points),
                    "width": width,
                    "lanes": lanes,
                    "type": road_type,
                    "direction": direction,
                    "start_point": sorted_points[0],
                    "end_point": sorted_points[-1]
                })

        return network

    def _sort_path_points(self, points: List[Tuple[int, int]]) -> List[List[int]]:
        """
        Sort points to form a continuous path.

        Args:
            points: List of (x, y) tuples

        Returns:
            Sorted list of [x, y] points
        """
        if not points:
            return []

        # Start with arbitrary point
        sorted_points = [list(points[0])]
        remaining = set(points[1:])

        while remaining:
            last_point = sorted_points[-1]

            # Find nearest remaining point
            min_dist = float('inf')
            nearest_point = None

            for point in remaining:
                dist = (point[0] - last_point[0])**2 + (point[1] - last_point[1])**2
                if dist < min_dist:
                    min_dist = dist
                    nearest_point = point

            if nearest_point and min_dist < 100:  # Max gap of 10 pixels
                sorted_points.append(list(nearest_point))
                remaining.remove(nearest_point)
            else:
                break  # No more nearby points

        return sorted_points

    def _calculate_path_length(self, points: List[List[int]]) -> float:
        """
        Calculate the length of a path.

        Args:
            points: List of [x, y] points

        Returns:
            Path length in pixels
        """
        if len(points) < 2:
            return 0

        length = 0
        for i in range(len(points) - 1):
            dx = points[i+1][0] - points[i][0]
            dy = points[i+1][1] - points[i][1]
            length += np.sqrt(dx*dx + dy*dy)

        return length

    def _get_road_width_at_point(self, road_mask: np.ndarray, point: List[int]) -> float:
        """
        Estimate road width at a specific point.

        Args:
            road_mask: Binary road mask
            point: [x, y] point on the road

        Returns:
            Estimated width in pixels
        """
        x, y = point

        # Use distance transform
        dist_transform = cv2.distanceTransform(road_mask, cv2.DIST_L2, 5)

        # Width is approximately 2 * distance to edge
        if 0 <= y < dist_transform.shape[0] and 0 <= x < dist_transform.shape[1]:
            width = dist_transform[y, x] * 2
            return max(5, width)  # Minimum width of 5 pixels

        return 10  # Default width

    def _detect_lanes(self, road_mask: np.ndarray, network: List[Dict]) -> List[Dict]:
        """
        Detect individual lanes in roads.

        Args:
            road_mask: Binary road mask
            network: Road network segments

        Returns:
            List of lane dictionaries
        """
        lanes = []

        for road_segment in network:
            num_lanes = road_segment["lanes"]
            width = road_segment["width"]
            points = road_segment["points"]

            if num_lanes == 1:
                # Single lane road
                lanes.append({
                    "id": len(lanes),
                    "road_id": road_segment["id"],
                    "centerline": points,
                    "width": width,
                    "direction": road_segment["direction"]
                })
            else:
                # Multi-lane road: create separate lanes
                # For simplicity, we'll create parallel centerlines
                lane_width = width / num_lanes

                for lane_idx in range(num_lanes):
                    # Calculate offset from center
                    offset = (lane_idx - (num_lanes - 1) / 2) * lane_width

                    # Create offset centerline
                    offset_points = self._offset_path(points, offset)

                    # Determine direction for this lane
                    if road_segment["direction"] == "one-way":
                        lane_direction = "forward"
                    else:
                        lane_direction = "forward" if lane_idx < num_lanes // 2 else "backward"

                    lanes.append({
                        "id": len(lanes),
                        "road_id": road_segment["id"],
                        "lane_index": lane_idx,
                        "centerline": offset_points,
                        "width": lane_width,
                        "direction": lane_direction
                    })

        return lanes

    def _offset_path(self, points: List[List[int]], offset: float) -> List[List[int]]:
        """
        Create a path parallel to the given path with specified offset.

        Args:
            points: Original path points
            offset: Perpendicular offset (positive = right, negative = left)

        Returns:
            Offset path points
        """
        if len(points) < 2:
            return points

        offset_points = []

        for i in range(len(points)):
            # Calculate perpendicular direction
            if i == 0:
                dx = points[i+1][0] - points[i][0]
                dy = points[i+1][1] - points[i][1]
            elif i == len(points) - 1:
                dx = points[i][0] - points[i-1][0]
                dy = points[i][1] - points[i-1][1]
            else:
                dx = points[i+1][0] - points[i-1][0]
                dy = points[i+1][1] - points[i-1][1]

            # Normalize
            length = np.sqrt(dx*dx + dy*dy) + 1e-6
            dx /= length
            dy /= length

            # Perpendicular vector (rotate 90 degrees)
            perp_x = -dy
            perp_y = dx

            # Apply offset
            new_x = int(points[i][0] + perp_x * offset)
            new_y = int(points[i][1] + perp_y * offset)

            offset_points.append([new_x, new_y])

        return offset_points

    def _detect_crosswalks(self, image: np.ndarray, intersections: List[Dict]) -> List[Dict]:
        """
        Detect crosswalks near intersections.

        Args:
            image: Map image
            intersections: List of intersections

        Returns:
            List of crosswalk dictionaries
        """
        crosswalks = []

        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Look for striped patterns (crosswalks)
        # This is a simplified detection - real crosswalks would need more sophisticated detection

        for intersection in intersections:
            x, y = intersection["position"]

            # Define region around intersection
            region_size = 30
            x1 = max(0, x - region_size)
            y1 = max(0, y - region_size)
            x2 = min(gray.shape[1], x + region_size)
            y2 = min(gray.shape[0], y + region_size)

            region = gray[y1:y2, x1:x2]

            if region.size == 0:
                continue

            # Look for high-frequency patterns (stripes)
            # Using FFT or gradient analysis would be better, but for simplicity:
            std_dev = np.std(region)

            if std_dev > 30:  # High variance suggests stripes
                crosswalks.append({
                    "position": [x, y],
                    "intersection_id": len(crosswalks),
                    "type": "crosswalk"
                })

        return crosswalks

    def get_road_mask(self) -> np.ndarray:
        """Get the detected road mask."""
        return self.road_mask

    def get_road_at_point(self, x: int, y: int) -> Optional[Dict]:
        """
        Get the road segment at a specific point.

        Args:
            x: X coordinate
            y: Y coordinate

        Returns:
            Road segment dictionary or None
        """
        for road in self.road_data["network"]:
            # Check if point is near the road path
            points = np.array(road["points"])
            if len(points) > 0:
                distances = np.sqrt(np.sum((points - np.array([x, y]))**2, axis=1))
                if np.min(distances) < road["width"] / 2:
                    return road

        return None

    def get_nearest_lane(self, x: int, y: int) -> Optional[Dict]:
        """
        Get the nearest lane to a point.

        Args:
            x: X coordinate
            y: Y coordinate

        Returns:
            Lane dictionary or None
        """
        min_distance = float('inf')
        nearest_lane = None

        for lane in self.road_data["lanes"]:
            points = np.array(lane["centerline"])
            if len(points) > 0:
                distances = np.sqrt(np.sum((points - np.array([x, y]))**2, axis=1))
                min_dist = np.min(distances)
                if min_dist < min_distance:
                    min_distance = min_dist
                    nearest_lane = lane

        return nearest_lane if min_distance < 50 else None
