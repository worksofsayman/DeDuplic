from flask import Flask, request, send_file, render_template, redirect, url_for
import pandas as pd
import io
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Store cleaned CSVs temporarily (in-memory) using a dictionary
# Note: On serverless, each invocation is stateless. For small usage, this works.
CLEANED_FILES = {}

BASE_URL = "http://deduplic.vercel.app"  # Change to your domain

@app.route('/', methods=['GET', 'POST'])
def upload_and_process():
    qr_code_url = "/static/qr.png"
    logo_url = "/static/logo.png"

    duplicates_str = None
    error_msg = None
    file_id = None

    if request.method == 'POST':
        uploaded_file = request.files.get('file')
        column_name = request.form.get('column_name')

        if not uploaded_file:
            error_msg = "No file uploaded."
        elif not column_name:
            error_msg = "Please specify the column name."
        else:
            try:
                df = pd.read_csv(uploaded_file)

                if column_name not in df.columns:
                    error_msg = f"CSV does not contain column '{column_name}'."
                else:
                    # Find duplicates
                    duplicate_ids = df[df.duplicated(subset=[column_name], keep='first')][column_name].unique()
                    duplicates_str = ", ".join(map(str, duplicate_ids)) if len(duplicate_ids) > 0 else "None"

                    # Remove duplicates
                    df_cleaned = df.drop_duplicates(subset=[column_name], keep='first')

                    # Store cleaned CSV in memory with a unique ID
                    file_id = str(datetime.now().timestamp()).replace('.', '')
                    csv_buffer = io.BytesIO()
                    df_cleaned.to_csv(csv_buffer, index=False)
                    csv_buffer.seek(0)
                    CLEANED_FILES[file_id] = csv_buffer.getvalue()

            except Exception as e:
                error_msg = str(e)

    return render_template(
        'index.html',
        duplicates=duplicates_str,
        error=error_msg,
        qr_url=qr_code_url,
        logo_url=logo_url,
        file_id=file_id
    )


@app.route('/download/<file_id>')
def download_file(file_id):
    csv_data = CLEANED_FILES.get(file_id)
    if not csv_data:
        return redirect(url_for('upload_and_process'))

    return send_file(
        io.BytesIO(csv_data),
        mimetype='text/csv',
        as_attachment=True,
        download_name='cleaned_file.csv'
    )


@app.route('/sitemap.xml')
def sitemap():
    urls = ["/"]
    sitemap_xml = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    for path in urls:
        sitemap_xml += f"""  <url>
    <loc>{BASE_URL}{path}</loc>
    <lastmod>{datetime.now().date()}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.8</priority>
  </url>\n"""
    sitemap_xml += '</urlset>'
    return app.response_class(sitemap_xml, mimetype='application/xml')


@app.route('/robots.txt')
def robots():
    robots_txt = f"""User-agent: *
Allow: /

Sitemap: {BASE_URL}/sitemap.xml
"""
    return app.response_class(robots_txt, mimetype='text/plain')


if __name__ == '__main__':
    app.run(debug=True)
