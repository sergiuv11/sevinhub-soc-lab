from flask import Flask, render_template, request, send_file
import markdown
import pdfkit
import os

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['GENERATED_FOLDER'] = 'generated'

# Ensure upload and generated folders exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['GENERATED_FOLDER'], exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'markdown_file' not in request.files:
        return 'No file part'
    file = request.files['markdown_file']
    if file.filename == '':
        return 'No selected file'
    if file:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)
        
        with open(filepath, 'r', encoding='utf-8') as f:
            md_content = f.read()
        
        html_content = markdown.markdown(md_content)
        
        # Save HTML for preview and PDF generation
        html_filename = os.path.splitext(file.filename)[0] + '.html'
        html_filepath = os.path.join(app.config['GENERATED_FOLDER'], html_filename)
        with open(html_filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
            
        return render_template('preview.html', html_content=html_content, original_filename=file.filename)

@app.route('/download_pdf/<filename>')
def download_pdf(filename):
    html_filename = os.path.splitext(filename)[0] + '.html'
    html_filepath = os.path.join(app.config['GENERATED_FOLDER'], html_filename)
    
    if not os.path.exists(html_filepath):
        return "HTML file not found for PDF generation.", 404

    pdf_filename = os.path.splitext(filename)[0] + '.pdf'
    pdf_filepath = os.path.join(app.config['GENERATED_FOLDER'], pdf_filename)
    
    # Using pdfkit to convert HTML to PDF
    # Requires wkhtmltopdf to be installed and in PATH
    try:
        pdfkit.from_file(html_filepath, pdf_filepath)
        return send_file(pdf_filepath, as_attachment=True)
    except Exception as e:
        return f"Error generating PDF: {e}. Make sure wkhtmltopdf is installed and in your system's PATH.", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
