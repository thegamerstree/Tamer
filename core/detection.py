"""
Advanced computer vision detection system for GDMO
"""

import time
import threading
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, Future
import win32gui
import win32process
import psutil
from PIL import ImageGrab
import numpy as np

# Optional imports with fallbacks
CV_AVAILABLE = False
try:
    import cv2
    CV_AVAILABLE = True
except ImportError:
    print("Warning: OpenCV not available. Computer vision disabled.")

from config.constants import DIGIMON_COLOR_PROFILES, WINDOW_DETECTION_PATTERNS, DETECTION_THRESHOLDS
from utils.logger import Logger

@dataclass
class DetectedEntity:
    """Represents a detected entity in the game"""
    entity_type: str
    x: int
    y: int
    width: int
    height: int
    confidence: float
    distance_from_center: float
    area: int
    timestamp: float
    color_match_score: float
    stability_score: float = 1.0

@dataclass
class DetectionRegion:
    """Represents a region of interest for detection"""
    x: int
    y: int
    width: int
    height: int
    priority: int
    last_detection: float = 0

class DigimonDetector:
    """Advanced computer vision detector with optimization and threading"""
    
    def __init__(self):
        self.logger = Logger()
        self.detection_enabled = CV_AVAILABLE
        
        # Window management
        self.game_window_region = None
        self.window_title = ""
        self.detected_windows = []
        self.active_window_hwnd = None
        
        # Detection optimization
        self.roi_regions = []
        self.last_screenshot = None
        self.last_screenshot_time = 0
        self.screenshot_cache_duration = 0.033  # ~30 FPS
        
        # Threading and performance
        self.executor = ThreadPoolExecutor(max_workers=2) if CV_AVAILABLE else None
        self.detection_future: Optional[Future] = None
        self.detection_lock = threading.Lock()
        
        # Detection history and stability
        self.detection_history = []
        self.max_history = 50
        self.entity_tracking = {}
        
        # Performance metrics
        self.detection_times = []
        self.max_detection_times = 100
        self.total_detections = 0
        self.successful_detections = 0
        
        # Adaptive optimization
        self.performance_mode = "balanced"  # "fast", "balanced", "quality"
        self.auto_roi_enabled = True
        self.detection_interval = 0.1
        
        if not CV_AVAILABLE:
            self.logger.warning("Computer vision not available - detection disabled")
    
    def initialize(self) -> bool:
        """Initialize the detection system"""
        if not self.detection_enabled:
            return False
        
        try:
            # Test OpenCV functionality
            test_image = np.zeros((100, 100, 3), dtype=np.uint8)
            _ = cv2.cvtColor(test_image, cv2.COLOR_BGR2HSV)
            
            self.logger.info("Detection system initialized")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize detection system: {e}")
            self.detection_enabled = False
            return False
    
    def setup_game_window(self, window_title: str = "") -> Tuple[bool, List[Tuple[str, Tuple, str]]]:
        """
        Setup game window detection
        
        Returns:
            Tuple of (success, list of (title, rect, process_name))
        """
        if not self.detection_enabled:
            return False, []
        
        try:
            self.detected_windows = []
            
            def enum_windows_callback(hwnd, windows):
                if win32gui.IsWindowVisible(hwnd):
                    window_text = win32gui.GetWindowText(hwnd).lower()
                    rect = win32gui.GetWindowRect(hwnd)
                    
                    try:
                        _, pid = win32process.GetWindowThreadProcessId(hwnd)
                        process = psutil.Process(pid)
                        process_name = process.name().lower()
                    except:
                        process_name = "unknown"
                    
                    # Check if this looks like a game window
                    for pattern in WINDOW_DETECTION_PATTERNS:
                        if pattern.lower() in window_text or pattern.lower() in process_name:
                            # Validate window rectangle
                            if (rect[0] > -30000 and rect[2] > rect[0] and 
                                rect[3] > rect[1] and (rect[2] - rect[0]) > 200 and 
                                (rect[3] - rect[1]) > 200):
                                windows.append((hwnd, window_text, rect, process_name))
                                break
                
                return True
            
            win32gui.EnumWindows(enum_windows_callback, self.detected_windows)
            
            # Auto-select best window
            if self.detected_windows:
                best_window = self._select_best_game_window()
                if best_window:
                    hwnd, title, rect, proc_name = best_window
                    self.set_game_window_by_hwnd(hwnd)
                    
                return True, [(title, rect, proc_name) for hwnd, title, rect, proc_name in self.detected_windows]
            
            return False, []
            
        except Exception as e:
            self.logger.error(f"Window setup failed: {e}")
            return False, []
    
    def _select_best_game_window(self) -> Optional[Tuple]:
        """Select the best game window from detected windows"""
        if not self.detected_windows:
            return None
        
        # Score windows based on various factors
        scored_windows = []
        
        for hwnd, title, rect, proc_name in self.detected_windows:
            score = 0
            
            # Prefer larger windows
            area = (rect[2] - rect[0]) * (rect[3] - rect[1])
            score += min(100, area / 10000)  # Normalize area score
            
            # Prefer windows with "digimon" or "gdmo" in title
            if "digimon" in title or "gdmo" in title:
                score += 50
            
            # Prefer GDMO.exe process
            if "gdmo" in proc_name:
                score += 30
            
            # Prefer windows that are not minimized
            if rect[0] >= 0 and rect[1] >= 0:
                score += 20
            
            scored_windows.append((score, hwnd, title, rect, proc_name))
        
        # Return highest scored window
        if scored_windows:
            scored_windows.sort(reverse=True)
            _, hwnd, title, rect, proc_name = scored_windows[0]
            return (hwnd, title, rect, proc_name)
        
        return None
    
    def set_game_window_by_hwnd(self, hwnd) -> Tuple[bool, str]:
        """Set game window by window handle"""
        try:
            rect = win32gui.GetWindowRect(hwnd)
            title = win32gui.GetWindowText(hwnd)
            
            if (rect[0] > -30000 and rect[2] > rect[0] and 
                rect[3] > rect[1]):
                
                self.game_window_region = rect
                self.window_title = title
                self.active_window_hwnd = hwnd
                
                # Reset ROI regions for new window
                self.roi_regions = []
                self._initialize_roi_regions()
                
                self.logger.info(f"Game window set: {title}")
                return True, title
            
            return False, "Invalid window rectangle"
            
        except Exception as e:
            self.logger.error(f"Failed to set game window: {e}")
            return False, str(e)
    
    def _initialize_roi_regions(self):
        """Initialize regions of interest for optimized detection"""
        if not self.game_window_region:
            return
        
        x, y, right, bottom = self.game_window_region
        width = right - x
        height = bottom - y
        
        # Create initial ROI regions
        # Center region (highest priority)
        center_w, center_h = width // 3, height // 3
        center_x = x + (width - center_w) // 2
        center_y = y + (height - center_h) // 2
        
        self.roi_regions = [
            DetectionRegion(center_x, center_y, center_w, center_h, 1),
            DetectionRegion(x, y, width, height // 3, 3),  # Top region
            DetectionRegion(x, y + height * 2 // 3, width, height // 3, 3),  # Bottom region
            DetectionRegion(x, y, width // 3, height, 4),  # Left region
            DetectionRegion(x + width * 2 // 3, y, width // 3, height, 4),  # Right region
        ]
    
    def get_optimized_screenshot(self, force_new: bool = False) -> Optional[np.ndarray]:
        """Get screenshot with caching optimization"""
        current_time = time.time()
        
        # Use cached screenshot if recent enough
        if (not force_new and self.last_screenshot is not None and 
            current_time - self.last_screenshot_time < self.screenshot_cache_duration):
            return self.last_screenshot
        
        if not self.game_window_region:
            return None
        
        try:
            # Determine capture region
            if self.auto_roi_enabled and self.roi_regions:
                # Use highest priority ROI that hasn't been checked recently
                capture_region = None
                for roi in sorted(self.roi_regions, key=lambda r: r.priority):
                    if current_time - roi.last_detection > self.detection_interval:
                        capture_region = (roi.x, roi.y, roi.x + roi.width, roi.y + roi.height)
                        roi.last_detection = current_time
                        break
                
                if not capture_region:
                    capture_region = self.game_window_region
            else:
                capture_region = self.game_window_region
            
            # Capture screenshot
            screenshot = ImageGrab.grab(bbox=capture_region)
            
            # Resize for performance if needed
            if self.performance_mode == "fast":
                new_size = (screenshot.width // 3, screenshot.height // 3)
                screenshot = screenshot.resize(new_size)
            elif self.performance_mode == "balanced":
                new_size = (screenshot.width // 2, screenshot.height // 2)
                screenshot = screenshot.resize(new_size)
            
            # Convert to OpenCV format
            cv_image = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            
            # Cache the screenshot
            self.last_screenshot = cv_image
            self.last_screenshot_time = current_time
            
            return cv_image
            
        except Exception as e:
            self.logger.error(f"Screenshot capture failed: {e}")
            return None
    
    def detect_entities(self, force_detection: bool = False) -> List[DetectedEntity]:
        """
        Detect entities in the game window
        
        Args:
            force_detection: Force immediate detection, bypassing timing checks
        """
        if not self.detection_enabled or not self.game_window_region:
            return []
        
        current_time = time.time()
        
        # Check if detection is needed
        if (not force_detection and self.detection_future and 
            not self.detection_future.done()):
            return self._get_recent_detections()
        
        # Start new detection
        self.detection_future = self.executor.submit(self._perform_detection)
        
        try:
            # Wait for detection with timeout
            entities = self.detection_future.result(timeout=0.2)
            return entities
        except:
            # Return recent detections if current detection fails/times out
            return self._get_recent_detections()
    
    def _perform_detection(self) -> List[DetectedEntity]:
        """Perform the actual entity detection"""
        detection_start = time.time()
        
        try:
            # Get screenshot
            screenshot = self.get_optimized_screenshot()
            if screenshot is None:
                return []
            
            # Convert to HSV for color detection
            hsv = cv2.cvtColor(screenshot, cv2.COLOR_BGR2HSV)
            
            # Apply slight blur to reduce noise
            hsv = cv2.GaussianBlur(hsv, (3, 3), 0)
            
            detected_entities = []
            
            # Process each entity type
            for entity_type, config in DIGIMON_COLOR_PROFILES.items():
                entities = self._detect_entity_type(hsv, entity_type, config)
                detected_entities.extend(entities)
            
            # Filter and validate detections
            filtered_entities = self._filter_and_validate_detections(detected_entities)
            
            # Update detection history
            self._update_detection_history(filtered_entities)
            
            # Track performance
            detection_time = time.time() - detection_start
            self.detection_times.append(detection_time)
            if len(self.detection_times) > self.max_detection_times:
                self.detection_times.pop(0)
            
            self.total_detections += 1
            if filtered_entities:
                self.successful_detections += 1
            
            # Update ROI regions based on detections
            if self.auto_roi_enabled and filtered_entities:
                self._update_roi_regions(filtered_entities)
            
            return filtered_entities
            
        except Exception as e:
            self.logger.error(f"Detection error: {e}")
            return []
    
    def _detect_entity_type(self, hsv_image: np.ndarray, entity_type: str, config: Dict) -> List[DetectedEntity]:
        """Detect entities of a specific type"""
        try:
            # Create combined mask for all color ranges
            combined_mask = None
            
            for color_range in config['colors']:
                lower, upper = color_range
                mask = cv2.inRange(hsv_image, np.array(lower), np.array(upper))
                
                # Morphological operations to clean up mask
                kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
                mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
                mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
                
                if combined_mask is None:
                    combined_mask = mask
                else:
                    combined_mask = cv2.bitwise_or(combined_mask, mask)
            
            if combined_mask is None:
                return []
            
            # Find contours
            contours, _ = cv2.findContours(combined_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            entities = []
            min_area = config.get('min_area', 50)
            max_area = config.get('max_area', 5000)
            
            for contour in contours:
                area = cv2.contourArea(contour)
                
                if min_area <= area <= max_area:
                    # Get bounding rectangle
                    x, y, w, h = cv2.boundingRect(contour)
                    
                    # Calculate center point
                    center_x = x + w // 2
                    center_y = y + h // 2
                    
                    # Adjust coordinates based on performance scaling
                    scale_factor = self._get_scale_factor()
                    center_x = int(center_x * scale_factor)
                    center_y = int(center_y * scale_factor)
                    w = int(w * scale_factor)
                    h = int(h * scale_factor)
                    
                    # Calculate distance from center
                    distance = self._calculate_distance_from_center(center_x, center_y)
                    
                    # Calculate confidence score
                    confidence = self._calculate_confidence(contour, area, min_area, max_area)
                    
                    # Calculate color match score
                    color_score = self._calculate_color_match_score(hsv_image, x, y, w, h, config)
                    
                    # Create entity
                    entity = DetectedEntity(
                        entity_type=entity_type,
                        x=center_x,
                        y=center_y,
                        width=w,
                        height=h,
                        confidence=confidence,
                        distance_from_center=distance,
                        area=area,
                        timestamp=time.time(),
                        color_match_score=color_score
                    )
                    
                    entities.append(entity)
            
            return entities
            
        except Exception as e:
            self.logger.error(f"Error detecting {entity_type}: {e}")
            return []
    
    def _get_scale_factor(self) -> float:
        """Get current scale factor based on performance mode"""
        if self.performance_mode == "fast":
            return 3.0
        elif self.performance_mode == "balanced":
            return 2.0
        else:
            return 1.0
    
    def _calculate_distance_from_center(self, x: int, y: int) -> float:
        """Calculate distance from center of game window"""
        if not self.game_window_region:
            return float('inf')
        
        window_x, window_y, window_right, window_bottom = self.game_window_region
        center_x = (window_right - window_x) // 2
        center_y = (window_bottom - window_y) // 2
        
        return ((x - center_x) ** 2 + (y - center_y) ** 2) ** 0.5
    
    def _calculate_confidence(self, contour, area: int, min_area: int, max_area: int) -> float:
        """Calculate confidence score for detection"""
        try:
            # Area-based confidence
            area_ratio = (area - min_area) / (max_area - min_area)
            area_confidence = min(1.0, area_ratio * 2)  # Peak at 50% of range
            
            # Shape-based confidence (solidity)
            hull = cv2.convexHull(contour)
            hull_area = cv2.contourArea(hull)
            solidity = area / hull_area if hull_area > 0 else 0
            
            # Aspect ratio confidence
            x, y, w, h = cv2.boundingRect(contour)
            aspect_ratio = w / h if h > 0 else 0
            aspect_confidence = 1.0 - abs(aspect_ratio - 1.0)  # Prefer square-ish shapes
            aspect_confidence = max(0.3, aspect_confidence)  # Minimum confidence
            
            # Combine confidence factors
            total_confidence = (area_confidence * 0.4 + 
                              solidity * 0.4 + 
                              aspect_confidence * 0.2)
            
            return min(1.0, max(0.1, total_confidence))
            
        except:
            return 0.5  # Default confidence
    
    def _calculate_color_match_score(self, hsv_image: np.ndarray, x: int, y: int, w: int, h: int, config: Dict) -> float:
        """Calculate how well the detected region matches expected colors"""
        try:
            # Extract region
            region = hsv_image[y:y+h, x:x+w]
            if region.size == 0:
                return 0.0
            
            # Calculate color distribution
            total_pixels = region.shape[0] * region.shape[1]
            matching_pixels = 0
            
            for color_range in config['colors']:
                lower, upper = color_range
                mask = cv2.inRange(region, np.array(lower), np.array(upper))
                matching_pixels += cv2.countNonZero(mask)
            
            # Calculate match percentage
            match_score = matching_pixels / total_pixels if total_pixels > 0 else 0
            return min(1.0, match_score)
            
        except Exception as e:
            self.logger.error(f"Color match calculation error: {e}")
            return 0.5  # Default score
    
    def _filter_and_validate_detections(self, entities: List[DetectedEntity]) -> List[DetectedEntity]:
        """Filter and validate detected entities"""
        if not entities:
            return []
        
        # Filter by confidence threshold
        confidence_threshold = DETECTION_THRESHOLDS['minimum_confidence']
        filtered = [e for e in entities if e.confidence >= confidence_threshold]
        
        # Remove overlapping detections (keep highest confidence)
        filtered = self._remove_overlapping_detections(filtered)
        
        # Validate against history for stability
        filtered = self._validate_against_history(filtered)
        
        # Sort by priority and confidence
        filtered.sort(key=lambda e: (
            DIGIMON_COLOR_PROFILES.get(e.entity_type, {}).get('priority', 999),
            -e.confidence
        ))
        
        return filtered
    
    def _remove_overlapping_detections(self, entities: List[DetectedEntity]) -> List[DetectedEntity]:
        """Remove overlapping detections, keeping the one with highest confidence"""
        if len(entities) <= 1:
            return entities
        
        filtered = []
        for entity in sorted(entities, key=lambda e: e.confidence, reverse=True):
            is_overlapping = False
            
            for existing in filtered:
                # Check if entities overlap significantly
                distance = ((entity.x - existing.x) ** 2 + (entity.y - existing.y) ** 2) ** 0.5
                min_distance = max(entity.width, entity.height, existing.width, existing.height) / 2
                
                if distance < min_distance:
                    is_overlapping = True
                    break
            
            if not is_overlapping:
                filtered.append(entity)
        
        return filtered
    
    def _validate_against_history(self, entities: List[DetectedEntity]) -> List[DetectedEntity]:
        """Validate detections against historical data for stability"""
        if not self.detection_history:
            return entities
        
        # Get recent detections
        recent_time = time.time() - 2.0  # Last 2 seconds
        recent_detections = [
            detection for detection in self.detection_history 
            if detection.timestamp > recent_time
        ]
        
        if not recent_detections:
            return entities
        
        validated = []
        for entity in entities:
            # Check if similar detection exists in recent history
            stability_score = 0.0
            
            for historical in recent_detections:
                if historical.entity_type == entity.entity_type:
                    distance = ((entity.x - historical.x) ** 2 + (entity.y - historical.y) ** 2) ** 0.5
                    
                    if distance < 100:  # Close enough to be same entity
                        time_diff = entity.timestamp - historical.timestamp
                        stability_score = max(stability_score, 1.0 - (time_diff / 2.0))
            
            entity.stability_score = stability_score
            
            # Include if stable or high confidence
            if stability_score > 0.3 or entity.confidence > DETECTION_THRESHOLDS['excellent_confidence']:
                validated.append(entity)
        
        return validated
    
    def _update_detection_history(self, entities: List[DetectedEntity]):
        """Update detection history with new entities"""
        current_time = time.time()
        
        # Add new detections
        self.detection_history.extend(entities)
        
        # Remove old detections
        cutoff_time = current_time - 10.0  # Keep 10 seconds of history
        self.detection_history = [
            detection for detection in self.detection_history 
            if detection.timestamp > cutoff_time
        ]
        
        # Limit history size
        if len(self.detection_history) > self.max_history:
            self.detection_history = self.detection_history[-self.max_history:]
    
    def _update_roi_regions(self, entities: List[DetectedEntity]):
        """Update ROI regions based on recent detections"""
        if not entities or not self.auto_roi_enabled:
            return
        
        # Find areas with most activity
        activity_centers = []
        for entity in entities:
            activity_centers.append((entity.x, entity.y))
        
        if len(activity_centers) >= 2:
            # Calculate centroid of activity
            avg_x = sum(x for x, y in activity_centers) / len(activity_centers)
            avg_y = sum(y for x, y in activity_centers) / len(activity_centers)
            
            # Update center ROI to focus on activity area
            if self.roi_regions and self.game_window_region:
                roi_size = 200
                new_x = max(self.game_window_region[0], int(avg_x - roi_size // 2))
                new_y = max(self.game_window_region[1], int(avg_y - roi_size // 2))
                
                self.roi_regions[0] = DetectionRegion(new_x, new_y, roi_size, roi_size, 1)
    
    def _get_recent_detections(self) -> List[DetectedEntity]:
        """Get recent detections from history"""
        if not self.detection_history:
            return []
        
        recent_time = time.time() - 0.5  # Last 0.5 seconds
        return [
            detection for detection in self.detection_history 
            if detection.timestamp > recent_time
        ]
    
    def get_movement_direction(self, target_x: int, target_y: int) -> List[str]:
        """Get movement directions to reach target"""
        if not self.game_window_region:
            return []
        
        window_x, window_y, window_right, window_bottom = self.game_window_region
        center_x = (window_right - window_x) // 2
        center_y = (window_bottom - window_y) // 2
        
        movements = []
        threshold = 50  # Minimum distance to trigger movement
        
        dx = target_x - center_x
        dy = target_y - center_y
        
        if abs(dx) > threshold:
            movements.append('D' if dx > 0 else 'A')
        
        if abs(dy) > threshold:
            movements.append('S' if dy > 0 else 'W')
        
        return movements
    
    def get_detection_statistics(self) -> Dict[str, Any]:
        """Get detection system performance statistics"""
        avg_detection_time = 0
        if self.detection_times:
            avg_detection_time = sum(self.detection_times) / len(self.detection_times)
        
        success_rate = 0
        if self.total_detections > 0:
            success_rate = self.successful_detections / self.total_detections
        
        return {
            'detection_enabled': self.detection_enabled,
            'window_detected': self.game_window_region is not None,
            'window_title': self.window_title,
            'total_detections': self.total_detections,
            'successful_detections': self.successful_detections,
            'success_rate': success_rate,
            'avg_detection_time': avg_detection_time,
            'detection_fps': 1.0 / avg_detection_time if avg_detection_time > 0 else 0,
            'performance_mode': self.performance_mode,
            'roi_enabled': self.auto_roi_enabled,
            'active_roi_regions': len(self.roi_regions),
            'history_size': len(self.detection_history)
        }
    
    def set_performance_mode(self, mode: str):
        """Set detection performance mode"""
        if mode in ["fast", "balanced", "quality"]:
            self.performance_mode = mode
            self.logger.info(f"Detection performance mode set to: {mode}")
            
            # Adjust detection interval based on mode
            if mode == "fast":
                self.detection_interval = 0.05  # 20 FPS
            elif mode == "balanced":
                self.detection_interval = 0.1   # 10 FPS
            else:  # quality
                self.detection_interval = 0.2   # 5 FPS
    
    def toggle_roi_optimization(self, enabled: bool):
        """Toggle ROI optimization"""
        self.auto_roi_enabled = enabled
        if enabled and self.game_window_region:
            self._initialize_roi_regions()
        else:
            self.roi_regions = []
        
        self.logger.info(f"ROI optimization {'enabled' if enabled else 'disabled'}")
    
    def cleanup(self):
        """Clean up detection system resources"""
        try:
            if self.executor:
                self.executor.shutdown(wait=True)
                self.executor = None
            
            # Clear caches
            self.last_screenshot = None
            self.detection_history = []
            self.roi_regions = []
            
            self.logger.info("Detection system cleaned up")
            
        except Exception as e:
            self.logger.error(f"Error during detection cleanup: {e}")