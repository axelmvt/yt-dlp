import os
import threading
import time
import subprocess
from flask import Flask, render_template_string, request, redirect, url_for, flash, send_file

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a secure key

DOWNLOADS_DIR = '/downloads'
os.makedirs(DOWNLOADS_DIR, exist_ok=True)

# Background cleanup thread: deletes files older than 24 hours.
def cleanup_downloads():
    while True:
        now = time.time()
        for filename in os.listdir(DOWNLOADS_DIR):
            filepath = os.path.join(DOWNLOADS_DIR, filename)
            if os.path.isfile(filepath) and (now - os.path.getmtime(filepath) > 24 * 3600):
                try:
                    os.remove(filepath)
                    print(f"Deleted old file: {filepath}")
                except Exception as e:
                    print(f"Error deleting file {filepath}: {e}")
        time.sleep(3600)  # Check every hour

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
  </head>
  <body>
    <div class="container mt-5">
      <h1 class="mb-4">yt-dlp Downloader</h1>
      <p>Main supported services: YouTube, TikTok, Twitter (X), Instagram, Facebook</p>
      <a href="{{ url_for('supported') }}" class="btn btn-link mb-3">View All Supported Sites</a>
      {% with messages = get_flashed_messages() %}
        {% if messages %}
          <div class="alert alert-info">
            {% for msg in messages %}
              <div>{{ msg }}</div>
            {% endfor %}
          </div>
        {% endif %}
      {% endwith %}
      <form method="post">
        <div class="mb-3">
          <label for="url" class="form-label">Video URL</label>
          <input type="text" class="form-control" id="url" name="url" placeholder="Enter video URL" required>
        </div>
        <div class="mb-3">
          <label for="download_type" class="form-label">Download Type</label>
          <select class="form-select" id="download_type" name="download_type">
            <option value="video" selected>Video (default)</option>
            <option value="audio">Audio Only</option>
          </select>
        </div>
        <div class="mb-3">
          <label for="format" class="form-label">Format (optional)</label>
          <input type="text" class="form-control" id="format" name="format" placeholder="e.g., mp4, mkv, mp3">
        </div>
        <div class="mb-3">
          <label for="quality" class="form-label">Video Quality (optional)</label>
          <input type="text" class="form-control" id="quality" name="quality" placeholder="e.g., 720, 1080">
        </div>
        <div class="mb-3">
          <label for="subtitles" class="form-label">Subtitles (optional)</label>
          <input type="text" class="form-control" id="subtitles" name="subtitles" placeholder="e.g., en, es">
        </div>
        <div class="mb-3 form-check">
          <input type="checkbox" class="form-check-input" id="direct_download" name="direct_download">
          <label class="form-check-label" for="direct_download">
            Direct Download (download file immediately)
          </label>
        </div>
        <button type="submit" class="btn btn-primary">Download</button>
      </form>
    </div>
  </body>
</html>
"""

# Simple supported sites page.
SUPPORTED_TEMPLATE = """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Supported Sites</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
  </head>
  <body>
    <div class="container mt-5">
      <h1 class="mb-4">Supported Sites</h1>
      <p>This tool supports downloads from a wide range of services.</p>
      <ul>
        <li>YouTube</li>
        <li>TikTok</li>
        <li>Twitter (X)</li>
        <li>Instagram</li>
        <li>Facebook</li>
      </ul>
      <p>For the full list, see 
        <a href="https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md" target="_blank">
          yt-dlp Supported Sites
        </a>.
      </p>
      <a href="{{ url_for('index') }}" class="btn btn-secondary mt-3">Back</a>
    </div>
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
        direct_download = request.form.get('direct_download') == 'on'
        
        if not url:
            flash("URL is required!")
            return redirect(url_for('index'))

        # Compute expected output filename.
        expected_file = get_output_filename(url, download_type, fmt, quality, subtitles)
        if expected_file and os.path.exists(expected_file):
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

        # If Direct Download was requested, stream the file immediately.
        if direct_download and expected_file and os.path.exists(expected_file):
            return send_file(expected_file, as_attachment=True)
        
        flash("File saved to cache and available for download later.")
        return redirect(url_for('index'))
    
    return render_template_string(HTML_TEMPLATE)

@app.route('/supported')
def supported():
    return render_template_string(SUPPORTED_TEMPLATE)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

