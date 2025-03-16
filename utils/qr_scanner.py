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
            bytes_data = camera_image.getvalue()
            nparr = np.frombuffer(bytes_data, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            # Convert to grayscale for QR detection
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Scan for QR codes
            qr_codes = decode(gray)
            
            if not qr_codes:
                return None, "No QR code found in camera frame"
            
            # Process results
            results = []
            for qr_code in qr_codes:
                data = qr_code.data.decode('utf-8')
                results.append(QRScanner._parse_qr_data(data))
            
            return results, None

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
        try:
            lines = data.split('\n')
            result = {'sender': {}, 'artist': {}}
            current_section = None

            for line in lines:
                line = line.strip()
                if not line:
                    continue

                if line == 'SR:':
                    current_section = 'sender'
                    continue
                elif line == 'AT:':
                    current_section = 'artist'
                    continue

                if current_section and ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip()
                    value = value.strip()

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
