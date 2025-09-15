from flask import Flask, request, render_template
import pandas as pd
import io
import os
import base64

app = Flask(__name__)
app.secret_key = os.urandom(24)

@app.route('/', methods=['GET', 'POST'])
def upload_and_process():
    duplicates_str = None
    cleaned_csv_b64 = None
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

                    # Encode cleaned CSV in Base64 for JS download
                    csv_buffer = io.BytesIO()
                    df_cleaned.to_csv(csv_buffer, index=False)
                    csv_buffer.seek(0)
                    cleaned_csv_b64 = base64.b64encode(csv_buffer.getvalue()).decode('utf-8')

            except Exception as e:
                error_msg = str(e)

    return render_template(
        'index.html',
        duplicates=duplicates_str,
        csv_b64=cleaned_csv_b64,
        error=error_msg,
        logo_url="/static/logo.png",
        qr_url="/static/qr.png"
    )


if __name__ == '__main__':
    app.run(debug=True)
