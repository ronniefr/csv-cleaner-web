import os
import logging
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
import base64
from flask import Flask, request, render_template_string, send_file, redirect, url_for, flash

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Global variable to store cleaned data path
CLEAN_DATA_PATH = None

# HTML templates
UPLOAD_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>CSV Cleaner</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .container { max-width: 600px; margin: 0 auto; }
        .form-group { margin-bottom: 20px; }
        input[type="file"] { margin-bottom: 10px; }
        .btn { background-color: #4CAF50; color: white; padding: 10px 20px; border: none; cursor: pointer; }
        .btn:hover { background-color: #45a049; }
        .error { color: red; }
    </style>
</head>
<body>
    <div class="container">
        <h2>CSV Cleaner</h2>
        {% with messages = get_flashed_messages() %}
            {% if messages %}
                <ul class="error">
                {% for message in messages %}
                    <li>{{ message }}</li>
                {% endfor %}
                </ul>
            {% endif %}
        {% endwith %}
        <form id="uploadForm" method="POST" enctype="multipart/form-data" onsubmit="return validateForm()">
            <div class="form-group">
                <input type="file" id="csvFile" name="file" accept=".csv">
            </div>
            <div class="form-group">
                <button type="submit" class="btn">Upload and Clean CSV</button>
            </div>
        </form>
    </div>
    <script>
        function validateForm() {
            const fileInput = document.getElementById('csvFile');
            if (!fileInput.files.length) {
                alert('Please select a CSV file.');
                return false;
            }
            const fileName = fileInput.files[0].name;
            if (!fileName.endsWith('.csv')) {
                alert('Please select a valid CSV file.');
                return false;
            }
            return true;
        }
    </script>
</body>
</html>
'''

RESULT_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Cleaning Results</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .container { max-width: 1000px; margin: 0 auto; }
        .section { margin-bottom: 30px; }
        .btn { background-color: #008CBA; color: white; padding: 10px 20px; text-decoration: none; display: inline-block; }
        .btn:hover { background-color: #007B9A; }
        .chart { margin: 20px 0; }
        img { max-width: 100%; height: auto; }
        .error { color: red; }
    </style>
</head>
<body>
    <div class="container">
        <h2>Cleaning Results</h2>
        {% with messages = get_flashed_messages() %}
            {% if messages %}
                <ul class="error">
                {% for message in messages %}
                    <li>{{ message }}</li>
                {% endfor %}
                </ul>
            {% endif %}
        {% endwith %}
        
        <div class="section">
            <h3>Summary</h3>
            <p>Original rows: {{ original_rows }}</p>
            <p>Cleaned rows: {{ cleaned_rows }}</p>
        </div>
        
        {% if age_histogram %}
        <div class="section">
            <h3>Age Distribution</h3>
            <div class="chart">
                <img src="{{ age_histogram }}" alt="Age Histogram">
            </div>
        </div>
        {% endif %}
        
        {% if city_bar_chart %}
        <div class="section">
            <h3>City Distribution</h3>
            <div class="chart">
                <img src="{{ city_bar_chart }}" alt="City Bar Chart">
            </div>
        </div>
        {% endif %}
        
        <div class="section">
            <a href="{{ url_for('download_file') }}" class="btn">Download Cleaned CSV</a>
            <a href="{{ url_for('index') }}" class="btn" style="background-color: #f44336;">Upload Another File</a>
        </div>
    </div>
</body>
</html>
'''


def sanitize_cell(value):
    """
    Sanitize a cell value to prevent CSV injection.
    
    Args:
        value: Cell value to sanitize
        
    Returns:
        Sanitized value
    """
    if isinstance(value, str) and value.startswith('='):
        return "'" + value
    return value


def clean_csv_data(df):
    """
    Clean the CSV data according to requirements.
    
    Args:
        df (pd.DataFrame): Input DataFrame
        
    Returns:
        pd.DataFrame: Cleaned DataFrame
    """
    original_rows = len(df)
    logger.info(f"Starting with {original_rows} rows")
    
    # Remove rows with missing values
    df = df.dropna()
    logger.info(f"After removing missing values: {len(df)} rows")
    
    # Remove duplicate rows
    df = df.drop_duplicates()
    logger.info(f"After removing duplicates: {len(df)} rows")
    
    # Sanitize all cells to prevent CSV injection
    df = df.applymap(sanitize_cell)
    logger.info("Data sanitization complete")
    
    return df


def create_age_histogram(df):
    """
    Create a histogram for the Age column if it exists.
    
    Args:
        df (pd.DataFrame): DataFrame with potential Age column
        
    Returns:
        str: Base64 encoded image or None
    """
    if 'Age' not in df.columns:
        logger.info("Age column not found")
        return None
        
    try:
        # Check if Age column is numeric
        pd.to_numeric(df['Age'], errors='raise')
        
        plt.figure(figsize=(10, 6))
        plt.hist(df['Age'], bins=20, color='skyblue', edgecolor='black')
        plt.title('Age Distribution')
        plt.xlabel('Age')
        plt.ylabel('Frequency')
        plt.grid(axis='y', alpha=0.75)
        
        img = BytesIO()
        plt.savefig(img, format='png')
        img.seek(0)
        plot_url = base64.b64encode(img.getvalue()).decode()
        plt.close()
        
        logger.info("Age histogram created successfully")
        return f"data:image/png;base64,{plot_url}"
    except Exception as e:
        logger.error(f"Error creating age histogram: {str(e)}")
        return None


def create_city_bar_chart(df):
    """
    Create a bar chart for the City column if it exists.
    
    Args:
        df (pd.DataFrame): DataFrame with potential City column
        
    Returns:
        str: Base64 encoded image or None
    """
    if 'City' not in df.columns:
        logger.info("City column not found")
        return None
        
    try:
        city_counts = df['City'].value_counts()
        
        plt.figure(figsize=(10, 6))
        city_counts.plot(kind='bar', color='lightcoral')
        plt.title('City Distribution')
        plt.xlabel('City')
        plt.ylabel('Count')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        
        img = BytesIO()
        plt.savefig(img, format='png')
        img.seek(0)
        plot_url = base64.b64encode(img.getvalue()).decode()
        plt.close()
        
        logger.info("City bar chart created successfully")
        return f"data:image/png;base64,{plot_url}"
    except Exception as e:
        logger.error(f"Error creating city bar chart: {str(e)}")
        return None


@app.route('/', methods=['GET'])
def index():
    """Render the file upload page."""
    return render_template_string(UPLOAD_TEMPLATE)


@app.route('/', methods=['POST'])
def upload_file():
    """Handle file upload and processing."""
    global CLEAN_DATA_PATH
    
    if 'file' not in request.files:
        flash('No file selected')
        return redirect(request.url)
        
    file = request.files['file']
    
    if file.filename == '':
        flash('No file selected')
        return redirect(request.url)
        
    if not file.filename.endswith('.csv'):
        flash('Invalid file type. Please upload a CSV file.')
        return redirect(request.url)
        
    try:
        # Read the CSV file
        df = pd.read_csv(file)
        original_rows = len(df)
        logger.info(f"File uploaded with {original_rows} rows")
        
        # Clean the data
        cleaned_df = clean_csv_data(df)
        cleaned_rows = len(cleaned_df)
        
        # Create visualizations
        age_histogram = create_age_histogram(cleaned_df)
        city_bar_chart = create_city_bar_chart(cleaned_df)
        
        # Save cleaned data temporarily
        CLEAN_DATA_PATH = os.path.join(os.getcwd(), 'cleaned_data.csv')
        cleaned_df.to_csv(CLEAN_DATA_PATH, index=False)
        logger.info(f"Cleaned data saved to {CLEAN_DATA_PATH}")
        
        # Render results page
        return render_template_string(
            RESULT_TEMPLATE,
            original_rows=original_rows,
            cleaned_rows=cleaned_rows,
            age_histogram=age_histogram,
            city_bar_chart=city_bar_chart
        )
    except pd.errors.EmptyDataError:
        flash('Uploaded file is empty or invalid.')
        return redirect(url_for('index'))
    except Exception as e:
        logger.error(f"Error processing file: {str(e)}")
        flash(f'Error processing file: {str(e)}')
        return redirect(url_for('index'))


@app.route('/download')
def download_file():
    """Provide download of cleaned CSV file."""
    global CLEAN_DATA_PATH
    
    if not CLEAN_DATA_PATH or not os.path.exists(CLEAN_DATA_PATH):
        flash('No cleaned file available for download.')
        return redirect(url_for('index'))
        
    try:
        return send_file(
            CLEAN_DATA_PATH,
            as_attachment=True,
            download_name='cleaned_data.csv',
            mimetype='text/csv'
        )
    except Exception as e:
        logger.error(f"Error downloading file: {str(e)}")
        flash('Error downloading file.')
        return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=False)