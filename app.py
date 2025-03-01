import os
import threading
import time
import subprocess
import sqlite3
from flask import Flask, render_template_string, request, redirect, url_for, flash, send_file
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a secure key

DOWNLOADS_DIR = '/downloads'
DATABASE_DIR = '/app/data'
os.makedirs(DOWNLOADS_DIR, exist_ok=True)
os.makedirs(DATABASE_DIR, exist_ok=True)

# Setup database
def init_db():
    conn = sqlite3.connect(os.path.join(DATABASE_DIR, 'downloads.db'))
    c = conn.cursor()
    c.execute('''
    CREATE TABLE IF NOT EXISTS downloads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        url TEXT NOT NULL,
        filename TEXT NOT NULL,
        download_date TIMESTAMP NOT NULL,
        last_accessed TIMESTAMP NOT NULL
    )
    ''')
    conn.commit()
    conn.close()

# Check if a URL has already been downloaded
def get_cached_download(url):
    conn = sqlite3.connect(os.path.join(DATABASE_DIR, 'downloads.db'))
    c = conn.cursor()
    c.execute("SELECT filename FROM downloads WHERE url = ?", (url,))
    result = c.fetchone()
    
    if result:
        # Update last accessed time
        c.execute("UPDATE downloads SET last_accessed = ? WHERE url = ?", 
                 (datetime.now().isoformat(), url))
        conn.commit()
        filename = result[0]
        conn.close()
        return filename
    
    conn.close()
    return None

# Add a new download to the database
def add_download_to_db(url, filename):
    now = datetime.now().isoformat()
    conn = sqlite3.connect(os.path.join(DATABASE_DIR, 'downloads.db'))
    c = conn.cursor()
    c.execute("INSERT INTO downloads (url, filename, download_date, last_accessed) VALUES (?, ?, ?, ?)",
             (url, filename, now, now))
    conn.commit()
    conn.close()

# Modified cleanup function to use the database for better tracking
def cleanup_downloads():
    while True:
        now = time.time()
        conn = sqlite3.connect(os.path.join(DATABASE_DIR, 'downloads.db'))
        c = conn.cursor()
        
        # Get files older than 24 hours
        c.execute("SELECT filename FROM downloads WHERE (julianday('now') - julianday(last_accessed)) > 1")
        old_files = c.fetchall()
        
        for (filename,) in old_files:
            filepath = os.path.join(DOWNLOADS_DIR, os.path.basename(filename))
            if os.path.isfile(filepath):
                try:
                    os.remove(filepath)
                    print(f"Deleted old file: {filepath}")
                    # Remove from database
                    c.execute("DELETE FROM downloads WHERE filename = ?", (filename,))
                except Exception as e:
                    print(f"Error deleting file {filepath}: {e}")
        
        conn.commit()
        conn.close()
        time.sleep(3600)  # Check every hour

init_db()  # Initialize database first

# Then start the cleanup thread
cleanup_thread = threading.Thread(target=cleanup_downloads, daemon=True)
cleanup_thread.start()

# Prettier HTML template using Bootstrap for the main page.
HTML_TEMPLATE = """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>yt-dlp Downloader</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
      body {
        background-color: #f8f9fa;
        color: #212529;
        font-family: 'Segoe UI', Roboto, 'Helvetica Neue', sans-serif;
      }
      .card {
        border-radius: 15px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        border: none;
      }
      .header-container {
        background: linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%);
        border-radius: 15px 15px 0 0;
        padding: 30px;
        color: white;
      }
      .form-container {
        padding: 30px;
      }
      .btn-primary {
        background: #6366F1;
        border: none;
        border-radius: 8px;
        padding: 10px 20px;
        font-weight: 600;
        transition: all 0.3s;
      }
      .btn-primary:hover {
        background: #4F46E5;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(79, 70, 229, 0.2);
      }
      .form-control, .form-select {
        border-radius: 8px;
        padding: 12px;
        border: 1px solid #E5E7EB;
      }
      .form-label {
        font-weight: 500;
        margin-bottom: 8px;
      }
      .service-icon {
        font-size: 24px;
        margin-right: 10px;
        vertical-align: middle;
      }
      .loader {
        display: none;
        border: 5px solid #f3f3f3;
        border-top: 5px solid #6366F1;
        border-radius: 50%;
        width: 30px;
        height: 30px;
        animation: spin 1s linear infinite;
        margin-right: 10px;
      }
      @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
      }
      .supported-services {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        margin-bottom: 15px;
        justify-content: center;
      }
      .service-badge {
        background-color: #EEF2FF;
        color: #4F46E5;
        padding: 6px 12px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 500;
      }
      .download-animation {
        position: relative;
        width: 100px;
        height: 100px;
        margin: 0 auto;
      }
      .download-icon {
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        font-size: 3rem;
        color: #6366F1;
        z-index: 2;
      }
      .download-progress {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        border: 5px solid #E0E7FF;
        border-top: 5px solid #6366F1;
        border-radius: 50%;
        animation: spin 1.5s linear infinite;
      }
      .success-animation {
        position: relative;
        width: 100px;
        height: 100px;
        margin: 0 auto;
      }
      .success-icon {
        font-size: 5rem;
        animation: pop-in 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275);
      }
      @keyframes pop-in {
        0% { transform: scale(0); opacity: 0; }
        75% { transform: scale(1.1); opacity: 1; }
        100% { transform: scale(1); opacity: 1; }
      }
    </style>
  </head>
  <body>
    <div class="container py-5">
      <div class="row justify-content-center">
        <div class="col-lg-8">
          <div class="card mb-4">
            <div class="header-container">
              <h1 class="mb-3"><i class="fas fa-download me-2"></i>yt-dlp Downloader</h1>
              <p class="mb-0 opacity-90">Download videos from popular platforms with ease</p>
            </div>
            <div class="form-container">
              {% with messages = get_flashed_messages() %}
                {% if messages %}
                  <div class="alert alert-info alert-dismissible fade show" role="alert">
                    {% for msg in messages %}
                      <div>{{ msg }}</div>
                    {% endfor %}
                    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                  </div>
                {% endif %}
              {% endwith %}
              
              <div class="supported-services mb-3">
                <div class="service-badge"><i class="fab fa-youtube"></i> YouTube</div>
                <div class="service-badge"><i class="fab fa-tiktok"></i> TikTok</div>
                <div class="service-badge"><i class="fab fa-twitter"></i> Twitter</div>
                <div class="service-badge"><i class="fab fa-instagram"></i> Instagram</div>
                <div class="service-badge"><i class="fab fa-facebook"></i> Facebook</div>
                <a href="{{ url_for('supported') }}" class="service-badge text-decoration-none">
                  <i class="fas fa-plus"></i> More
                </a>
              </div>
              
              <form method="post" id="downloadForm">
                <div class="mb-4">
                  <label for="url" class="form-label">Video URL</label>
                  <div class="input-group">
                    <span class="input-group-text"><i class="fas fa-link"></i></span>
                    <input type="text" class="form-control" id="url" name="url" placeholder="Paste video URL here" required>
                  </div>
                </div>
                
                <div class="row mb-3">
                  <div class="col-md-6 mb-3 mb-md-0">
                    <label for="download_type" class="form-label">Download Type</label>
                    <div class="input-group">
                      <span class="input-group-text"><i class="fas fa-file-video"></i></span>
                      <select class="form-select" id="download_type" name="download_type">
                        <option value="video" selected>Video (default)</option>
                        <option value="audio">Audio Only</option>
                      </select>
                    </div>
                  </div>
                  <div class="col-md-6">
                    <label for="format" class="form-label">Format (optional)</label>
                    <div class="input-group">
                      <span class="input-group-text"><i class="fas fa-file-code"></i></span>
                      <input type="text" class="form-control" id="format" name="format" placeholder="mp4, mkv, mp3">
                    </div>
                  </div>
                </div>
                
                <div class="row mb-3">
                  <div class="col-md-6 mb-3 mb-md-0">
                    <label for="quality" class="form-label">Video Quality (optional)</label>
                    <div class="input-group">
                      <span class="input-group-text"><i class="fas fa-tv"></i></span>
                      <input type="text" class="form-control" id="quality" name="quality" placeholder="720, 1080">
                    </div>
                  </div>
                  <div class="col-md-6">
                    <label for="subtitles" class="form-label">Subtitles (optional)</label>
                    <div class="input-group">
                      <span class="input-group-text"><i class="fas fa-closed-captioning"></i></span>
                      <input type="text" class="form-control" id="subtitles" name="subtitles" placeholder="en, es">
                    </div>
                  </div>
                </div>
                
                <div class="d-grid gap-2">
                  <button type="submit" class="btn btn-primary" id="downloadBtn">
                    <span class="loader" id="downloadLoader"></span>
                    <i class="fas fa-download me-2"></i> Download
                  </button>
                </div>
              </form>
            </div>
          </div>
          
          <div class="text-center text-muted small">
            <p>Powered by <a href="https://github.com/yt-dlp/yt-dlp" target="_blank" class="text-decoration-none">yt-dlp</a> • Made with <i class="fas fa-heart text-danger"></i></p>
          </div>
        </div>
      </div>
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
      document.addEventListener('DOMContentLoaded', function() {
        const downloadForm = document.getElementById('downloadForm');
        const downloadBtn = document.getElementById('downloadBtn');
        
        // Store the original button background color
        const originalBtnColor = '#6366F1';
        const tempBtnColor = '#4338CA'; // Darker color to show when downloading
        
        // Function to handle form submission
        downloadForm.addEventListener('submit', function(event) {
          // Don't prevent default - we want the form to submit normally
          
          // Change button color to indicate download is happening
          downloadBtn.style.backgroundColor = tempBtnColor;
          downloadBtn.disabled = true;
          
          // Reset button after 2 seconds
          setTimeout(function() {
            downloadBtn.style.backgroundColor = originalBtnColor;
            downloadBtn.disabled = false;
          }, 2000);
        });
      });
    </script>
  </body>
</html>
"""

# Enhanced supported sites page.
SUPPORTED_TEMPLATE = """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Supported Sites - yt-dlp Downloader</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
      body {
        background-color: #f8f9fa;
        color: #212529;
        font-family: 'Segoe UI', Roboto, 'Helvetica Neue', sans-serif;
      }
      .card {
        border-radius: 15px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        border: none;
      }
      .header-container {
        background: linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%);
        border-radius: 15px 15px 0 0;
        padding: 30px;
        color: white;
      }
      .content-container {
        padding: 30px;
      }
      .btn-secondary {
        background: #4B5563;
        border: none;
        border-radius: 8px;
        padding: 10px 20px;
        font-weight: 600;
        transition: all 0.3s;
      }
      .btn-secondary:hover {
        background: #374151;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(55, 65, 81, 0.2);
      }
      .site-list {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
        gap: 15px;
        margin-top: 20px;
      }
      .site-item {
        background: #EEF2FF;
        border-radius: 10px;
        padding: 15px;
        display: flex;
        align-items: center;
        transition: all 0.2s;
      }
      .site-item:hover {
        background: #E0E7FF;
        transform: translateY(-3px);
        box-shadow: 0 4px 12px rgba(99, 102, 241, 0.1);
      }
      .site-icon {
        font-size: 24px;
        width: 40px;
        color: #4F46E5;
        text-align: center;
      }
      .btn-back {
        display: inline-flex;
        align-items: center;
        gap: 8px;
      }
      .github-link {
        color: #4F46E5;
        text-decoration: none;
        font-weight: 500;
        transition: all 0.2s;
      }
      .github-link:hover {
        color: #4338CA;
        text-decoration: underline;
      }
    </style>
  </head>
  <body>
    <div class="container py-5">
      <div class="row justify-content-center">
        <div class="col-lg-10">
          <div class="card mb-4">
            <div class="header-container">
              <h1 class="mb-3"><i class="fas fa-list-check me-2"></i>Supported Sites</h1>
              <p class="mb-0 opacity-90">Download videos from these platforms using yt-dlp</p>
            </div>
            <div class="content-container">
              <p class="lead">This tool supports downloading from a wide range of popular video-sharing services:</p>
              
              <div class="site-list">
                <div class="site-item">
                  <div class="site-icon"><i class="fab fa-youtube"></i></div>
                  <div>YouTube</div>
                </div>
                <div class="site-item">
                  <div class="site-icon"><i class="fab fa-tiktok"></i></div>
                  <div>TikTok</div>
                </div>
                <div class="site-item">
                  <div class="site-icon"><i class="fab fa-twitter"></i></div>
                  <div>Twitter (X)</div>
                </div>
                <div class="site-item">
                  <div class="site-icon"><i class="fab fa-instagram"></i></div>
                  <div>Instagram</div>
                </div>
                <div class="site-item">
                  <div class="site-icon"><i class="fab fa-facebook"></i></div>
                  <div>Facebook</div>
                </div>
                <div class="site-item">
                  <div class="site-icon"><i class="fab fa-vimeo"></i></div>
                  <div>Vimeo</div>
                </div>
                <div class="site-item">
                  <div class="site-icon"><i class="fab fa-twitch"></i></div>
                  <div>Twitch</div>
                </div>
                <div class="site-item">
                  <div class="site-icon"><i class="fas fa-film"></i></div>
                  <div>Dailymotion</div>
                </div>
                <div class="site-item">
                  <div class="site-icon"><i class="fab fa-reddit"></i></div>
                  <div>Reddit</div>
                </div>
              </div>
              
              <div class="mt-4 mb-3">
                <p>And <strong>hundreds more!</strong> For the full list, see the 
                  <a href="https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md" target="_blank" class="github-link">
                    <i class="fab fa-github"></i> yt-dlp Supported Sites documentation
                  </a>.
                </p>
              </div>
              
              <a href="{{ url_for('index') }}" class="btn btn-secondary btn-back mt-3">
                <i class="fas fa-arrow-left"></i> Back to Downloader
              </a>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
  </body>
</html>
"""

def get_output_filename(url, download_type, fmt, quality, subtitles):
    """
    Uses yt-dlp to compute the expected output filename.
    Since --get-filename does not account for postprocessing (like recode),
    for video downloads we force the extension to .mp4.
    """
    output_template = os.path.join(DOWNLOADS_DIR, "%(id)s_%(title)s.%(ext)s")
    cmd = ["yt-dlp", "--get-filename", "-o", output_template]
    if download_type == 'audio':
        cmd.extend(["-x", "--audio-format", "mp3"])
    # Do not add --recode-video here because it won't be reflected in the filename.
    if fmt:
        cmd.extend(["-f", fmt])
    elif quality:
        cmd.extend(["-f", f"bestvideo[height<={quality}]+bestaudio/best[height<={quality}]"])
    if subtitles:
        cmd.extend(["--write-subs", "--sub-lang", subtitles])
    cmd.append(url)
    try:
        filename = subprocess.check_output(cmd, universal_newlines=True).strip()
        # For video downloads, force the final extension to mp4.
        if download_type != 'audio':
            filename = os.path.splitext(filename)[0] + ".mp4"
        return filename
    except subprocess.CalledProcessError:
        return None

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        url = request.form.get('url')
        download_type = request.form.get('download_type')
        fmt = request.form.get('format')
        quality = request.form.get('quality')
        subtitles = request.form.get('subtitles')
        
        if not url:
            flash("URL is required!")
            return redirect(url_for('index'))

        # Check if this URL has already been downloaded
        cached_file = get_cached_download(url)
        if cached_file and os.path.exists(cached_file):
            flash("Using cached version. Initiating download.")
            return send_file(cached_file, as_attachment=True)

        # Compute expected output filename.
        expected_file = get_output_filename(url, download_type, fmt, quality, subtitles)
        if expected_file and os.path.exists(expected_file):
            # Add to database if it exists but wasn't in our DB
            add_download_to_db(url, expected_file)
            flash("File already exists. Initiating direct download.")
            return send_file(expected_file, as_attachment=True)

        # Build the yt-dlp command.
        output_template = os.path.join(DOWNLOADS_DIR, "%(id)s_%(title)s.%(ext)s")
        cmd = ["yt-dlp", url, "-o", output_template]
        if download_type == 'audio':
            cmd.extend(["-x", "--audio-format", "mp3"])
        else:
            # Force recoding to mp4.
            cmd.extend(["--recode-video", "mp4"])
        if fmt:
            cmd.extend(["-f", fmt])
        elif quality:
            cmd.extend(["-f", f"bestvideo[height<={quality}]+bestaudio/best[height<={quality}]"])
        if subtitles:
            cmd.extend(["--write-subs", "--sub-lang", subtitles])
        
        try:
            subprocess.run(cmd, check=True)
            flash("Download completed successfully!")
        except subprocess.CalledProcessError:
            flash("An error occurred during download.")
            return redirect(url_for('index'))
        
        # After download, update the expected filename (for video, force .mp4)
        if download_type != 'audio':
            expected_file = os.path.splitext(expected_file)[0] + ".mp4"
            
        # Add to database
        if expected_file and os.path.exists(expected_file):
            add_download_to_db(url, expected_file)

        # Always stream the file immediately
        if expected_file and os.path.exists(expected_file):
            return send_file(expected_file, as_attachment=True)
        
        flash("File processed but could not be found for download.")
        return redirect(url_for('index'))
    
    return render_template_string(HTML_TEMPLATE)

@app.route('/supported')
def supported():
    return render_template_string(SUPPORTED_TEMPLATE)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

