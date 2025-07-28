# csv-cleaner-web
Reusable CSV cleaning tool with simple web UI
# CSV Cleaner Web App

A simple, reusable web tool for cleaning CSV files. Upload your messy data, get it processed (remove duplicates/missing values, sanitize for security), view basic visualizations, and download the cleaned version. Built with Python (Flask, Pandas, Matplotlib) for beginners learning data handling—perfect for startups or AI prep.

## Why This Tool?
- Solves real-world "dirty data" problems: Fixes incompleteness, duplicates, and risks like CSV injection.
- Reusable: Modular backend logic you can plug into other projects (e.g., ETL pipelines).
- User-friendly: Basic HTML/JS UI for uploads/downloads—no CLI needed.
- Educational: Teaches fundamentals like data parsing, error handling, and visualization.

## Features
- **Cleaning**: Removes rows with missing values, eliminates duplicates, and sanitizes cells (e.g., prefixes '=' to prevent injection attacks).
- **Visualization**: Generates histogram for "Age" (if present) and bar chart for "City" counts—helps inspect data quickly.
- **Security**: Input validation and sanitization to avoid common risks.
- **Output**: Downloadable cleaned CSV with inline report.
- **Modular**: Core functions (e.g., `clean_csv()`) can be imported elsewhere.

## Installation
1. Clone the repo: `git clone https://github.com/ronniefr/csv-cleaner-web.git`
2. Install dependencies: `pip install flask pandas matplotlib`
3. Run locally: `python app.py` (opens at http://127.0.0.1:5000)

## Usage
1. Open in browser: Go to the upload page.
2. Select and submit your CSV file.
3. View the report: See plots (if applicable) and click "Download Cleaned CSV".
Example input: A CSV with columns like "Name", "Age", "City" (include some blanks/duplicates for testing).

## Security Notes
- Prevents CSV injection by sanitizing formulas.
- Error handling for invalid files—user-friendly messages.

## Contributing
Fork and PR! See open issues (e.g., enhance UI with React). Add your name to CONTRIBUTORS.md.

## License
MIT—free to use/modify.
