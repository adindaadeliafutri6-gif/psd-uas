import os
import datetime
import json

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from werkzeug.utils import secure_filename
import pandas as pd

from backend.data_loader import load_data
from backend.data_cleaning import clean_dataset, analyze_quality, get_cleaning_summary
from backend.preprocessing import detect_data_types
from backend.descriptive_stats import get_summary_metrics, get_descriptive_stats
from backend.advanced_stats import get_advanced_stats
from backend.dashboard_overview import generate_overview_dashboard
from backend.viz_engine import (
    generate_master_chart, category_available, CATEGORY_CHARTS, CHART_LABELS,
)
from backend.insights_generator import generate_auto_insights
from backend.time_series import detect_datetime_cols, generate_ts_plots

app = Flask(__name__, template_folder='frontend/templates', static_folder='frontend/static')
app.secret_key = 'super_secret_key_week_15_itsb'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024

ALLOWED_EXTENSIONS = {'csv', 'txt', 'xlsx'}
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# ─────────────────────────────────────────────────────────────────────────────
# ROUTES
# ─────────────────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    uploaded_files = []
    try:
        if os.path.exists(app.config['UPLOAD_FOLDER']):
            folder_path = app.config['UPLOAD_FOLDER']
            files = [
                f for f in os.listdir(folder_path)
                if os.path.isfile(os.path.join(folder_path, f))
            ]
            files.sort(
                key=lambda x: os.path.getmtime(os.path.join(folder_path, x)),
                reverse=True,
            )
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

            # ── Deteksi duplikat ──────────────────────────────────────────────
            if os.path.exists(filepath):
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({
                        'duplicate': True,
                        'filename' : filename,
                        'redirect' : url_for('dashboard', filename=filename),
                    })
                flash(
                    f'Dataset "{filename}" sudah pernah dianalisis sebelumnya. '
                    'Menampilkan data lama...', 'info',
                )
                return redirect(url_for('dashboard', filename=filename))

            file.save(filepath)

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'duplicate': False,
                    'filename' : filename,
                    'redirect' : url_for('dashboard', filename=filename),
                })

            flash(f'Dataset "{filename}" berhasil diunggah!', 'success')
            return redirect(url_for('dashboard', filename=filename))
        else:
            flash('Format file tidak valid. Gunakan .csv, .txt, atau .xlsx', 'error')

    return render_template('upload.html', history=uploaded_files)


@app.route('/dashboard/<filename>')
def dashboard(filename):
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    if not os.path.exists(filepath):
        flash('File tidak ditemukan.', 'error')
        return redirect(url_for('upload_file'))

    df_raw = load_data(filepath)
    if df_raw is None:
        flash('Gagal membaca dataset.', 'error')
        return redirect(url_for('upload_file'))

    # ── Data Cleaning ─────────────────────────────────────────────────────────
    def _clean_flag(name, default=True):
        if name in request.args:
            return request.args.get(name) == '1'
        return default

    clean_opts = {
        'strip_whitespace'       : _clean_flag('strip_ws'),
        'empty_to_nan'           : _clean_flag('empty_nan'),
        'drop_duplicates'        : _clean_flag('drop_dupes'),
        'drop_empty_cols'        : _clean_flag('drop_empty'),
        'drop_high_missing'      : float(request.args.get('drop_miss_thresh', '0') or 0),
        'fill_missing_numeric'   : request.args.get('fill_num', 'none'),
        'fill_missing_categorical': request.args.get('fill_cat', 'none'),
        'cap_outliers'           : _clean_flag('cap_outliers', default=False),
    }
    df, cleaning_log = clean_dataset(df_raw, clean_opts)
    cleaning_summary = get_cleaning_summary(df_raw, df, cleaning_log)
    quality_report   = analyze_quality(df_raw)

    # ── Column detection ──────────────────────────────────────────────────────
    num_cols, cat_cols = detect_data_types(df)

    # ── Summary metrics ───────────────────────────────────────────────────────
    metrics = get_summary_metrics(df, num_cols, cat_cols)

    # ── Descriptive stats ─────────────────────────────────────────────────────
    num_stats, cat_stats = get_descriptive_stats(df, num_cols, cat_cols)

    # ── Advanced stats ────────────────────────────────────────────────────────
    advanced = get_advanced_stats(df, num_cols, cat_cols)

    # ── Time Series detection ─────────────────────────────────────────────────
    dt_cols = detect_datetime_cols(df)

    # ── Dashboard overview ────────────────────────────────────────────────────
    overview = generate_overview_dashboard(
        df, num_cols, cat_cols, dt_cols=dt_cols, metrics=metrics
    )

    # ── Time Series plots (plots hanya berisi TS; viz utama via AJAX) ─────────
    plots            = {}   # default kosong
    ts_insights_list = []
    ts_meta          = {}

    if dt_cols:
        try:
            ts_plots, ts_insights_list, ts_meta = generate_ts_plots(
                df, dt_cols, num_cols
            )
            plots = ts_plots  # hanya TS plots yang dikirim ke template
        except Exception as e:
            print(f"[TS] generate_ts_plots error: {e}")

    # ── Intelligent insights ──────────────────────────────────────────────────
    auto_insights = generate_auto_insights(
        df, num_cols, cat_cols, ts_insights=ts_insights_list
    )

    # ── Preview (100 baris pertama) ───────────────────────────────────────────
    preview_html = df.to_html(
        classes='data-table display nowrap',
        index=False,
        table_id='preview-table',
    )

    # ── Dataset info untuk sidebar card ───────────────────────────────────────
    file_size_kb = 0.0
    if os.path.exists(filepath):
        file_size_kb = os.path.getsize(filepath) / 1024.0
    file_size_str = f"{file_size_kb:,.2f} KB"

    dt_file = datetime.datetime.fromtimestamp(os.path.getmtime(filepath))
    months  = ["Jan","Feb","Mar","Apr","May","Jun",
               "Jul","Aug","Sep","Oct","Nov","Dec"]
    upload_time_str = (
        f"{dt_file.day:02d} {months[dt_file.month - 1]} {dt_file.year} "
        f"{dt_file.hour:02d}:{dt_file.minute:02d}"
    )
    dataset_info = {
        'name': filename,
        'rows': metrics['total_rows'],
        'cols': metrics['total_columns'],
        'size': file_size_str,
        'time': upload_time_str,
    }

    # ── col_data untuk interactive chart (sampled) ────────────────────────────
    col_data = {}
    for col in num_cols:
        series = df[col].dropna()
        if len(series) > 2000:
            series = series.sample(2000, random_state=42)
        col_data[col] = {
            'type'  : 'numeric',
            'values': [round(float(v), 4) for v in series.tolist()],
        }
    for col in cat_cols:
        vc = df[col].value_counts().head(20)
        col_data[col] = {
            'type'  : 'categorical',
            'labels': vc.index.astype(str).tolist(),
            'counts': [int(v) for v in vc.values.tolist()],
        }

    return render_template(
        'dashboard.html',
        filename         = filename,
        preview          = preview_html,
        metrics          = metrics,
        num_stats        = num_stats,
        cat_stats        = cat_stats,
        plots            = plots,
        insights         = auto_insights,
        advanced         = advanced,
        num_cols         = num_cols,
        cat_cols         = cat_cols,
        col_data         = col_data,
        dataset_info     = dataset_info,
        cleaning_summary = cleaning_summary,
        quality_report   = quality_report,
        clean_opts       = clean_opts,
        overview         = overview,
        # ── Time Series ──────────────────────────────────────────────────────
        has_ts           = bool(dt_cols),
        dt_cols          = dt_cols,
        ts_meta          = ts_meta,
    )


# ─────────────────────────────────────────────────────────────────────────────
# VISUALIZATION MASTER API
# ─────────────────────────────────────────────────────────────────────────────

def _load_analysis_df(filename):
    """Muat & bersihkan dataset (sama seperti dashboard default)."""
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(filepath):
        return None, None, None, None
    df_raw = load_data(filepath)
    if df_raw is None:
        return None, None, None, None
    df, _ = clean_dataset(df_raw, {})
    num_cols, cat_cols = detect_data_types(df)
    dt_cols = detect_datetime_cols(df)
    return df, num_cols, cat_cols, dt_cols


@app.route('/api/viz-chart/<filename>')
def api_viz_chart(filename):
    """Generate satu grafik master berdasarkan kategori, tipe, dan kolom."""
    df, num_cols, cat_cols, _ = _load_analysis_df(filename)
    if df is None:
        return jsonify({'ok': False, 'placeholder': 'Dataset tidak ditemukan.'}), 404

    category   = request.args.get('category', 'numerical')
    chart_type = request.args.get('chart_type', '')
    col_x      = request.args.get('col_x') or None
    col_y      = request.args.get('col_y') or None
    col_z      = request.args.get('col_z') or None

    try:
        print('[api/viz-chart] params:', {
            'category'  : category,
            'chart_type': chart_type,
            'col_x'     : col_x,
            'col_y'     : col_y,
            'col_z'     : col_z,
        })
    except Exception:
        pass

    if not chart_type:
        types      = CATEGORY_CHARTS.get(category, [])
        chart_type = types[0] if types else ''

    result = generate_master_chart(
        df, num_cols, cat_cols, category, chart_type,
        col_x=col_x, col_y=col_y, col_z=col_z,
    )
    result['category']  = category
    result['available'] = category_available(category, num_cols, cat_cols)
    return jsonify(result)


# ─────────────────────────────────────────────────────────────────────────────
# AI CHAT ENDPOINT
# ─────────────────────────────────────────────────────────────────────────────

@app.route('/api/ai-chat', methods=['POST'])
def ai_chat():
    """Proxy-free AI endpoint — pakai Anthropic API langsung dari server."""
    try:
        import anthropic
        data     = request.get_json()
        user_msg = data.get('message', '')
        context  = data.get('context', '')

        client = anthropic.Anthropic(api_key=os.environ.get('ANTHROPIC_API_KEY', ''))
        system_prompt = (
            "Kamu adalah asisten analisis data cerdas bernama DataBot untuk aplikasi "
            "DS Generator Kelompok 2. "
            "Jawab dengan bahasa yang jelas, ringkas, dan informatif. "
            f"Konteks dataset saat ini: {context}"
        )
        message = client.messages.create(
            model      = "claude-sonnet-4-20250514",
            max_tokens = 1024,
            system     = system_prompt,
            messages   = [{"role": "user", "content": user_msg}],
        )
        return jsonify({'reply': message.content[0].text})

    except ImportError:
        return jsonify({
            'reply': 'Library anthropic belum terpasang. Jalankan: pip install anthropic'
        }), 500
    except Exception as e:
        return jsonify({'reply': f'Error: {str(e)}'}), 500


# ─────────────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    app.run(debug=True)