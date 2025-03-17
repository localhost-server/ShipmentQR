import qrcode
import base64
from io import BytesIO
import uuid
import pandas as pd
from datetime import datetime

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

def generate_download_link(img_base64: str, filename: str) -> str:
    """Generate HTML download link for QR code image."""
    return f'<a href="data:image/png;base64,{img_base64}" download="{filename}">Download QR</a>'

def process_upload_data(df: pd.DataFrame, sender_settings: dict) -> list:
    """Process uploaded data and generate QR codes."""
    entries = []
    
    for index, row in df.iterrows():
        # Generate reference ID
        ref_id = str(uuid.uuid4())[:8]
        
        # Combine address fields
        address_parts = []
        address_fields = ['Address: Address Line 1', 'Address: Address Line 2', 'Address: City',
                       'Address: State', 'Address: Zip/Postal Code', 'Address: Country']
        
        for field in address_fields:
            if field in row and pd.notna(row[field]) and str(row[field]).strip():
                address_parts.append(str(row[field]).strip())
        
        combined_address = ', '.join(address_parts)

        # Generate QR content
        qr_content = create_qr_content(
            sender_settings,
            {
                'name': row['Artist Name'],
                'phone': row.get('Phone', ''),
                'address': combined_address
            }
        )
        
        qr_code = generate_qr_code(qr_content)
        
        entry = {
            'reference_id': ref_id,
            'data': {
                'sender': sender_settings,
                'Artist Name': row['Artist Name'],
                'Phone': row.get('Phone', ''),
                'Address': combined_address
            },
            'qr_code': qr_code,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        entries.append(entry)
    
    return entries

def create_qr_content(sender_info: dict, artist_info: dict) -> str:
    """Create QR code content string from sender and artist information."""
    return (
        f"SR:\nNM: {sender_info['name']}\nADD: {sender_info['address']}\n"
        f"CT: {sender_info['city']}\nSTT: {sender_info['state']}\n"
        f"CD: {sender_info['zip']}\n\nAT:\nNM: {artist_info['name']}\n"
        f"PH: {artist_info.get('phone', '')}\nADD: {artist_info.get('address', '')}"
    )
