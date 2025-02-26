import os
import threading
import time
import subprocess
from flask import Flask, render_template, request, redirect, url_for, flash, send_file

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
        download_type = request.form.get('download_type', 'video')
        fmt = request.form.get('format')
        quality = request.form.get('quality')
        subtitles = request.form.get('subtitles')
        direct_download = request.form.get('direct_download') == 'on'
        
        if not url:
            flash("URL is required!", "danger")
            return redirect(url_for('index'))

        # Compute expected output filename.
        expected_file = get_output_filename(url, download_type, fmt, quality, subtitles)
        if expected_file and os.path.exists(expected_file):
            flash("File already exists. Initiating download.", "info")
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
            flash("Download completed successfully!", "success")
        except subprocess.CalledProcessError:
            flash("An error occurred during download.", "danger")
            return redirect(url_for('index'))
        
        # After download, update the expected filename (for video, force .mp4)
        if download_type != 'audio':
            expected_file = os.path.splitext(expected_file)[0] + ".mp4"

        # If Direct Download was requested, stream the file immediately.
        if direct_download and expected_file and os.path.exists(expected_file):
            return send_file(expected_file, as_attachment=True)
        
        flash("File saved to cache and available for download later.", "success")
        return redirect(url_for('index'))
    
    return render_template('index.html')

@app.route('/supported')
def supported():
    return render_template('supported.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

