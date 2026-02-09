from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import sys
import json
from werkzeug.utils import secure_filename
import tempfile
import uuid
from datetime import datetime

# Mock pigpio for development
from unittest.mock import MagicMock
sys.modules['pigpio'] = MagicMock()

# Import from brachiograph-main folder
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'brachiograph-main'))
from linedraw import vectorise, makesvg

app = Flask(__name__)
CORS(app)  # Enable CORS for React

UPLOAD_FOLDER = tempfile.gettempdir()
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Processing queue and history
processing_queue = []
processing_history = []
currently_processing = None

@app.route('/api/upload', methods=['POST'])
def upload_image():
    """Upload and add image to processing queue"""

    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'Empty filename'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type'}), 400

    # Get processing parameters
    resolution = int(request.form.get('resolution', 512))
    draw_contours = int(request.form.get('contours', 2))
    draw_hatch = int(request.form.get('hatch', 16))

    try:
        # Save uploaded file
        filename = secure_filename(file.filename)
        job_id = str(uuid.uuid4())
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], f"{job_id}_{filename}")
        file.save(filepath)

        # Read file as base64 for preview storage
        import base64
        with open(filepath, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')

        # Determine image mime type
        ext = filename.rsplit('.', 1)[1].lower()
        mime_types = {
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'png': 'image/png',
            'gif': 'image/gif',
            'bmp': 'image/bmp'
        }
        mime_type = mime_types.get(ext, 'image/jpeg')

        # Create job object
        job = {
            'id': job_id,
            'filename': filename,
            'filepath': filepath,
            'image_preview': f"data:{mime_type};base64,{image_data}",
            'settings': {
                'resolution': resolution,
                'contours': draw_contours,
                'hatch': draw_hatch
            },
            'status': 'queued',
            'created_at': datetime.now().isoformat(),
            'progress': 0
        }

        # Add to queue
        processing_queue.append(job)

        return jsonify({
            'success': True,
            'job_id': job_id,
            'queue_position': len(processing_queue)
        })

    except Exception as e:
        print(f"Error uploading image: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/process-queue', methods=['POST'])
def process_queue():
    """Process all items in the queue"""
    global currently_processing

    if not processing_queue:
        return jsonify({'error': 'Queue is empty'}), 400

    if currently_processing:
        return jsonify({'error': 'Already processing'}), 400

    results = []

    while processing_queue:
        job = processing_queue.pop(0)
        currently_processing = job

        try:
            job['status'] = 'processing'
            job['progress'] = 10

            # Create images directory
            images_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'images')
            os.makedirs(images_dir, exist_ok=True)

            # Copy file to images directory
            import shutil
            temp_filepath = os.path.join(images_dir, job['filename'])
            shutil.copy(job['filepath'], temp_filepath)

            job['progress'] = 30

            # Change to temp directory
            original_dir = os.getcwd()
            os.chdir(app.config['UPLOAD_FOLDER'])

            try:
                # Process image
                print(f"Processing {job['filename']}...")
                lines = vectorise(
                    job['filename'],
                    resolution=job['settings']['resolution'],
                    draw_contours=job['settings']['contours'],
                    repeat_contours=1,
                    draw_hatch=job['settings']['hatch'] if job['settings']['hatch'] > 0 else False,
                    repeat_hatch=1
                )
                job['progress'] = 70
            finally:
                os.chdir(original_dir)

            # Generate SVG preview BEFORE flipping
            svg_content = makesvg(lines)
            job['progress'] = 80

            # Flip Y coordinates for plotting
            if lines:
                all_y = [point[1] for line in lines for point in line]
                max_y = max(all_y) if all_y else 0
                flipped_lines = []
                for line in lines:
                    flipped_line = [[point[0], max_y - point[1]] for point in line]
                    flipped_lines.append(flipped_line)
                lines = flipped_lines

            # Calculate statistics
            total_segments = sum(len(line) - 1 for line in lines)
            estimated_time = total_segments * 0.5 / 60

            # Save JSON
            json_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{job['id']}.json")
            with open(json_path, 'w') as f:
                json.dump(lines, f)

            # Update job
            job['status'] = 'complete'
            job['progress'] = 100
            job['lines'] = lines
            job['svg'] = svg_content
            job['lines_count'] = len(lines)
            job['segments_count'] = total_segments
            job['estimated_time_minutes'] = round(estimated_time, 1)
            job['json_path'] = json_path
            job['completed_at'] = datetime.now().isoformat()

            # Add to history
            processing_history.append(job)

            # Clean up
            try:
                os.remove(job['filepath'])
                os.remove(temp_filepath)
                svg_path = os.path.join(images_dir, job['filename'] + '.svg')
                if os.path.exists(svg_path):
                    os.remove(svg_path)
                json_path_old = os.path.join(images_dir, job['filename'] + '.json')
                if os.path.exists(json_path_old):
                    os.remove(json_path_old)
            except:
                pass

            results.append({
                'job_id': job['id'],
                'status': 'complete',
                'lines_count': job['lines_count']
            })

        except Exception as e:
            job['status'] = 'error'
            job['error'] = str(e)
            processing_history.append(job)
            print(f"Error processing {job['filename']}: {e}")
            import traceback
            traceback.print_exc()

            results.append({
                'job_id': job['id'],
                'status': 'error',
                'error': str(e)
            })

    currently_processing = None

    return jsonify({
        'success': True,
        'processed': len(results),
        'results': results
    })

@app.route('/api/queue', methods=['GET'])
def get_queue():
    """Get current queue status"""
    return jsonify({
        'queue': [{
            'id': job['id'],
            'filename': job['filename'],
            'status': job['status'],
            'settings': job['settings'],
            'created_at': job['created_at']
        } for job in processing_queue],
        'currently_processing': {
            'id': currently_processing['id'],
            'filename': currently_processing['filename'],
            'progress': currently_processing['progress']
        } if currently_processing else None
    })

@app.route('/api/history', methods=['GET'])
def get_history():
    """Get processing history"""
    return jsonify({
        'history': [{
            'id': job['id'],
            'filename': job['filename'],
            'image_preview': job['image_preview'],
            'svg': job.get('svg'),
            'status': job['status'],
            'settings': job['settings'],
            'lines_count': job.get('lines_count'),
            'segments_count': job.get('segments_count'),
            'estimated_time_minutes': job.get('estimated_time_minutes'),
            'created_at': job['created_at'],
            'completed_at': job.get('completed_at'),
            'error': job.get('error')
        } for job in reversed(processing_history)]  # Most recent first
    })

@app.route('/api/history/<job_id>', methods=['DELETE'])
def delete_history_item(job_id):
    """Delete a history item"""
    global processing_history

    # Find and remove the job
    processing_history = [job for job in processing_history if job['id'] != job_id]

    # Clean up files
    try:
        json_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{job_id}.json")
        if os.path.exists(json_path):
            os.remove(json_path)
    except:
        pass

    return jsonify({'success': True})

@app.route('/api/queue/<job_id>', methods=['DELETE'])
def remove_from_queue(job_id):
    """Remove an item from the queue"""
    global processing_queue

    # Find and remove the job
    job = next((j for j in processing_queue if j['id'] == job_id), None)

    if not job:
        return jsonify({'error': 'Job not found'}), 404

    processing_queue = [j for j in processing_queue if j['id'] != job_id]

    # Clean up file
    try:
        if os.path.exists(job['filepath']):
            os.remove(job['filepath'])
    except:
        pass

    return jsonify({'success': True})

@app.route('/api/simulate', methods=['POST'])
def get_simulation_frames():
    """Generate animation frames for web visualization"""

    if 'lines' not in current_job:
        return jsonify({'error': 'No image processed yet'}), 400

    lines = current_job['lines']
    frames = []

    inner_arm = 8
    outer_arm = 8

    def xy_to_angles(x, y):
        """Convert XY to angles"""
        import math
        hypotenuse = math.sqrt(x**2 + y**2)

        if hypotenuse > (inner_arm + outer_arm):
            return None, None

        hypotenuse_angle = math.asin(x / hypotenuse)
        inner_angle = math.acos((hypotenuse**2 + inner_arm**2 - outer_arm**2) / (2 * hypotenuse * inner_arm))
        outer_angle = math.acos((inner_arm**2 + outer_arm**2 - hypotenuse**2) / (2 * inner_arm * outer_arm))

        shoulder = hypotenuse_angle - inner_angle
        elbow = math.pi - outer_angle

        return shoulder, elbow

    # Sample every Nth point to reduce data
    sample_rate = max(1, sum(len(line) for line in lines) // 500)

    point_count = 0
    for line in lines:
        pen_down = False
        for i, point in enumerate(line):
            point_count += 1
            if point_count % sample_rate != 0:
                continue

            x, y = point
            shoulder, elbow = xy_to_angles(x, y)

            if shoulder is not None:
                frames.append({
                    'x': x,
                    'y': y,
                    'shoulder': shoulder,
                    'elbow': elbow,
                    'pen_down': pen_down
                })

            pen_down = True

    return jsonify({
        'frames': frames[:1000],  # Limit to 1000 frames
        'inner_arm': inner_arm,
        'outer_arm': outer_arm
    })

@app.route('/api/download-json/<job_id>', methods=['GET'])
def download_json(job_id):
    """Download JSON for a specific job"""

    # Find job in history
    job = next((j for j in processing_history if j['id'] == job_id), None)

    if not job or 'lines' not in job:
        return jsonify({'error': 'Job not found or not processed'}), 404

    json_data = json.dumps(job['lines'], indent=2)

    return jsonify({
        'json': json_data,
        'filename': f"{job['filename']}.json"
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)