# QR Code Generator

A Streamlit web application that generates QR codes from spreadsheet data.

## Features

- Upload CSV or Excel files
- Automatically converts each row to QR codes
- Download or print QR codes
- Supports any spreadsheet structure
- No column name restrictions

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

3. Upload your spreadsheet (CSV or Excel)

4. View, download, or print QR codes for each row

## Project Structure

```
QRGen/
├── app.py              # Main Streamlit application
├── requirements.txt    # Project dependencies
└── utils/
    ├── __init__.py
    ├── data_handler.py # Spreadsheet processing
    └── qr_generator.py # QR code generation
```

## License

MIT License
