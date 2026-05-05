# from flask import Blueprint, request, jsonify, send_file
# from models.db import get_connection
# from services.analyzer import run_full_analysis, get_analysis_summary_text
# from services.report import generate_pdf_report
# from routes.chat import set_analysis_context
# import os
# import json
# import tempfile
# from werkzeug.utils import secure_filename

# analysis_bp = Blueprint('analysis', __name__)

# UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'uploads')
# ALLOWED_EXTENSIONS = {'csv', 'json'}

# os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# _last_analysis = {}  # global cache for dashboard


# def allowed_file(filename):
#     return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# @analysis_bp.route('/upload', methods=['POST'])
# def upload_dataset():
#     if 'file' not in request.files:
#         return jsonify({'error': 'No file part in request'}), 400

#     file = request.files['file']
#     if file.filename == '':
#         return jsonify({'error': 'No file selected'}), 400

#     if not allowed_file(file.filename):
#         return jsonify({'error': 'Invalid file type. Use CSV or JSON.'}), 400

#     filename = secure_filename(file.filename)
#     filepath = os.path.join(UPLOAD_FOLDER, filename)
#     file.save(filepath)

#     # Quick metadata extraction
#     try:
#         import pandas as pd
#         if filename.endswith('.csv'):
#             df = pd.read_csv(filepath, nrows=5)
#         else:
#             df = pd.read_json(filepath)
#             df = df.head(5)

#         full_df = pd.read_csv(filepath) if filename.endswith('.csv') else pd.read_json(filepath)
#         row_count = len(full_df)
#         columns = full_df.columns.tolist()
#     except Exception as e:
#         return jsonify({'error': f'Could not read file: {str(e)}'}), 422

#     # Save to DB
#     conn = get_connection()
#     c = conn.cursor()
#     c.execute(
#         "INSERT INTO datasets (filename, filepath, row_count, columns) VALUES (?,?,?,?)",
#         (filename, filepath, row_count, json.dumps(columns))
#     )
#     conn.commit()
#     dataset_id = c.lastrowid
#     conn.close()

#     return jsonify({
#         'success': True,
#         'dataset_id': dataset_id,
#         'filename': filename,
#         'row_count': row_count,
#         'columns': columns
#     })


# @analysis_bp.route('/analyze', methods=['POST'])
# def analyze():
#     data = request.get_json()
#     dataset_id = data.get('dataset_id') if data else None

#     conn = get_connection()
#     c = conn.cursor()

#     if dataset_id:
#         row = c.execute("SELECT * FROM datasets WHERE id=?", (dataset_id,)).fetchone()
#     else:
#         row = c.execute("SELECT * FROM datasets ORDER BY id DESC LIMIT 1").fetchone()

#     conn.close()

#     if not row:
#         return jsonify({'error': 'No dataset found. Please upload a dataset first.'}), 404

#     filepath = row['filepath']
#     if not os.path.exists(filepath):
#         return jsonify({'error': f'Dataset file not found at {filepath}'}), 404

#     try:
#         analysis = run_full_analysis(filepath)
#     except Exception as e:
#         return jsonify({'error': f'Analysis failed: {str(e)}'}), 500

#     # Cache for dashboard and chatbot
#     global _last_analysis
#     _last_analysis = analysis

#     summary_text = get_analysis_summary_text(analysis)
#     dataset_id_int = int(row['id'])
#     set_analysis_context(dataset_id_int, summary_text)

#     # Cache in DB
#     conn = get_connection()
#     c = conn.cursor()
#     c.execute("DELETE FROM analysis_cache WHERE dataset_id=?", (dataset_id_int,))
#     c.execute("INSERT INTO analysis_cache (dataset_id, analysis_json) VALUES (?,?)",
#               (dataset_id_int, json.dumps(analysis)))
#     conn.commit()
#     conn.close()

#     return jsonify(analysis)


# @analysis_bp.route('/dashboard', methods=['GET'])
# def dashboard():
#     global _last_analysis
#     if _last_analysis:
#         return jsonify(_last_analysis)

#     # Try fetching from DB
#     conn = get_connection()
#     c = conn.cursor()
#     row = c.execute("SELECT analysis_json FROM analysis_cache ORDER BY id DESC LIMIT 1").fetchone()
#     conn.close()

#     if row:
#         analysis = json.loads(row['analysis_json'])
#         _last_analysis = analysis
#         return jsonify(analysis)

#     return jsonify({'error': 'No analysis data available. Please upload and analyze a dataset first.'}), 404


# @analysis_bp.route('/report/download', methods=['GET'])
# def download_report():
#     global _last_analysis
#     if not _last_analysis:
#         return jsonify({'error': 'No analysis data. Run analysis first.'}), 404

#     try:
#         tmp = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
#         tmp.close()
#         generate_pdf_report(_last_analysis, tmp.name)
#         return send_file(tmp.name, as_attachment=True,
#                          download_name='retail_trend_report.pdf',
#                          mimetype='application/pdf')
#     except Exception as e:
#         return jsonify({'error': str(e)}), 500


# @analysis_bp.route('/datasets', methods=['GET'])
# def list_datasets():
#     conn = get_connection()
#     c = conn.cursor()
#     rows = c.execute("SELECT id, filename, row_count, columns, uploaded_at FROM datasets ORDER BY id DESC").fetchall()
#     conn.close()
#     return jsonify([dict(r) for r in rows])



from flask import Blueprint, request, jsonify, send_file
from models.db import get_connection
from services.analyzer import run_full_analysis, get_analysis_summary_text
from services.report import generate_pdf_report
from routes.chat import set_analysis_context
import os
import json
import tempfile
from werkzeug.utils import secure_filename

analysis_bp = Blueprint('analysis', __name__)

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'uploads')
ALLOWED_EXTENSIONS = {'csv', 'json'}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

_last_analysis = {}  # global cache for dashboard


def clear_last_analysis():
    global _last_analysis
    _last_analysis = {}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@analysis_bp.route('/upload', methods=['POST'])
def upload_dataset():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in request'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type. Use CSV or JSON.'}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    # Quick metadata extraction
    try:
        import pandas as pd
        if filename.endswith('.csv'):
            df = pd.read_csv(filepath, nrows=5)
        else:
            df = pd.read_json(filepath)
            df = df.head(5)

        full_df = pd.read_csv(filepath) if filename.endswith('.csv') else pd.read_json(filepath)
        row_count = len(full_df)
        columns = full_df.columns.tolist()
    except Exception as e:
        return jsonify({'error': f'Could not read file: {str(e)}'}), 422

    # Save to DB
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "INSERT INTO datasets (filename, filepath, row_count, columns) VALUES (?,?,?,?)",
        (filename, filepath, row_count, json.dumps(columns))
    )
    conn.commit()
    dataset_id = c.lastrowid
    conn.close()

    return jsonify({
        'success': True,
        'dataset_id': dataset_id,
        'filename': filename,
        'row_count': row_count,
        'columns': columns
    })


@analysis_bp.route('/analyze', methods=['POST'])
def analyze():
    data = request.get_json()
    dataset_id = data.get('dataset_id') if data else None

    conn = get_connection()
    c = conn.cursor()

    if dataset_id:
        row = c.execute("SELECT * FROM datasets WHERE id=?", (dataset_id,)).fetchone()
    else:
        row = c.execute("SELECT * FROM datasets ORDER BY id DESC LIMIT 1").fetchone()

    conn.close()

    if not row:
        return jsonify({'error': 'No dataset found. Please upload a dataset first.'}), 404

    filepath = row['filepath']
    if not os.path.exists(filepath):
        return jsonify({'error': f'Dataset file not found at {filepath}'}), 404

    try:
        analysis = run_full_analysis(filepath)
    except Exception as e:
        return jsonify({'error': f'Analysis failed: {str(e)}'}), 500

    # Cache for dashboard and chatbot
    global _last_analysis
    _last_analysis = analysis

    summary_text = get_analysis_summary_text(analysis)
    dataset_id_int = int(row['id'])
    set_analysis_context(dataset_id_int, summary_text)

    # Cache in DB
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM analysis_cache WHERE dataset_id=?", (dataset_id_int,))
    c.execute("INSERT INTO analysis_cache (dataset_id, analysis_json) VALUES (?,?)",
              (dataset_id_int, json.dumps(analysis)))
    conn.commit()
    conn.close()

    return jsonify(analysis)


@analysis_bp.route('/dashboard', methods=['GET'])
def dashboard():
    global _last_analysis
    if _last_analysis:
        return jsonify(_last_analysis)

    # Try fetching from DB
    conn = get_connection()
    c = conn.cursor()
    row = c.execute("SELECT analysis_json FROM analysis_cache ORDER BY id DESC LIMIT 1").fetchone()
    conn.close()

    if row:
        analysis = json.loads(row['analysis_json'])
        _last_analysis = analysis
        return jsonify(analysis)

    return jsonify({'error': 'No analysis data available. Please upload and analyze a dataset first.'}), 404


@analysis_bp.route('/report/download', methods=['GET'])
def download_report():
    global _last_analysis
    if not _last_analysis:
        return jsonify({'error': 'No analysis data. Run analysis first.'}), 404

    try:
        tmp = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
        tmp.close()
        generate_pdf_report(_last_analysis, tmp.name)
        return send_file(tmp.name, as_attachment=True,
                         download_name='retail_trend_report.pdf',
                         mimetype='application/pdf')
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@analysis_bp.route('/datasets', methods=['GET'])
def list_datasets():
    conn = get_connection()
    c = conn.cursor()
    rows = c.execute("SELECT id, filename, row_count, columns, uploaded_at FROM datasets ORDER BY id DESC").fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])
