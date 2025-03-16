import qrcode
from io import BytesIO
import base64

def generate_qr_code(data: str) -> str:
    """Generate a QR code for given data and return as base64 string."""
    # Normalize line endings to Linux style
    data = data.replace('\r\n', '\n').replace('\r', '\n')
    
    qr = qrcode.QRCode(
        version=None,  # Let it auto-determine size based on data
        error_correction=qrcode.constants.ERROR_CORRECT_H,  # High error correction
        box_size=12,  # Larger box size for better readability
        border=4,
    )
    qr.add_data(data, optimize=0)  # Disable optimization to maintain exact data format
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()
