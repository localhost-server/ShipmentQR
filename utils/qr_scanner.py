import cv2
from pyzbar.pyzbar import decode
import numpy as np
import streamlit as st
import tempfile
import os
import time


class QRScanner:
    @staticmethod
    def scan_from_camera():
        try:
            # Only initialize camera in scan tab when active
            if ('active_tab' not in st.session_state or 
                st.session_state.active_tab != 'scan' or 
                'camera_active' not in st.session_state or 
                not st.session_state.camera_active):
                return None, None

            camera_image = st.camera_input(" ")
            if camera_image is None:
                return None, None

            # Process the image
            try:
                bytes_data = camera_image.getvalue()
                st.info("Processing image...")
                nparr = np.frombuffer(bytes_data, np.uint8)
                frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                
                if frame is None:
                    st.error("Failed to decode image")
                    return None, "Failed to process camera image"
                
                st.info("Processing image...")
                # First normalize the image a bit
                frame = cv2.resize(frame, None, fx=1.5, fy=1.5, interpolation=cv2.INTER_CUBIC)
                
                # Convert to grayscale
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                
                # Apply adaptive thresholding
                binary = cv2.adaptiveThreshold(
                    gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                    cv2.THRESH_BINARY, 21, 10
                )
                
                # Define detection methods with their parameters
                detection_methods = [
                    (frame, "original"),
                    (gray, "grayscale"),
                    (binary, "binary"),
                    (cv2.GaussianBlur(gray, (5, 5), 0), "blurred"),
                    (cv2.bilateralFilter(gray, 9, 75, 75), "bilateral_filtered"),
                ]
                
                qr_codes = None
                method_used = None
                
                for img, method in detection_methods:
                    try:
                        qr_codes = decode(img)
                        if qr_codes:
                            method_used = method
                            st.success(f"QR code found using {method} method")
                            break
                    except Exception as e:
                        st.warning(f"Error with {method} method: {str(e)}")
                        continue

                if qr_codes:
                    st.info(f"Raw QR code data found (hex): {qr_codes[0].data.hex()}")
                    
            except Exception as e:
                st.error(f"Image processing error: {str(e)}")
                return None, f"Failed to process image: {str(e)}"
            
            if not qr_codes:
                return None, "No QR code found in camera frame"
            
            # Process results
            results = []
            for qr_code in qr_codes:
                try:
                    # Try UTF-8 decoding with error handling
                    try:
                        data = qr_code.data.decode('utf-8')
                        # Normalize line endings
                        data = data.replace('\r\n', '\n').replace('\r', '\n')
                        st.info("Successfully decoded using UTF-8")
                    except UnicodeDecodeError as e:
                        st.error(f"Failed to decode QR data: {str(e)}")
                        st.info(f"Raw QR data (hex): {qr_code.data.hex()}")
                        continue

                    if not data:
                        st.warning("Empty QR code data")
                        continue
                    
                    st.info(f"Raw QR data: {repr(data)}")  # Use repr to show escape characters
                    parsed_data = QRScanner._parse_qr_data(data.replace('\r\n', '\n'))  # Normalize line endings
                    if parsed_data and not 'error' in parsed_data:
                        st.success("Successfully parsed QR data")
                        results.append(parsed_data)
                    else:
                        st.warning(f"Failed to parse QR data: {parsed_data.get('error', 'Unknown error')}")
                        
                except Exception as e:
                    st.error(f"QR decode error: {str(e)}")
                    continue
            
            if results:
                st.success(f"Successfully decoded QR code using {method_used} method")
                return results, None
            return None, "Could not decode QR code data"

        except Exception as e:
            return None, f"Error scanning QR code: {str(e)}"

    @staticmethod
    def scan_from_image(uploaded_file):
        try:
            # Create a temporary file to save the uploaded image
            with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_path = tmp_file.name

            # Read the image using OpenCV
            image = cv2.imread(tmp_path)
            if image is None:
                raise Exception("Failed to read image")

            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

            # Scan for QR codes
            qr_codes = decode(gray)

            # Clean up temporary file
            os.unlink(tmp_path)

            if not qr_codes:
                return None, "No QR code found in the image"

            # Process results
            results = []
            for qr_code in qr_codes:
                data = qr_code.data.decode('utf-8')
                results.append(QRScanner._parse_qr_data(data))

            return results, None

        except Exception as e:
            return None, f"Error scanning QR code: {str(e)}"

    @staticmethod
    def _parse_qr_data(data):
        """Parse the QR code data into a structured format"""
        def log_debug(msg):
            print(f"QR Parser Debug: {msg}")
            st.info(msg)

        try:
            log_debug("Parsing QR data...")
            log_debug(f"Raw data to parse: {data}")
            
            lines = data.split('\n')
            result = {'sender': {}, 'artist': {}}
            current_section = None

            for line_num, line in enumerate(lines):
                line = line.strip()
                if not line:
                    continue

                log_debug(f"Processing line {line_num + 1}: {line}")

                if line == 'SR:':
                    log_debug("Found sender section")
                    current_section = 'sender'
                    continue
                elif line == 'AT:':
                    log_debug("Found artist section")
                    current_section = 'artist'
                    continue

                if current_section and ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip()
                    value = value.strip()
                    log_debug(f"Section: {current_section}, Key: {key}, Value: {value}")

                    if current_section == 'sender':
                        if key == 'NM':
                            result['sender']['name'] = value
                        elif key == 'ADD':
                            result['sender']['address'] = value
                        elif key == 'CT':
                            result['sender']['city'] = value
                        elif key == 'STT':
                            result['sender']['state'] = value
                        elif key == 'CD':
                            result['sender']['zip'] = value

                    elif current_section == 'artist':
                        if key == 'NM':
                            result['artist']['name'] = value
                        elif key == 'PH':
                            result['artist']['phone'] = value
                        elif key == 'ADD':
                            result['artist']['address'] = value
            
            log_debug(f"Final parsed result: {result}")
            return result
        except Exception as e:
            return {'error': f"Failed to parse QR data: {str(e)}"}

    @staticmethod
    def format_scan_result(result):
        """Format the scan result for display"""
        if not result or 'error' in result:
            return "Failed to parse QR code data"

        formatted = []
        
        # Sender Information
        if result.get('sender'):
            formatted.append("📤 Sender Information")
            sender = result['sender']
            if sender.get('name'):
                formatted.append(f"Name: {sender['name']}")
            if sender.get('address'):
                formatted.append(f"Address: {sender['address']}")
            if all(sender.get(k) for k in ['city', 'state', 'zip']):
                formatted.append(f"Location: {sender['city']}, {sender['state']} {sender['zip']}")
            formatted.append("")

        # Artist Information
        if result.get('artist'):
            formatted.append("🎨 Artist Information")
            artist = result['artist']
            if artist.get('name'):
                formatted.append(f"Name: {artist['name']}")
            if artist.get('phone'):
                formatted.append(f"Phone: {artist['phone']}")
            if artist.get('address'):
                formatted.append(f"Address: {artist['address']}")

        return "\n".join(formatted)
