import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from werkzeug.utils import secure_filename
import pandas as pd
from backend.visualizations import generate_plots, generate_comparison
from backend.insights_generator import generate_auto_insights
import json


from backend.data_loader import load_data
from backend.preprocessing import detect_data_types
from backend.descriptive_stats import get_summary_metrics, get_descriptive_stats
from backend.advanced_stats import get_advanced_stats  # NEW: Week 15

app = Flask(__name__, template_folder='frontend/templates', static_folder='frontend/static')
app.secret_key = 'super_secret_key_week_15_itsb'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024

ALLOWED_EXTENSIONS = {'csv', 'txt', 'xlsx'}
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    uploaded_files = []
    try:
        if os.path.exists(app.config['UPLOAD_FOLDER']):
            folder_path = app.config['UPLOAD_FOLDER']
            files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
            files.sort(key=lambda x: os.path.getmtime(os.path.join(folder_path, x)), reverse=True)
            uploaded_files = files
    except Exception as e:
        print(f"Error membaca history: {e}")

    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part', 'error')
            return redirect(request.url)

        file = request.files['file']
        if file.filename == '':
            flash('No selected file', 'error')
            return redirect(request.url)

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

            # ─── DETEKSI DUPLIKAT ───
            if os.path.exists(filepath):
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({'duplicate': True, 'filename': filename, 'redirect': url_for('dashboard', filename=filename)})
                flash(f'Dataset "{filename}" sudah pernah dianalisis sebelumnya. Menampilkan data lama...', 'info')
                return redirect(url_for('dashboard', filename=filename))

            file.save(filepath)

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'duplicate': False, 'filename': filename, 'redirect': url_for('dashboard', filename=filename)})

            flash(f'Dataset "{filename}" berhasil diunggah!', 'success')
            return redirect(url_for('dashboard', filename=filename))
        else:
            flash('Format file tidak valid. Gunakan .csv, .txt, atau .xlsx', 'error')

    return render_template('upload.html', history=uploaded_files)

@app.route('/dashboard/<filename>')
def dashboard(filename):
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    df = load_data(filepath)

    if df is None:
        flash('Gagal membaca dataset.', 'error')
        return redirect(url_for('upload_file'))

    preview_html = df.head(100).to_html(classes='data-table display nowrap', index=False)
    num_cols, cat_cols = detect_data_types(df)
    metrics = get_summary_metrics(df)
    metrics['num_count'] = len(num_cols)
    metrics['cat_count'] = len(cat_cols)
    num_stats, cat_stats = get_descriptive_stats(df, num_cols, cat_cols)

    # ─── WEEK 15: Advanced Stats, Plots, Insights ───
    advanced = get_advanced_stats(df, num_cols, cat_cols)
    plots_json = generate_plots(df, num_cols, cat_cols)
    auto_insights = generate_auto_insights(df, num_cols, cat_cols)

    return render_template('dashboard.html',
                           filename=filename,
                           preview=preview_html,
                           metrics=metrics,
                           num_stats=num_stats,
                           cat_stats=cat_stats,
                           plots=plots_json,
                           insights=auto_insights,
                           advanced=advanced,
                           num_cols=num_cols,
                           cat_cols=cat_cols)


# ─── COMPARISON ENDPOINT (NEW) ───────────────────────────────────────────────
@app.route('/api/compare')
def api_compare():
    """
    Endpoint untuk fitur Variable Comparison di tab Visualizations.
    Query params:
        filename : nama file yang sedang dibuka (dari URL dashboard)
        mode     : scatter | bar | violin | hist_overlay
        col_a    : kolom numerik
        col_b    : kolom numerik (scatter) atau kategorik (lainnya)
    """
    filename = request.args.get('filename', '')
    mode     = request.args.get('mode', 'scatter')
    col_a    = request.args.get('col_a', '')
    col_b    = request.args.get('col_b', '')

    if not filename or not col_a or not col_b:
        return jsonify({'error': 'Parameter tidak lengkap (filename, col_a, col_b wajib)'}), 400

    filepath = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(filename))
    if not os.path.exists(filepath):
        return jsonify({'error': f'File "{filename}" tidak ditemukan di server'}), 404

    df = load_data(filepath)
    if df is None:
        return jsonify({'error': 'Gagal membaca dataset'}), 500

    _, _ = detect_data_types(df)   # hanya untuk konsistensi; tidak dipakai di sini

    result = generate_comparison(df, mode, col_a, col_b)
    if result is None:
        return jsonify({'error': f'Kombinasi mode={mode}, col_a={col_a}, col_b={col_b} tidak valid'}), 400
    if isinstance(result, dict) and result.get('error'):
        return jsonify(result), 400

    return jsonify(result)


# ─── AI CHAT ENDPOINT ────────────────────────────────────────────────────────
@app.route('/api/ai-chat', methods=['POST'])
def ai_chat():
    """Proxy-free AI endpoint — pakai Anthropic API langsung dari server."""
    try:
        import anthropic
        data = request.get_json()
        user_msg = data.get('message', '')
        context  = data.get('context', '')

        client = anthropic.Anthropic(api_key=os.environ.get('ANTHROPIC_API_KEY', ''))
        system_prompt = (
            "Kamu adalah asisten analisis data cerdas bernama DataBot untuk aplikasi DS Generator Kelompok 2. "
            "Jawab dengan bahasa yang jelas, ringkas, dan informatif. "
            f"Konteks dataset saat ini: {context}"
        )
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            system=system_prompt,
            messages=[{"role": "user", "content": user_msg}]
        )
        return jsonify({'reply': message.content[0].text})
    except ImportError:
        return jsonify({'reply': 'Library anthropic belum terpasang. Jalankan: pip install anthropic'}), 500
    except Exception as e:
        return jsonify({'reply': f'Error: {str(e)}'}), 500


if __name__ == '__main__':
    app.run(debug=True)