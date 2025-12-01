import cv2
import os
from datetime import datetime
from config import Config

class Vision:
    def __init__(self, camera_index=0):
        self.camera_index = camera_index
        self.cap = None
        self.image_dir = Config.IMAGE_DIR
        
        # Create image directory if it doesn't exist
        os.makedirs(self.image_dir, exist_ok=True)
        
        # Initialize camera
        self._init_camera()
    
    def _init_camera(self):
        """Initialize camera connection"""
        try:
            self.cap = cv2.VideoCapture(self.camera_index)
            
            # Set camera properties for better quality
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            self.cap.set(cv2.CAP_PROP_FPS, 30)
            
            # Test capture
            ret, _ = self.cap.read()
            if ret:
                print("✅ Camera initialized successfully")
            else:
                print("⚠️ Camera connected but failed to capture")
                
        except Exception as e:
            print(f"❌ Camera initialization error: {e}")
            self.cap = None
    
    def capture_frame(self, save=True):
        """
        Capture a single frame from camera
        
        Args:
            save (bool): Whether to save the image
            
        Returns:
            str: Path to saved image, or None if error
        """
        if self.cap is None or not self.cap.isOpened():
            print("❌ Camera not available")
            return None
        
        try:
            ret, frame = self.cap.read()
            
            if not ret:
                print("❌ Failed to capture frame")
                return None
            
            if save:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                image_path = os.path.join(self.image_dir, f"capture_{timestamp}.jpg")
                
                cv2.imwrite(image_path, frame)
                print(f"📸 Image saved: {image_path}")
                
                return image_path
            
            return frame
            
        except Exception as e:
            print(f"❌ Capture error: {e}")
            return None
    
    def get_latest_image(self):
        """Get path to most recently captured image"""
        try:
            images = [f for f in os.listdir(self.image_dir) if f.endswith('.jpg')]
            if not images:
                return None
            
            images.sort(reverse=True)
            return os.path.join(self.image_dir, images[0])
            
        except Exception as e:
            print(f"❌ Error getting latest image: {e}")
            return None
    
    def show_live_feed(self, duration=5):
        """
        Show live camera feed for testing
        
        Args:
            duration (int): Seconds to display feed
        """
        if self.cap is None:
            print("❌ Camera not available")
            return
        
        print(f"📹 Showing live feed for {duration} seconds...")
        print("Press 'q' to quit early")
        
        start_time = datetime.now()
        
        while (datetime.now() - start_time).seconds < duration:
            ret, frame = self.cap.read()
            
            if not ret:
                break
            
            cv2.imshow('Camera Feed', frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        cv2.destroyAllWindows()
    
    def cleanup(self):
        """Release camera resources"""
        if self.cap is not None:
            self.cap.release()
            print("✅ Camera released")


# Test the module
if __name__ == "__main__":
    vision = Vision()
    
    print("\n📸 Vision System Test")
    
    # Test 1: Capture single frame
    print("\n1. Capturing frame...")
    image_path = vision.capture_frame()
    
    if image_path:
        print(f"✅ Image captured: {image_path}")
    
    # Test 2: Get latest image
    print("\n2. Getting latest image...")
    latest = vision.get_latest_image()
    print(f"Latest image: {latest}")
    
    # Test 3: Show live feed (comment out if running headless)
    # print("\n3. Showing live feed...")
    # vision.show_live_feed(duration=3)
    
    # Cleanup
    vision.cleanup()
