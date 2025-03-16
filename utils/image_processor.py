import cv2
import numpy as np

class ImageProcessor:
    @staticmethod
    def preprocess_image(image):
        """Apply various image processing techniques to improve QR code detection"""
        try:
            # Resize for better resolution
            image = cv2.resize(image, None, fx=1.5, fy=1.5)
            
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Apply Gaussian blur to reduce noise
            gray = cv2.GaussianBlur(gray, (5, 5), 0)
            
            # Improve contrast
            gray = cv2.equalizeHist(gray)
            
            return gray
        except Exception as e:
            raise Exception(f"Image preprocessing failed: {str(e)}")

    @staticmethod
    def try_different_processing(image):
        """Try different image processing techniques"""
        processed_images = []
        
        try:
            # Original grayscale
            processed_images.append(cv2.cvtColor(image, cv2.COLOR_BGR2GRAY))
            
            # Enhanced processing
            enhanced = ImageProcessor.preprocess_image(image)
            processed_images.append(enhanced)
            
            # Binary threshold
            _, binary = cv2.threshold(
                cv2.cvtColor(image, cv2.COLOR_BGR2GRAY),
                127, 255, cv2.THRESH_BINARY
            )
            processed_images.append(binary)
            
            return processed_images
        except Exception as e:
            raise Exception(f"Image processing attempts failed: {str(e)}")
