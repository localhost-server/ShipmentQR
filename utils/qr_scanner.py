import cv2
from pyzbar.pyzbar import decode
import numpy as np
import streamlit as st
import tempfile
import os
import time
from utils.image_processor import ImageProcessor
from utils.qr_data_parser import QRDataParser

class QRScanner:
    @staticmethod
    def scan_from_camera():
        """Scan QR code from camera input"""
        try:
            # Check camera state
            if ('active_tab' not in st.session_state or 
                st.session_state.active_tab != 'scan' or 
                'camera_active' not in st.session_state or 
                not st.session_state.camera_active):
                return None, None

            # Get camera input
            camera_image = st.camera_input("Point camera at QR code", key="qr_scanner")
            if camera_image is None:
                return None, None

            # Process image
            try:
                # Convert image to OpenCV format
                bytes_data = camera_image.getvalue()
                nparr = np.frombuffer(bytes_data, np.uint8)
                frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                if frame is None:
                    return None, "Failed to process camera image. Please try again."

                # Try different image processing methods
                processed_images = ImageProcessor.try_different_processing(frame)
                qr_codes = []
                
                # Try to find QR codes in each processed image
                for processed_image in processed_images:
                    found_codes = decode(processed_image)
                    if found_codes:
                        qr_codes = found_codes
                        break

                if not qr_codes:
                    return None, "No QR code found. Please ensure good lighting and hold the camera steady."

                # Parse QR code data
                results = []
                for qr_code in qr_codes:
                    try:
                        data = qr_code.data.decode('utf-8')
                        parsed_data = QRDataParser.parse_data(data)
                        if parsed_data and 'error' not in parsed_data:
                            results.append(parsed_data)
                    except Exception as e:
                        st.warning(f"Failed to process one QR code: {str(e)}")
                        continue

                if not results:
                    return None, "QR code found but data format is invalid."

                return results, None

            except Exception as e:
                return None, f"Camera processing error: {str(e)}. Please check camera permissions and try again."

        except Exception as e:
            return None, f"Error scanning QR code: {str(e)}"

    @staticmethod
    def scan_from_image(uploaded_file):
        """Scan QR code from uploaded image file"""
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_path = tmp_file.name

            try:
                # Read image
                image = cv2.imread(tmp_path)
                if image is None:
                    raise Exception("Failed to read image file")

                # Try different image processing methods
                processed_images = ImageProcessor.try_different_processing(image)
                qr_codes = []
                
                # Try to find QR codes in each processed image
                for processed_image in processed_images:
                    found_codes = decode(processed_image)
                    if found_codes:
                        qr_codes = found_codes
                        break

                if not qr_codes:
                    return None, "No QR code found. Please ensure the image is clear and well-lit."

                # Parse QR code data
                results = []
                for qr_code in qr_codes:
                    try:
                        data = qr_code.data.decode('utf-8')
                        parsed_data = QRDataParser.parse_data(data)
                        if parsed_data and 'error' not in parsed_data:
                            results.append(parsed_data)
                    except Exception as e:
                        st.warning(f"Failed to process one QR code: {str(e)}")
                        continue

                if not results:
                    return None, "QR code found but data format is invalid."

                return results, None

            finally:
                # Clean up temporary file
                try:
                    os.unlink(tmp_path)
                except:
                    pass

        except Exception as e:
            return None, f"Error scanning QR code: {str(e)}"

    @staticmethod
    def format_scan_result(result):
        """Format the scan result for display"""
        return QRDataParser.format_result(result)
