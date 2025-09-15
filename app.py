from flask import Flask, request, send_file, render_template
import pandas as pd
import io
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

@app.route('/', methods=['GET', 'POST'])
def upload_and_process():
    duplicates_str = None
    cleaned_csv = None
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

                    # Store cleaned CSV in memory buffer (will send directly on download)
                    csv_buffer = io.BytesIO()
                    df_cleaned.to_csv(csv_buffer, index=False)
                    csv_buffer.seek(0)
                    cleaned_csv = csv_buffer.getvalue()

                    # Save cleaned CSV temporarily as hidden input for download
                    # We'll pass it as base64 to HTML to download directly
                    import base64
                    cleaned_csv_b64 = base64.b64encode(cleaned_csv).decode('utf-8')

                    return render_template(
                        'index.html',
                        duplicates=duplicates_str,
                        error=None,
                        csv_b64=cleaned_csv_b64
                    )

            except Exception as e:
                error_msg = str(e)

    return render_template(
        'index.html',
        duplicates=None,
        error=error_msg
    )


@app.route('/download/<string:csv_b64>')
def download_file(csv_b64):
    import base64
    csv_bytes = base64.b64decode(csv_b64)
    return send_file(
        io.BytesIO(csv_bytes),
        mimetype='text/csv',
        as_attachment=True,
        download_name='cleaned_file.csv'
    )


if __name__ == '__main__':
    app.run(debug=True)
