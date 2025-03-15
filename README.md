# Artist QR Code Generator

A Streamlit web application that generates QR codes for artist shipping information.

## Features

- Upload CSV or Excel files
- Generate QR codes for each artist
- Download or print QR codes
- Combines address fields automatically
- View all QR codes directly without expanding
- History tab with timestamps
- Session-based history tracking

## Required Spreadsheet Fields

- Artist Name (required)
- Phone (optional)
- Address Fields (optional):
  - Address: Address Line 1
  - Address: Address Line 2
  - Address: City
  - Address: State
  - Address: Zip/Postal Code
  - Address: Country
  
All address fields will be combined into a single address string in the QR code.

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/QRGen.git
cd QRGen
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Run the application:
```bash
streamlit run app.py
```

2. Open your browser and go to `http://localhost:8501`

3. Generate QR Codes:
   - Upload your spreadsheet (CSV or Excel) with artist information
   - View generated QR codes immediately
   - Download or print individual QR codes

4. View History:
   - Switch to History tab to see all generated QR codes
   - QR codes are sorted by generation time (newest first)
   - All QR codes remain available during the session

## Project Structure

```
QRGen/
├── app.py              # Main Streamlit application
├── requirements.txt    # Project dependencies
└── utils/
    ├── __init__.py
    ├── data_handler.py # Download functionality
    └── qr_generator.py # QR code generation
```

## QR Code Data Format

Each QR code contains:
- Reference ID (automatically generated)
- Artist Name
- Phone (if provided)
- Combined Address (if address fields are provided)

## License

MIT License
