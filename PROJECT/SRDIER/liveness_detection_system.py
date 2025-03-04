import cv2
import numpy as np
import os
import signal
import sys
from time import time

class LivenessDetector:
    def __init__(self):
        # Load OpenCV's pre-trained face cascade classifier
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        self.face_cascade = cv2.CascadeClassifier(cascade_path)
        if self.face_cascade.empty():
            raise ValueError("Error: Could not load face cascade classifier. Please check OpenCV installation.")
        
        # Initialize counters for blink detection
        self.blink_counter = 0
        self.previous_eye_state = True  # True for open, False for closed
        
        # Constants
        self.EYE_THRESHOLD = 0.3
        self.BLINK_CONSEC_FRAMES = 3
        
        # Movement detection
        self.previous_frame = None
        self.movement_threshold = 500
        self.last_movement_time = time()
        self.movement_timeout = 2.0  # seconds

    def detect_movement(self, frame):
        """Detect if there is movement in the frame"""
        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray, (21, 21), 0)
            
            if self.previous_frame is None:
                self.previous_frame = gray
                return True
            
            # Compute difference between current and previous frame
            frame_diff = cv2.absdiff(self.previous_frame, gray)
            self.previous_frame = gray
            
            # Calculate total movement
            movement = np.sum(frame_diff)
            
            if movement > self.movement_threshold:
                self.last_movement_time = time()
                return True
                
            # Check if no movement for too long
            if time() - self.last_movement_time > self.movement_timeout:
                return False
                
            return True
            
        except Exception as e:
            print(f"Error in detect_movement: {str(e)}")
            return True

    def detect_eyes(self, frame):
        """Detect eyes in the frame using simple image processing"""
        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
            
            for (x, y, w, h) in faces:
                # Get the eye region (approximate)
                eye_region_h = int(h/3)
                eye_region_w = int(w/3)
                eye_y = y + int(h/4)
                
                # Left and right eye regions
                left_eye = gray[eye_y:eye_y+eye_region_h, x+eye_region_w:x+2*eye_region_w]
                right_eye = gray[eye_y:eye_y+eye_region_h, x+2*eye_region_w:x+3*eye_region_w]
                
                # Calculate average intensity
                if left_eye.size > 0 and right_eye.size > 0:
                    left_intensity = np.mean(left_eye)
                    right_intensity = np.mean(right_eye)
                    avg_intensity = (left_intensity + right_intensity) / 2
                    
                    # Return True if eyes are likely open (higher intensity)
                    return avg_intensity > 128
            
            return True  # Default to open if no face detected
        except Exception as e:
            print(f"Error in detect_eyes: {str(e)}")
            return True

    def detect_liveness(self, frame):
        """Detect if the input is from a live person or a photo"""
        try:
            # Check for movement
            has_movement = self.detect_movement(frame)
            
            # Check eye state
            current_eye_state = self.detect_eyes(frame)
            
            # Detect blink (transition from open to closed to open)
            if self.previous_eye_state and not current_eye_state:
                self.blink_counter += 1
            
            self.previous_eye_state = current_eye_state
            
            # Determine if the input is live based on movement and blinks
            is_live = has_movement and self.blink_counter > 0
            
            # Return status and additional info
            return is_live, self.blink_counter, has_movement
            
        except Exception as e:
            print(f"Error in detect_liveness: {str(e)}")
            return False, 0, False

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    print("\nExiting program...")
    # Cleanup
    cv2.destroyAllWindows()
    sys.exit(0)

def main():
    # Set up signal handler for Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        # Initialize detector
        detector = LivenessDetector()
        
        # Start video capture
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("Error: Could not open camera! Please check if camera is connected.")
            return

        print("Liveness detection started. Press 'q' to quit or Ctrl+C to exit.")
        print("Blink a few times to verify liveness.")
        
        while True:
            try:
                ret, frame = cap.read()
                if not ret:
                    print("Error: Could not read frame! Check camera connection.")
                    break
                    
                # Check liveness
                is_live, blink_count, has_movement = detector.detect_liveness(frame)
                
                # Determine status message
                if not has_movement:
                    status = "Photo Detected (No Movement)"
                    color = (0, 0, 255)  # Red
                elif blink_count == 0:
                    status = "Waiting for Eye Blink..."
                    color = (0, 165, 255)  # Orange
                else:
                    status = f"Live Person (Blinks: {blink_count})"
                    color = (0, 255, 0)  # Green
                
                # Draw status on frame
                cv2.putText(frame, f"Status: {status}", (10, 30), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
                
                # Show frame
                cv2.imshow("Liveness Detection", frame)
                
                # Break loop on 'q' press
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    print("\nExiting program...")
                    break

            except Exception as e:
                print(f"Error in main loop: {str(e)}")
                break

    except Exception as e:
        print(f"Error: {str(e)}")
    
    finally:
        # Cleanup
        if 'cap' in locals():
            cap.release()
        cv2.destroyAllWindows()
        print("Program terminated.")

if __name__ == "__main__":
    main() 