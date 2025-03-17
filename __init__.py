# Package initialization file
from .qr_generator import generate_qr_code
from .data_handler import generate_download_link

__all__ = [
    'generate_qr_code',
    'generate_download_link'
]
