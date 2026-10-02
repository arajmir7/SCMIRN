"""
Heatmap Engine for SCMIRN Geospatial Service
Generates heatmap data for civic issues visualization using various algorithms
"""

import math
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import json


class HeatmapAlgorithm(Enum):
    """Available heatmap generation algorithms"""
    GRID = "grid"
    KERNEL_DENSITY = "kernel"
    CLUSTERING = "cluster"
    WEIGHTED = "weighted"


@dataclass
class GeoPoint:
    """Represents a geographic point with intensity weighting"""
    lat: float
    lon: float
    intensity: float = 1.0
    weight: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            'lat': self.lat,
            'lon': self.lon,
            'intensity': self.intensity,
            'weight': self.weight,
            'metadata': self.metadata
        }


@dataclass
class HeatmapCell:
    """Represents a single heatmap grid cell"""
    grid_x: int
    grid_y: int
    center_lat: float
    center_lon: float
    intensity: float = 0.0
    count: int = 0
    points: List[GeoPoint] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            'x': self.grid_x,
            'y': self.grid_y,
            'lat': self.center_lat,
            'lon': self.center_lon,
            'intensity': round(self.intensity, 3),
            'count': self.count,
            'radius': self._calculate_radius(),
            'issues': [p.metadata for p in self.points[:5]]  # Limit metadata
        }
    
    def _calculate_radius(self) -> int:
        """Calculate visual radius based on point count"""
        base = 20
        return min(base + (self.count * 8), 120)


class HeatmapEngine:
    """
    Advanced heatmap generation engine for civic issue visualization
    Supports multiple algorithms and clustering techniques
    """
    
    DEFAULT_GRID_SIZE = 0.001  # ~100m at equator
    DEFAULT_RADIUS_METERS = 500
    EARTH_RADIUS_METERS = 6371000
    
    def __init__(self, grid_size: float = DEFAULT_GRID_SIZE):
        self.grid_size = grid_size
        self.cells: Dict[Tuple[int, int], HeatmapCell] = {}
        
    def build(self, points: List[Dict[str, Any]], algorithm: str = "grid") -> List[Dict]:
        """
        Main entry point to build heatmap data
        
        Args:
            points: List of issue dictionaries with lat, lon, priority_score, etc.
            algorithm: 'grid', 'kernel', 'cluster', or 'weighted'
            
        Returns:
            List of heatmap cells ready for frontend visualization
        """
        if not points:
            return []
            
        # Convert raw points to GeoPoint objects
        geo_points = self._normalize_points(points)
        
        # Route to appropriate algorithm
        algo = HeatmapAlgorithm(algorithm) if algorithm in [a.value for a in HeatmapAlgorithm] else HeatmapAlgorithm.GRID
        
        if algo == HeatmapAlgorithm.KERNEL_DENSITY:
            return self._generate_kernel_density(geo_points)
        elif algo == HeatmapAlgorithm.CLUSTERING:
            return self._generate_cluster_centers(geo_points)
        elif algo == HeatmapAlgorithm.WEIGHTED:
            return self._generate_weighted_heatmap(geo_points)
        else:
            return self._generate_grid_heatmap(geo_points)
    
    def _normalize_points(self, points: List[Dict]) -> List[GeoPoint]:
        """Convert raw issue data to GeoPoint objects with calculated intensities"""
        geo_points = []
        
        for point in points:
            if not self._validate_coordinates(point):
                continue
                
            intensity = self._calculate_intensity(point)
            weight = self._calculate_weight(point)
            
            geo_points.append(GeoPoint(
                lat=float(point.get('lat', 0)),
                lon=float(point.get('lon', 0)),
                intensity=intensity,
                weight=weight,
                metadata={
                    'id': point.get('id'),
                    'title': point.get('title', ''),
                    'category': point.get('category', 'Unknown'),
                    'priority_tier': point.get('priority_tier', 'medium'),
                    'priority_score': point.get('priority_score', 5000),
                    'status': point.get('status', 'reported'),
                    'fund_target': point.get('fund_target', 0),
                    'fund_collected': point.get('fund_collected', 0)
                }
            ))
        
        return geo_points
    
    def _validate_coordinates(self, point: Dict) -> bool:
        """Validate that point has valid coordinates"""
        try:
            lat = float(point.get('lat', 0))
            lon = float(point.get('lon', 0))
            return -90 <= lat <= 90 and -180 <= lon <= 180
        except (TypeError, ValueError):
            return False
    
    def _calculate_intensity(self, point: Dict) -> float:
        """
        Calculate intensity value (0.0 - 1.0) based on issue priority and metadata
        """
        # Priority tier base values
        tier_values = {
            'critical': 1.0,
            'high': 0.75,
            'medium': 0.5,
            'low': 0.25
        }
        
        tier = point.get('priority_tier', 'medium').lower()
        base_intensity = tier_values.get(tier, 0.5)
        
        # Adjust by priority score (0-10000 scale)
        score = point.get('priority_score', 5000)
        score_factor = min(score / 10000.0, 1.0)
        
        # Funding urgency factor (if barely funded, higher intensity)
        fund_target = point.get('fund_target', 1)
        fund_collected = point.get('fund_collected', 0)
        if fund_target > 0:
            funding_ratio = fund_collected / fund_target
            urgency = 1.0 - funding_ratio  # Less funded = more urgent
        else:
            urgency = 0.5
        
        # Combine factors
        final_intensity = (base_intensity * 0.5) + (score_factor * 0.3) + (urgency * 0.2)
        return min(max(final_intensity, 0.0), 1.0)
    
    def _calculate_weight(self, point: Dict) -> float:
        """Calculate point weight for clustering algorithms"""
        # Age factor (newer issues have higher weight)
        # In production, use actual timestamp
        age_weight = 1.0
        
        # Verification weight
        status = point.get('status', '')
        status_weights = {
            'verified': 1.2,
            'in_progress': 1.1,
            'funded': 1.0,
            'reported': 0.9,
            'resolved': 0.3
        }
        
        return age_weight * status_weights.get(status, 1.0)
    
    def _generate_grid_heatmap(self, points: List[GeoPoint]) -> List[Dict]:
        """Generate grid-based heatmap (fastest, good for large datasets)"""
        if not points:
            return []
        
        # Calculate bounds
        bounds = self._calculate_bounds(points)
        min_lat, max_lat = bounds['min_lat'], bounds['max_lat']
        min_lon, max_lon = bounds['min_lon'], bounds['max_lon']
        
        # Reset cells
        self.cells = {}
        
        # Assign points to grid cells
        for point in points:
            grid_x = int((point.lon - min_lon) / self.grid_size)
            grid_y = int((point.lat - min_lat) / self.grid_size)
            
            key = (grid_x, grid_y)
            
            if key not in self.cells:
                self.cells[key] = HeatmapCell(
                    grid_x=grid_x,
                    grid_y=grid_y,
                    center_lat=min_lat + (grid_y + 0.5) * self.grid_size,
                    center_lon=min_lon + (grid_x + 0.5) * self.grid_size
                )
            
            cell = self.cells[key]
            cell.intensity += point.intensity * point.weight
            cell.count += 1
            cell.points.append(point)
        
        # Normalize intensities
        return self._normalize_and_convert_cells()
    
    def _generate_kernel_density(self, points: List[GeoPoint], bandwidth: Optional[float] = None) -> List[Dict]:
        """
        Generate kernel density estimation heatmap
        Smoother than grid-based, better for visualization
        """
        if not points:
            return []
        
        if bandwidth is None:
            bandwidth = self.grid_size * 2.5
        
        # First generate grid
        grid_result = self._generate_grid_heatmap(points)
        
        # Apply Gaussian smoothing
        smoothed = self._apply_gaussian_smoothing(grid_result, bandwidth)
        
        return smoothed
    
    def _apply_gaussian_smoothing(self, cells: List[Dict], bandwidth: float) -> List[Dict]:
        """Apply Gaussian kernel smoothing to grid cells"""
        if len(cells) < 2:
            return cells
        
        smoothed = []
        
        for i, cell in enumerate(cells):
            new_intensity = cell['intensity']
            total_weight = 1.0
            
            # Add influence from neighbors
            for j, other in enumerate(cells):
                if i == j:
                    continue
                
                dist = self._haversine_distance(
                    cell['lat'], cell['lon'],
                    other['lat'], other['lon']
                )
                
                if dist < bandwidth * self.EARTH_RADIUS_METERS:
                    weight = self._gaussian_kernel(dist, bandwidth * self.EARTH_RADIUS_METERS)
                    new_intensity += other['intensity'] * weight
                    total_weight += weight
            
            smoothed.append({
                **cell,
                'intensity': round(min(new_intensity / total_weight, 1.0), 3),
                'smoothed': True
            })
        
        return smoothed
    
    def _gaussian_kernel(self, distance: float, bandwidth: float) -> float:
        """Gaussian kernel function for smoothing"""
        if bandwidth == 0:
            return 0
        return math.exp(-0.5 * (distance / bandwidth) ** 2)
    
    def _generate_weighted_heatmap(self, points: List[GeoPoint]) -> List[Dict]:
        """Generate heatmap weighted by multiple factors"""
        # Similar to grid but with different weighting
        return self._generate_grid_heatmap(points)
    
    def _generate_cluster_centers(self, points: List[GeoPoint], min_cluster_size: int = 3) -> List[Dict]:
        """
        Identify high-density cluster centers
        Returns centroids for resource allocation prioritization
        """
        if len(points) < min_cluster_size:
            return []
        
        clusters = []
        used_indices = set()
        
        for i, p1 in enumerate(points):
            if i in used_indices:
                continue
            
            cluster_points = [p1]
            used_indices.add(i)
            
            # Find nearby points
            for j, p2 in enumerate(points[i+1:], start=i+1):
                if j in used_indices:
                    continue
                
                dist = self._haversine_distance(p1.lat, p1.lon, p2.lat, p2.lon)
                
                if dist < self.DEFAULT_RADIUS_METERS:
                    cluster_points.append(p2)
                    used_indices.add(j)
            
            if len(cluster_points) >= min_cluster_size:
                cluster_data = self._create_cluster_data(cluster_points)
                clusters.append(cluster_data)
        
        # Sort by combined severity score
        clusters.sort(key=lambda x: x['severity_score'], reverse=True)
        return clusters
    
    def _create_cluster_data(self, points: List[GeoPoint]) -> Dict:
        """Create cluster data from group of points"""
        # Calculate centroid
        avg_lat = sum(p.lat for p in points) / len(points)
        avg_lon = sum(p.lon for p in points) / len(points)
        
        # Calculate radius (max distance + padding)
        max_dist = 0
        for p in points:
            dist = self._haversine_distance(avg_lat, avg_lon, p.lat, p.lon)
            max_dist = max(max_dist, dist)
        
        # Calculate aggregate metrics
        total_intensity = sum(p.intensity for p in points)
        avg_intensity = total_intensity / len(points)
        
        # Severity score combines count and intensity
        severity_score = len(points) * avg_intensity * 100
        
        # Dominant category
        categories = {}
        for p in points:
            cat = p.metadata.get('category', 'Unknown')
            categories[cat] = categories.get(cat, 0) + 1
        dominant_category = max(categories.items(), key=lambda x: x[1])[0] if categories else 'Mixed'
        
        return {
            'type': 'cluster',
            'lat': round(avg_lat, 6),
            'lon': round(avg_lon, 6),
            'issue_count': len(points),
            'radius': int(max_dist * 1.2) + 50,  # 20% padding + base
            'intensity': round(min(avg_intensity, 1.0), 3),
            'severity_score': round(severity_score, 2),
            'dominant_category': dominant_category,
            'categories': categories,
            'bounds': {
                'radius_meters': int(max_dist * 1.5)
            },
            'issues': [p.to_dict() for p in points[:10]]  # Sample of issues
        }
    
    def _normalize_and_convert_cells(self) -> List[Dict]:
        """Normalize cell intensities and convert to dict format"""
        if not self.cells:
            return []
        
        intensities = [c.intensity for c in self.cells.values()]
        max_intensity = max(intensities) if intensities else 1
        min_intensity = min(intensities) if intensities else 0
        
        result = []
        for cell in self.cells.values():
            # Normalize to 0-1 range
            if max_intensity != min_intensity:
                normalized = (cell.intensity - min_intensity) / (max_intensity - min_intensity)
            else:
                normalized = 0.5
            
            cell.intensity = normalized
            result.append(cell.to_dict())
        
        # Sort by intensity descending
        result.sort(key=lambda x: x['intensity'], reverse=True)
        return result
    
    def _calculate_bounds(self, points: List[GeoPoint]) -> Dict:
        """Calculate geographic bounds of point set"""
        lats = [p.lat for p in points]
        lons = [p.lon for p in points]
        
        return {
            'min_lat': min(lats),
            'max_lat': max(lats),
            'min_lon': min(lons),
            'max_lon': max(lons),
            'center_lat': (min(lats) + max(lats)) / 2,
            'center_lon': (min(lons) + max(lons)) / 2
        }
    
    def _haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate great circle distance between two points in meters
        """
        R = self.EARTH_RADIUS_METERS
        
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)
        
        a = math.sin(delta_phi/2)**2 + \
            math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return R * c
    
    def get_hotspots(self, points: List[Dict], top_n: int = 10) -> List[Dict]:
        """
        Get top N hotspot locations for prioritization
        """
        clusters = self.build(points, algorithm='cluster')
        return clusters[:top_n] if len(clusters) > top_n else clusters
    
    def export_to_geojson(self, heatmap_data: List[Dict]) -> Dict:
        """Export heatmap data to GeoJSON format"""
        features = []
        
        for cell in heatmap_data:
            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [cell['lon'], cell['lat']]
                },
                "properties": {
                    "intensity": cell['intensity'],
                    "count": cell.get('count', 1),
                    "radius": cell.get('radius', 20),
                    "type": cell.get('type', 'cell')
                }
            }
            features.append(feature)
        
        return {
            "type": "FeatureCollection",
            "features": features
        }


# Integration helpers
def generate_issue_heatmap(issues: List[Dict], algorithm: str = "grid") -> Dict:
    """
    Convenience function for generating heatmap from issues
    
    Returns:
        Dict with 'cells' and 'metadata'
    """
    engine = HeatmapEngine()
    
    data = engine.build(issues, algorithm=algorithm)
    hotspots = engine.get_hotspots(issues, top_n=5)
    
    return {
        'algorithm': algorithm,
        'total_issues': len(issues),
        'heatmap_cells': data,
        'hotspots': hotspots,
        'bounds': engine._calculate_bounds([GeoPoint(i['lat'], i['lon']) for i in issues if 'lat' in i and 'lon' in i]) if issues else None
    }


def get_priority_zones(issues: List[Dict]) -> List[Dict]:
    """
    Get high-priority zones for resource allocation
    """
    engine = HeatmapEngine()
    return engine.get_hotspots(issues, top_n=10)