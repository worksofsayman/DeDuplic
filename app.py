from flask import Flask, request, send_file, render_template, session, redirect, url_for
import pandas as pd
import io
import os
from flask_session import Session

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Use filesystem-based session to persist CSVs
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

BASE_URL = "http://deduplic.vercel.app"

@app.route('/', methods=['GET', 'POST'])
def upload_and_process():
    qr_code_url = "/static/qr.png"
    logo_url = "/static/logo.png"

    duplicates_str = None
    error_msg = None

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

                    # Store CSV in session
                    csv_buffer = io.BytesIO()
                    df_cleaned.to_csv(csv_buffer, index=False)
                    csv_buffer.seek(0)
                    session['cleaned_csv'] = csv_buffer.getvalue()

            except Exception as e:
                error_msg = str(e)

    return render_template(
        'index.html',
        duplicates=duplicates_str,
        error=error_msg,
        qr_url=qr_code_url,
        logo_url=logo_url
    )

@app.route('/download')
def download_file():
    csv_data = session.get('cleaned_csv')
    if not csv_data:
        return redirect(url_for('upload_and_process'))

    return send_file(
        io.BytesIO(csv_data),
        mimetype='text/csv',
        as_attachment=True,
        download_name='cleaned_file.csv'
    )

if __name__ == '__main__':
    app.run(debug=True)
