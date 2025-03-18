from flask import Flask, render_template, request, jsonify
import os
import platform
import logging
from escpos import printer as escpos_printer
import usb.core

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Global printer status
printer_available = False
printer_info = None

def detect_printer():
    """Detect the USB thermal printer and initialize it"""
    global printer_available, printer_info
    
    try:
        # Specific Neiko/Beeprt PL70e-BT vendor/product ID from system_profiler output
        neiko_vendor_id = 0x09c6  # Vendor ID for your Beeprt Printer
        neiko_product_id = 0x0426  # Product ID for your printer
        
        # Try the specific printer first
        device = usb.core.find(idVendor=neiko_vendor_id, idProduct=neiko_product_id)
        if device is not None:
            logger.info(f"Found Neiko/Beeprt PL70e-BT printer with vendor ID: {neiko_vendor_id:04x}, product ID: {neiko_product_id:04x}")
            printer_info = {
                'vendor_id': neiko_vendor_id,
                'product_id': neiko_product_id,
                'in_ep': 0x81,  # Default input endpoint
                'out_ep': 0x03  # Default output endpoint
            }
            printer_available = True
            return True
            
        # Fall back to standard vendor/product IDs for common thermal printers
        vendor_ids = [0x0416, 0x04b8, 0x067b, 0x0483, 0x1504, 0x1cb0, 0x0dd4]
        product_ids = [0x5011, 0x0202, 0x2303, 0x5740, 0x0006, 0x0003, 0x0180]
        
        # Try to find the printer with different vendor/product ID combinations
        for vendor_id in vendor_ids:
            for product_id in product_ids:
                try:
                    # Check if device exists
                    device = usb.core.find(idVendor=vendor_id, idProduct=product_id)
                    if device is not None:
                        logger.info(f"Found printer with vendor ID: {vendor_id:04x}, product ID: {product_id:04x}")
                        printer_info = {
                            'vendor_id': vendor_id,
                            'product_id': product_id,
                            'in_ep': 0x81,  # Default input endpoint
                            'out_ep': 0x03  # Default output endpoint
                        }
                        printer_available = True
                        return True
                except Exception as e:
                    continue
        
        logger.warning("No compatible printer found")
        printer_available = False
        return False
    
    except Exception as e:
        logger.error(f"Error detecting printer: {str(e)}")
        printer_available = False
        return False
        
def get_printer():
    """Get a connection to the printer based on the detected printer info"""
    if not printer_available or not printer_info:
        logger.warning("Attempted to get printer but no printer is available")
        return None
    
    try:
        # Create USB printer connection with the detected parameters
        printer = escpos_printer.Usb(
            printer_info['vendor_id'],
            printer_info['product_id'],
            0,  # USB interface number (usually 0)
            printer_info['in_ep'],
            printer_info['out_ep']
        )
        return printer
    except Exception as e:
        logger.error(f"Error connecting to printer: {str(e)}")
        return None

def print_qr_result(formatted_result):
    """Print the QR code result to the thermal printer"""
    if not printer_available:
        logger.info("Print requested but no printer available")
        return False
    
    try:
        # Get printer connection
        p = get_printer()
        if not p:
            return False
        
        # Format and print the result
        p.set(align='center', font='a', width=1, height=1, bold=True)
        p.text("QR SCAN RESULT\n\n")
        
        p.set(align='left', font='a', width=1, height=1, bold=False)
        
        # Print the formatted sections
        sections = formatted_result.split('\n')
        for section in sections:
            if section.startswith('📤') or section.startswith('🎨'):
                # Section header
                p.set(bold=True)
                p.text(f"{section}\n")
                p.set(bold=False)
            elif section.strip() == '':
                # Empty line
                p.text("\n")
            else:
                # Regular content
                p.text(f"{section}\n")
        
        # Add footer
        p.text("\n")
        p.set(align='center')
        p.text("--------------------------------\n")
        p.text("Thank you for using QR Scanner\n\n\n")
        
        # Cut the paper (if supported)
        p.cut()
        
        logger.info("Successfully printed QR scan result")
        return True
    
    except Exception as e:
        logger.error(f"Error printing: {str(e)}")
        return False


app = Flask(__name__)

# QR data parser class
class QRDataParser:
    @staticmethod
    def parse_data(data):
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
    def format_result(result):
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

@app.route('/')
def index():
    """Render the main application page"""
    return render_template('index.html')

@app.route('/process_qr', methods=['POST'])
def process_qr():
    """Process QR code data received from client and print automatically if printer available"""
    data = request.json.get('qr_data')
    if not data:
        return jsonify({'error': 'No QR data received'}), 400
    
    # Parse and format QR data
    parsed_data = QRDataParser.parse_data(data)
    formatted_result = QRDataParser.format_result(parsed_data)
    
    # Print the formatted result automatically if printer is available
    print_success = False
    if printer_available:
        print_success = print_qr_result(formatted_result)
    
    # Print the formatted result to the terminal
    print("\n" + "="*50)
    print("QR CODE SCAN RESULT:")
    print("="*50)
    print(formatted_result)
    print("="*50 + "\n")
    
    # Include printer status in the response
    return jsonify({
        'success': True,
        'formatted_result': formatted_result,
        'printer_available': printer_available,
        'print_success': print_success
    })

# Create templates directory if it doesn't exist
os.makedirs('templates', exist_ok=True)

# Create the HTML template with dark theme
with open('templates/index.html', 'w') as f:
    f.write("""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>QR Code Scanner</title>
    <style>
        :root {
            --bg-color: #121212;
            --surface-color: #1e1e1e;
            --primary-color: #7b68ee;
            --primary-dark: #6a5acd;
            --secondary-color: #536dfe;
            --success-color: #4CAF50;
            --success-dark: #3d8c40;
            --text-primary: #ffffff;
            --text-secondary: #b0b0b0;
            --border-color: #2c2c2c;
            --highlight-color: #00e676;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            max-width: 800px;
            margin: 0 auto;
            background-color: var(--bg-color);
            color: var(--text-primary);
        }
        
        h1 {
            text-align: center;
            color: var(--text-primary);
            margin-bottom: 30px;
        }
        
        #video-container {
            width: 100%;
            max-width: 640px;
            margin: 0 auto;
            position: relative;
            overflow: hidden;
            border-radius: 12px;
            box-shadow: 0 8px 16px rgba(0,0,0,0.4);
            border: 1px solid var(--border-color);
            background-color: #000;
        }
        
        #qr-video {
            width: 100%;
            height: auto;
            background-color: #000;
        }
        
        #qr-canvas {
            display: none;
        }
        
        #qr-result {
            margin-top: 25px;
            padding: 20px;
            border: 1px solid var(--border-color);
            border-radius: 12px;
            background-color: var(--surface-color);
            white-space: pre-line;
            display: none;
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
            line-height: 1.6;
        }
        
        #status-message {
            text-align: center;
            margin: 20px 0;
            font-weight: 500;
            color: var(--text-secondary);
            background-color: var(--surface-color);
            padding: 10px;
            border-radius: 30px;
            max-width: 80%;
            margin-left: auto;
            margin-right: auto;
        }
        
        #captured-image {
            width: 100%;
            max-width: 640px;
            margin: 25px auto;
            display: none;
            border-radius: 12px;
            box-shadow: 0 8px 16px rgba(0,0,0,0.4);
            border: 1px solid var(--border-color);
        }
        
        button {
            padding: 14px 28px;
            background-color: var(--primary-color);
            color: white;
            border: none;
            border-radius: 30px;
            font-size: 16px;
            font-weight: 500;
            cursor: pointer;
            display: block;
            margin: 25px auto;
            transition: all 0.3s ease;
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        }
        
        button:hover {
            background-color: var(--primary-dark);
            transform: translateY(-2px);
            box-shadow: 0 6px 12px rgba(0,0,0,0.3);
        }
        
        #rescan-button {
            display: none;
            background-color: var(--secondary-color);
        }
        
        #rescan-button:hover {
            background-color: #4a62e5;
        }

        /* Styles for the formatted results */
        #qr-result {
            font-size: 15px;
        }

        #qr-result strong {
            color: var(--text-primary);
        }

        /* QR info sections */
        #qr-result p:first-child,
        #qr-result p:nth-of-type(3) {
            font-weight: bold;
            color: var(--primary-color);
            font-size: 18px;
            margin-top: 15px;
            margin-bottom: 10px;
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 5px;
        }
    </style>
</head>
<body>
    <h1>QR Code Scanner</h1>
    
    <div id="video-container">
        <video id="qr-video" autoplay playsinline></video>
    </div>
    <canvas id="qr-canvas"></canvas>
    
    <div id="status-message">Starting camera...</div>
    
    <img id="captured-image" alt="Captured QR Code">
    
    <div id="qr-result"></div>
    
    <button id="rescan-button">Scan New QR Code</button>
    
    <!-- Include jsQR library for QR detection -->
    <script src="https://cdn.jsdelivr.net/npm/jsqr@1.4.0/dist/jsQR.min.js"></script>
    
    <script>
        // DOM elements
        const video = document.getElementById('qr-video');
        const canvas = document.getElementById('qr-canvas');
        const ctx = canvas.getContext('2d');
        const statusMessage = document.getElementById('status-message');
        const qrResult = document.getElementById('qr-result');
        const capturedImage = document.getElementById('captured-image');
        const rescanButton = document.getElementById('rescan-button');
        
        // Scanner state
        let scanning = false;
        let scanInterval = null;
        let videoStream = null;
        
        // Initialize camera on page load
        document.addEventListener('DOMContentLoaded', startCamera);
        
        // Start the camera
        function startCamera() {
            statusMessage.textContent = "Requesting camera access...";
            
            // Get user's camera
            navigator.mediaDevices.getUserMedia({ 
                video: { 
                    facingMode: "environment",
                    width: { ideal: 640 },
                    height: { ideal: 480 }
                } 
            })
            .then(stream => {
                videoStream = stream;
                video.srcObject = stream;
                
                // Wait for video to be ready
                video.onloadedmetadata = () => {
                    video.play();
                    
                    // Set canvas size to match video
                    canvas.width = video.videoWidth;
                    canvas.height = video.videoHeight;
                    
                    // Start scanning
                    startScanning();
                };
            })
            .catch(err => {
                statusMessage.textContent = `Camera error: ${err.message}`;
                console.error("Camera error:", err);
            });
        }
        
        // Start QR code scanning
        function startScanning() {
            if (scanning) return;
            
            scanning = true;
            statusMessage.textContent = "Scanning for QR code...";
            video.style.display = 'block';
            capturedImage.style.display = 'none';
            qrResult.style.display = 'none';
            rescanButton.style.display = 'none';
            
            // Process video frames
            scanInterval = setInterval(scanVideoFrame, 100); // 10 frames per second
        }
        
        // Process a video frame to detect QR codes
        function scanVideoFrame() {
            if (!scanning) return;
            
            // Draw current video frame to canvas
            ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
            
            // Get image data for processing
            const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
            
            // Look for QR code in the image
            const code = jsQR(imageData.data, imageData.width, imageData.height, {
                inversionAttempts: "dontInvert"
            });
            
            if (code) {
                // QR code found!
                console.log("QR code detected:", code.data);
                
                // Stop scanning
                stopScanning();
                
                // Highlight the QR code on canvas
                highlightQR(code.location);
                
                // Display the captured image
                capturedImage.src = canvas.toDataURL('image/jpeg');
                capturedImage.style.display = 'block';
                video.style.display = 'none';
                
                // Process QR code data
                processQRData(code.data);
            }
        }
        
        // Stop scanning
        function stopScanning() {
            scanning = false;
            clearInterval(scanInterval);
            statusMessage.textContent = "QR Code detected!";
            rescanButton.style.display = 'block';
        }
        
        // Highlight the detected QR code
        function highlightQR(location) {
            // Draw the video frame again
            ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
            
            // Draw QR code boundary
            ctx.beginPath();
            ctx.moveTo(location.topLeftCorner.x, location.topLeftCorner.y);
            ctx.lineTo(location.topRightCorner.x, location.topRightCorner.y);
            ctx.lineTo(location.bottomRightCorner.x, location.bottomRightCorner.y);
            ctx.lineTo(location.bottomLeftCorner.x, location.bottomLeftCorner.y);
            ctx.lineTo(location.topLeftCorner.x, location.topLeftCorner.y);
            ctx.lineWidth = 4;
            ctx.strokeStyle = '#00e676';
            ctx.stroke();
            
            // Add timestamp
            const now = new Date();
            const timestamp = now.toLocaleString();
            ctx.font = '16px "Segoe UI", sans-serif';
            ctx.fillStyle = '#00e676';
            ctx.fillText(`Scanned: ${timestamp}`, 10, 30);
        }
        
        // Process QR code data with the backend
        function processQRData(data) {
            fetch('/process_qr', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ qr_data: data }),
            })
            .then(response => response.json())
            .then(result => {
                if (result.success) {
                    // Display formatted result
                    qrResult.textContent = result.formatted_result;
                    qrResult.style.display = 'block';
                } else {
                    qrResult.textContent = `Error: ${result.error}`;
                    qrResult.style.display = 'block';
                }
            })
            .catch(error => {
                console.error('Error processing QR data:', error);
                qrResult.textContent = `Failed to process QR code: ${error.message}`;
                qrResult.style.display = 'block';
            });
        }
        
        // Rescan button handler
        rescanButton.addEventListener('click', startScanning);
        
        // Clean up resources when page is unloaded
        window.addEventListener('beforeunload', () => {
            if (videoStream) {
                videoStream.getTracks().forEach(track => track.stop());
            }
        });
    </script>
</body>
</html>
    """)

if __name__ == '__main__':
    # Detect printer at startup
    printer_detected = detect_printer()
    if printer_detected:
        print(f"Printer detected and ready: {printer_info}")
    else:
        print("No compatible printer detected. Running in display-only mode.")
    
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
