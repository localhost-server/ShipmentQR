# Artist QR Code Generator

A Streamlit web application that generates QR codes for shipping information, combining sender and artist details.

## Features

- Configure sender information in Settings
- Upload CSV or Excel files for artist information
- Generate QR codes with combined sender and artist details
- Download individual QR codes
- View QR code history
- Clear history functionality

## QR Code Format

Each QR code contains:
```
SR:
NM: [Sender Name]
ADD: [Address Line 1]
CT: [City]
STT: [State]
CD: [Zip]

AT:
NM: [Artist Name]
PH: [Phone if provided]
ADD: [Address if provided]
```

## Required Setup

1. Configure Sender Information in Settings tab:
   - Name
   - Address Line 1
   - City
   - State
   - Zip Code

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

3. First-time Setup:
   - Go to Settings tab
   - Enter sender information
   - Save settings

4. Generate QR Codes:
   - Upload your spreadsheet (CSV or Excel) with artist information
   - View generated QR codes immediately
   - Download individual QR codes

5. View History:
   - Switch to View QR Codes tab to see all generated codes
   - QR codes are sorted by generation time (newest first)
   - Clear history with one click when needed

## Project Structure

```
QRGen/
├── app.py              # Main Streamlit application
├── requirements.txt    # Project dependencies
├── settings.json      # Sender information storage
└── utils/
    ├── __init__.py
    ├── data_handler.py # Download functionality
    ├── db_handler.py   # Database operations
    └── qr_generator.py # QR code generation
```

## Dependencies

- streamlit==1.32.0
- pandas==2.2.0
- qrcode==7.4.2
- Pillow==10.2.0
- openpyxl==3.1.2

## License

MIT License
