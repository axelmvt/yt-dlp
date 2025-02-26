# Video Harvester

Video Harvester is a modern, user-friendly web application that allows you to download videos, audio, and subtitles from various online platforms including YouTube, TikTok, Twitter, Instagram, and many more.

## Features

- **Clean, Modern UI**: A sleek, responsive interface that works on desktop and mobile
- **Multiple Format Support**: Download videos in different formats and qualities
- **Audio Extraction**: Extract audio from videos in MP3 format
- **Subtitle Downloads**: Download subtitles in various languages
- **Wide Platform Support**: Works with hundreds of websites (powered by yt-dlp)
- **Direct Downloads**: Option to download files directly after processing
- **Automatic Cleanup**: Files are automatically deleted after 24 hours

## Installation and Setup

### Using Docker (Recommended)

The easiest way to run Video Harvester is with Docker:

```bash
# Clone the repository
git clone https://github.com/yourusername/video-harvester.git
cd video-harvester

# Start the application with Docker Compose
docker-compose up -d
```

The application will be available at http://localhost:5000

### Manual Installation

If you prefer to run the application directly on your system:

1. Make sure you have Python 3.8+ and ffmpeg installed
2. Clone the repository and install dependencies

```bash
git clone https://github.com/yourusername/video-harvester.git
cd video-harvester
pip install -r requirements.txt
```

3. Run the application

```bash
python app.py
```

## Usage

1. Enter a video URL in the input field
2. (Optional) Configure advanced options:
   - Choose between video or audio download
   - Select format and quality
   - Specify subtitle language
   - Enable direct download
3. Click "Download" to begin the download process

## Credits

This application is powered by:

- [yt-dlp](https://github.com/yt-dlp/yt-dlp): Core video downloading functionality
- [Flask](https://flask.palletsprojects.com/): Web framework
- [Font Awesome](https://fontawesome.com/): Icons

## License

This project is licensed under the MIT License - see the LICENSE file for details.
