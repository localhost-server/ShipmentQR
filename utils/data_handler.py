def generate_download_link(img_base64: str, filename: str) -> str:
    """Generate HTML download link for QR code image."""
    return f'<a href="data:image/png;base64,{img_base64}" download="{filename}">Download QR</a>'
