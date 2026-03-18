import zipfile
import os
from datetime import datetime

def create_zip_archive(source_folder, output_zip_path):
    with zipfile.ZipFile(output_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(source_folder):
            for file in files:
                file_path = os.path.join(root, file)
                # Arcname is the path inside the zip file
                arcname = os.path.relpath(file_path, source_folder)
                zipf.write(file_path, arcname)

if __name__ == '__main__':
    project_folder = "./url_analyzer"
    # Use current datetime for unique filename
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output_zip = f"url_analyzer_export_{timestamp}.zip"
    
    if os.path.exists(project_folder):
        create_zip_archive(project_folder, output_zip)
        print(f"Project '{project_folder}' successfully exported to '{output_zip}'")
    else:
        print(f"Error: Project folder '{project_folder}' not found.")
