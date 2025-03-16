import qrcode
from io import BytesIO
import base64

def generate_qr_code(data: str) -> str:
    """Generate a QR code for given data and return as base64 string."""
    qr = qrcode.QRCode(
        version=None,  # Let it auto-determine size based on data
        error_correction=qrcode.constants.ERROR_CORRECT_M,  # Medium error correction
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()
