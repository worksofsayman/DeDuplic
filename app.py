from flask import Flask, request, send_file, render_template
import pandas as pd
import io
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.urandom(24)

# ---- BASE URL FOR SITEMAP ----
BASE_URL = "http://deduplic.vercel.app"  # Change to your deployed domain

# ---- MAIN UPLOAD/PROCESS ROUTE ----
@app.route('/', methods=['GET', 'POST'])
def upload_and_process():
    qr_code_url = "/static/qr.png"
    logo_url = "/static/logo.png"

    if request.method == 'POST':
        uploaded_file = request.files.get('file')
        column_name = request.form.get('column_name')  # Column to check duplicates

        if not uploaded_file:
            return render_template('index.html', duplicates=None, error="No file uploaded.", qr_url=qr_code_url, logo_url=logo_url)

        if not column_name:
            return render_template('index.html', duplicates=None, error="Please specify the column name.", qr_url=qr_code_url, logo_url=logo_url)

        try:
            df = pd.read_csv(uploaded_file)

            if column_name not in df.columns:
                return render_template('index.html', duplicates=None, error=f"CSV does not contain column '{column_name}'.", qr_url=qr_code_url, logo_url=logo_url)

            # Find duplicate IDs
            duplicate_ids = df[df.duplicated(subset=[column_name], keep='first')][column_name].unique()
            duplicates_str = ", ".join(map(str, duplicate_ids)) if len(duplicate_ids) > 0 else "None"

            # Remove duplicates
            df_cleaned = df.drop_duplicates(subset=[column_name], keep='first')

            # Prepare CSV for download immediately
            csv_buffer = io.BytesIO()
            df_cleaned.to_csv(csv_buffer, index=False)
            csv_buffer.seek(0)

            # Send the cleaned CSV directly as download
            return send_file(
                csv_buffer,
                mimetype='text/csv',
                as_attachment=True,
                download_name='cleaned_file.csv'
            )

        except Exception as e:
            return render_template('index.html', duplicates=None, error=str(e), qr_url=qr_code_url, logo_url=logo_url)

    return render_template('index.html', duplicates=None, error=None, qr_url=qr_code_url, logo_url=logo_url)


# ---- SITEMAP ROUTE ----
@app.route('/sitemap.xml', methods=['GET'])
def sitemap():
    urls = [
        "/",         # Home
    ]

    sitemap_xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    sitemap_xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'

    for path in urls:
        sitemap_xml += f"""  <url>
    <loc>{BASE_URL}{path}</loc>
    <lastmod>{datetime.now().date()}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.8</priority>
  </url>\n"""

    sitemap_xml += '</urlset>'
    return app.response_class(sitemap_xml, mimetype='application/xml')


# ---- ROBOTS.TXT ROUTE ----
@app.route('/robots.txt', methods=['GET'])
def robots():
    robots_txt = f"""User-agent: *
Allow: /

Sitemap: {BASE_URL}/sitemap.xml
"""
    return app.response_class(robots_txt, mimetype='text/plain')


# ---- RUN APP ----
if __name__ == '__main__':
    app.run(debug=True)
