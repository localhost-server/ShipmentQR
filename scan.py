import streamlit as st
import cv2
from pyzbar.pyzbar import decode
import numpy as np

def main():
    st.title("QR Code Scanner")
    
    # Add description
    st.write("This app scans QR codes using your webcam and displays the content.")
    
    # Create a placeholder for the camera feed
    video_placeholder = st.empty()
    
    # Create a placeholder for the QR code result
    result_placeholder = st.empty()
    
    # Button to start/stop scanning
    start_button = st.button("Start/Stop Scanning")
    
    # Session state to track scanning status
    if 'scanning' not in st.session_state:
        st.session_state.scanning = False
    
    if start_button:
        st.session_state.scanning = not st.session_state.scanning
    
    # Initialize webcam if scanning is active
    if st.session_state.scanning:
        cap = cv2.VideoCapture(0)
        
        # Check if the webcam is opened correctly
        if not cap.isOpened():
            st.error("Error: Could not open webcam. Please make sure your webcam is connected and permissions are granted.")
            return
        
        try:
            while st.session_state.scanning:
                # Read frame from webcam
                ret, frame = cap.read()
                
                if not ret:
                    st.error("Failed to capture image from webcam")
                    break
                
                # Convert to RGB for display in Streamlit
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Display the frame
                video_placeholder.image(rgb_frame, channels="RGB", use_column_width=True)
                
                # Try to decode QR codes
                decoded_objects = decode(rgb_frame)
                
                # If QR code detected
                if decoded_objects:
                    for obj in decoded_objects:
                        # Extract QR code data
                        qr_data = obj.data.decode('utf-8')
                        
                        # Get coordinates of QR code
                        points = obj.polygon
                        if len(points) > 4:
                            hull = cv2.convexHull(np.array([point for point in points], dtype=np.float32))
                            points = hull
                        
                        # Draw boundary around QR code (for display purposes)
                        n = len(points)
                        for j in range(n):
                            cv2.line(rgb_frame, tuple(points[j]), tuple(points[(j + 1) % n]), (0, 255, 0), 3)
                        
                        # Update the display with the boundary
                        video_placeholder.image(rgb_frame, channels="RGB", use_column_width=True)
                        
                        # Display the QR code content
                        result_placeholder.subheader("QR Code Content:")
                        result_placeholder.code(qr_data)
                        
                        # Pause for a moment to see the result
                        st.session_state.scanning = False
                        break
        
        finally:
            # Always release the webcam when done
            cap.release()
    else:
        video_placeholder.info("Click 'Start/Stop Scanning' to activate the webcam")

if __name__ == "__main__":
    main()