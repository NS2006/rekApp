import os
import time
import sys
import uuid
import json
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, redirect, url_for
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge
from utils.video_processor import VideoProcessor
from utils.summarizer import TextSummarizer

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'hf-space-secret-key-change-this')

app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB
app.config['UPLOAD_FOLDER'] = '/tmp/uploads'
app.config['PROCESSED_FOLDER'] = '/tmp/processed'
app.config['ALLOWED_EXTENSIONS'] = {'mp4', 'avi', 'mov', 'mkv', 'webm'}

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['PROCESSED_FOLDER'], exist_ok=True)

print(f"Hugging Face Spaces setup complete", file=sys.stderr)
print(f"Upload folder: {app.config['UPLOAD_FOLDER']}", file=sys.stderr)
print(f"Processed folder: {app.config['PROCESSED_FOLDER']}", file=sys.stderr)

# Initialize summarizer with lazy loading
class LazySummarizer:
    def __init__(self, model_path='model'):
        self.model_path = model_path
        self._summarizer = None
    
    def get_summarizer(self):
        if self._summarizer is None:
            print("Loading model for first time on Hugging Face...", file=sys.stderr)
            self._summarizer = TextSummarizer(model_path=self.model_path)
        return self._summarizer
    
    def summarize(self, text):
        try:
            summarizer = self.get_summarizer()
            return summarizer.summarize(text)
        except Exception as e:
            print(f"Summarization failed: {e}", file=sys.stderr)
            sentences = text.split('.')
            if len(sentences) > 3:
                return '. '.join(sentences[:3]) + '.'
            return text[:300] + '...' if len(text) > 300 else text

summarizer = LazySummarizer(model_path='model')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def cleanup_old_files():
    now = datetime.now()
    
    for folder in [app.config['UPLOAD_FOLDER'], app.config['PROCESSED_FOLDER']]:
        if os.path.exists(folder):
            for filename in os.listdir(folder):
                filepath = os.path.join(folder, filename)
                try:
                    file_time = datetime.fromtimestamp(os.path.getmtime(filepath))
                    if now - file_time > timedelta(hours=1):
                        os.remove(filepath)
                        print(f"Cleaned up: {filepath}", file=sys.stderr)
                except:
                    pass

@app.errorhandler(RequestEntityTooLarge)
def handle_large_file(error):
    return jsonify({'error': 'File too large. Max 100MB.'}), 413

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/upload', methods=['POST'])
def upload_video():
    cleanup_old_files()
    
    if 'video' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['video']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type'}), 400
    
    job_id = str(uuid.uuid4())
    filename = secure_filename(file.filename)
    
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], f"{job_id}_{filename}")
    file.save(filepath)
    
    print(f"Video saved to: {filepath}", file=sys.stderr)
    
    meta_data = {
        'filename': filename,
        'filepath': filepath,
        'timestamp': time.time()
    }
    meta_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{job_id}.json")
    
    with open(meta_path, 'w') as f:
        json.dump(meta_data, f)

    return jsonify({
        'success': True,
        'job_id': job_id,
        'redirect': url_for('process', job_id=job_id)
    })

@app.route('/process/<job_id>')
def process(job_id):
    meta_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{job_id}.json")
    job_type = 'video' 
    
    if os.path.exists(meta_path):
        try:
            with open(meta_path, 'r') as f:
                data = json.load(f)
                job_type = data.get('job_type', 'video')
        except:
            pass
            
    return render_template('processing.html', job_id=job_id, job_type=job_type)

@app.route('/process-text', methods=['POST'])
def process_text():
    try:
        text_content = request.form.get('text')
        
        if not text_content:
            return jsonify({'status': 'error', 'message': 'No text provided'}), 400

        job_id = str(uuid.uuid4())
        
        # Save metadata so the status route knows what to do
        meta_data = {
            'job_type': 'text',
            'filename': 'Direct Text Input',
            'text_content': text_content,
            'timestamp': time.time()
        }
        
        meta_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{job_id}.json")
        with open(meta_path, 'w') as f:
            json.dump(meta_data, f)
            
        return jsonify({
            'status': 'success',
            'redirect': url_for('process', job_id=job_id)
        })

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/status/<job_id>')
def processing_status(job_id):
    try:
        meta_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{job_id}.json")
        
        if not os.path.exists(meta_path):
            return jsonify({'status': 'error', 'message': 'Job session expired'})
            
        with open(meta_path, 'r') as f:
            meta_data = json.load(f)
            
        job_type = meta_data.get('job_type', 'video')
        filename = meta_data.get('filename')

        if job_type == 'text':
            transcript = meta_data.get('text_content', '')
            print(f"Processing Text Job: {job_id}", file=sys.stderr)
            
            summary = summarizer.summarize(transcript)
            
            result_file = os.path.join(app.config['PROCESSED_FOLDER'], f"{job_id}_result.json")
            result_data = {
                'job_id': job_id,
                'filename': filename,
                'transcript': transcript,
                'summary': summary,
                'timestamp': time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            with open(result_file, 'w', encoding='utf-8') as f:
                json.dump(result_data, f, indent=2)
                
            if os.path.exists(meta_path):
                os.remove(meta_path)
                
            return jsonify({'status': 'complete', 'redirect': url_for('show_result', job_id=job_id)})
        else:
            filepath = meta_data.get('filepath')
            if not filepath or not os.path.exists(filepath):
                return jsonify({'status': 'error', 'message': 'Video file not found'})
            
            processor = VideoProcessor()
            
            audio_path = os.path.join(app.config['PROCESSED_FOLDER'], f"{job_id}_audio.wav")
            if not processor.extract_audio(filepath, audio_path):
                return jsonify({'status': 'error', 'message': 'Failed to extract audio'})
            
            transcript = processor.transcribe_audio(audio_path)
            if not transcript: transcript = "[Error: No speech detected]"
            
            summary = summarizer.summarize(transcript)
            
            result_file = os.path.join(app.config['PROCESSED_FOLDER'], f"{job_id}_result.json")
            result_data = {
                'job_id': job_id,
                'filename': filename,
                'transcript': transcript,
                'summary': summary,
                'timestamp': time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            with open(result_file, 'w', encoding='utf-8') as f:
                json.dump(result_data, f, indent=2)
            
            try:
                for p in [filepath, audio_path, meta_path]:
                    if os.path.exists(p): os.remove(p)
            except: pass
            
            return jsonify({'status': 'complete', 'redirect': url_for('show_result', job_id=job_id)})
            
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return jsonify({'status': 'error', 'message': str(e)})
    
@app.route('/result/<job_id>')
def show_result(job_id):
    result_file = os.path.join(app.config['PROCESSED_FOLDER'], f"{job_id}_result.json")
    
    if not os.path.exists(result_file):
        return "Result not found (it may have been cleaned up)", 404
    
    with open(result_file, 'r', encoding='utf-8') as f:
        result = json.load(f)
    
    return render_template('result.html', 
                          transcript=result['transcript'], 
                          summary=result['summary'],
                          filename=result['filename'],
                          job_id=job_id)

@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'environment': 'Hugging Face Spaces',
        'max_upload_size': '100MB',
        'storage_path': '/tmp'
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 7860))
    print(f"Starting Flask app on port {port}", file=sys.stderr)
    app.run(debug=False, host='0.0.0.0', port=port)