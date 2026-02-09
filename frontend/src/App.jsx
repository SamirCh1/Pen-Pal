import React, { useState, useEffect } from 'react';
import './App.css';

function App() {
    const [selectedFiles, setSelectedFiles] = useState([]);
    const [queue, setQueue] = useState([]);
    const [history, setHistory] = useState([]);
    const [processing, setProcessing] = useState(false);
    const [currentlyProcessing, setCurrentlyProcessing] = useState(null);

    // Settings
    const [resolution, setResolution] = useState(512);
    const [contours, setContours] = useState(2);
    const [hatch, setHatch] = useState(16);

    // Load history on mount
    useEffect(() => {
        loadHistory();
    }, []);

    // Poll queue status while processing
    useEffect(() => {
        let interval;
        if (processing) {
            interval = setInterval(() => {
                loadQueue();
            }, 1000);
        }
        return () => clearInterval(interval);
    }, [processing]);

    const loadQueue = async () => {
        try {
            const response = await fetch('/api/queue');
            const data = await response.json();
            setQueue(data.queue || []);
            setCurrentlyProcessing(data.currently_processing);
        } catch (error) {
            console.error('Failed to load queue:', error);
        }
    };

    const loadHistory = async () => {
        try {
            const response = await fetch('/api/history');
            const data = await response.json();
            setHistory(data.history || []);
        } catch (error) {
            console.error('Failed to load history:', error);
        }
    };

    const [showSimulator, setShowSimulator] = useState(false);

    const handleSimulate = () => {
        setShowSimulator(true);
    };

// In the results section, add:
    <button
        onClick={handleSimulate}
        className="btn btn-simulate"
    >
        View Arm Simulation
    </button>

    {showSimulator && <ArmSimulator />}

    const handleFileSelect = (e) => {
        const files = Array.from(e.target.files);
        setSelectedFiles(files);
    };

    const handleUploadToQueue = async () => {
        if (selectedFiles.length === 0) return;

        for (const file of selectedFiles) {
            const formData = new FormData();
            formData.append('file', file);
            formData.append('resolution', resolution);
            formData.append('contours', contours);
            formData.append('hatch', hatch);

            try {
                const response = await fetch('/api/upload', {
                    method: 'POST',
                    body: formData
                });

                const data = await response.json();

                if (data.error) {
                    alert(`Error uploading ${file.name}: ${data.error}`);
                }
            } catch (error) {
                alert(`Failed to upload ${file.name}: ${error.message}`);
            }
        }

        // Clear selected files and reload queue
        setSelectedFiles([]);
        document.getElementById('file-upload').value = '';
        loadQueue();
    };

    const handleProcessQueue = async () => {
        setProcessing(true);

        try {
            const response = await fetch('/api/process-queue', {
                method: 'POST'
            });

            const data = await response.json();

            if (data.error) {
                alert('Error: ' + data.error);
            } else {
                alert(`Processed ${data.processed} images!`);
                loadHistory();
            }
        } catch (error) {
            alert('Processing failed: ' + error.message);
        } finally {
            setProcessing(false);
            setCurrentlyProcessing(null);
            loadQueue();
        }
    };

    const handleRemoveFromQueue = async (jobId) => {
        try {
            await fetch(`/api/queue/${jobId}`, { method: 'DELETE' });
            loadQueue();
        } catch (error) {
            alert('Failed to remove from queue: ' + error.message);
        }
    };

    const handleDeleteHistory = async (jobId) => {
        if (!window.confirm('Delete this item from history?')) return;

        try {
            await fetch(`/api/history/${jobId}`, { method: 'DELETE' });
            loadHistory();
        } catch (error) {
            alert('Failed to delete: ' + error.message);
        }
    };

    const handleDownloadJSON = async (jobId, filename) => {
        try {
            const response = await fetch(`/api/download-json/${jobId}`);
            const data = await response.json();

            if (data.error) {
                alert('Error: ' + data.error);
                return;
            }

            // Download as file
            const blob = new Blob([data.json], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = data.filename || 'plotter-data.json';
            a.click();
            URL.revokeObjectURL(url);
        } catch (error) {
            alert('Download failed: ' + error.message);
        }
    };

    return (
        <div className="App">
            <header>
                <h1>Pen Plotter Control</h1>
            </header>

            <div className="container">
                {/* Upload Section */}
                <div className="card">
                    <h2>1. Upload Images</h2>

                    <div className="file-upload-wrapper">
                        <input
                            type="file"
                            accept="image/*"
                            multiple
                            onChange={handleFileSelect}
                            className="file-input"
                            id="file-upload"
                        />
                        <label htmlFor="file-upload" className="file-label">
                            {selectedFiles.length > 0
                                ? `${selectedFiles.length} file(s) selected`
                                : 'Choose images...'}
                        </label>
                    </div>

                    {selectedFiles.length > 0 && (
                        <div className="selected-files">
                            <h4>Selected Files:</h4>
                            <ul>
                                {selectedFiles.map((file, idx) => (
                                    <li key={idx}>{file.name}</li>
                                ))}
                            </ul>
                        </div>
                    )}
                </div>

                {/* Settings Section */}
                <div className="card">
                    <h2>2. Processing Settings</h2>

                    <div className="settings">
                        <label>
                            <span className="label-text">Resolution: {resolution}px</span>
                            <input
                                type="range"
                                min="256"
                                max="1024"
                                step="128"
                                value={resolution}
                                onChange={(e) => setResolution(parseInt(e.target.value))}
                            />
                            <span className="hint">Higher = more detail, slower processing</span>
                        </label>

                        <label>
                            <span className="label-text">Contour Detail: {contours}</span>
                            <input
                                type="range"
                                min="0"
                                max="10"
                                value={contours}
                                onChange={(e) => setContours(parseInt(e.target.value))}
                            />
                            <span className="hint">0 = none, 10 = maximum detail</span>
                        </label>

                        <label>
                            <span className="label-text">Hatching: {hatch > 0 ? hatch : 'Off'}</span>
                            <input
                                type="range"
                                min="0"
                                max="32"
                                step="4"
                                value={hatch}
                                onChange={(e) => setHatch(parseInt(e.target.value))}
                            />
                            <span className="hint">0 = off, lower number = denser shading</span>
                        </label>
                    </div>

                    <button
                        onClick={handleUploadToQueue}
                        disabled={selectedFiles.length === 0}
                        className="btn btn-primary"
                    >
                        Add to Queue ({selectedFiles.length})
                    </button>
                </div>

                {/* Queue Section */}
                <div className="card">
                    <h2>3. Processing Queue ({queue.length})</h2>

                    {currentlyProcessing && (
                        <div className="currently-processing">
                            <h4>Currently Processing:</h4>
                            <p>{currentlyProcessing.filename}</p>
                            <div className="progress-bar">
                                <div
                                    className="progress-fill"
                                    style={{ width: `${currentlyProcessing.progress}%` }}
                                />
                            </div>
                            <p>{currentlyProcessing.progress}%</p>
                        </div>
                    )}

                    {queue.length > 0 ? (
                        <>
                            <div className="queue-list">
                                {queue.map((job, idx) => (
                                    <div key={job.id} className="queue-item">
                                        <div className="queue-item-info">
                                            <strong>#{idx + 1}</strong>
                                            <span>{job.filename}</span>
                                            <span className="queue-item-settings">
                        {job.settings.resolution}px, C:{job.settings.contours}, H:
                                                {job.settings.hatch}
                      </span>
                                        </div>
                                        <button
                                            onClick={() => handleRemoveFromQueue(job.id)}
                                            className="btn-small btn-danger"
                                        >
                                            Remove
                                        </button>
                                    </div>
                                ))}
                            </div>

                            <button
                                onClick={handleProcessQueue}
                                disabled={processing}
                                className="btn btn-primary"
                                style={{ marginTop: '20px' }}
                            >
                                {processing ? 'Processing...' : `Process Queue (${queue.length})`}
                            </button>
                        </>
                    ) : (
                        <p className="empty-state">Queue is empty. Upload images to get started!</p>
                    )}
                </div>

                {/* History Section */}
                <div className="card">
                    <h2>4. Processing History ({history.length})</h2>

                    {history.length > 0 ? (
                        <div className="history-grid">
                            {history.map((item) => (
                                <div key={item.id} className="history-item">
                                    <div className="history-preview">
                                        {item.image_preview && (
                                            <img src={item.image_preview} alt={item.filename} />
                                        )}
                                        {item.status === 'error' && (
                                            <div className="error-overlay">Error</div>
                                        )}
                                    </div>

                                    <div className="history-info">
                                        <h4>{item.filename}</h4>

                                        {item.status === 'complete' && (
                                            <>
                                                <div className="history-stats">
                                                    <span>{item.lines_count} lines</span>
                                                    <span>{item.segments_count} segments</span>
                                                    <span>{item.estimated_time_minutes} min</span>
                                                </div>

                                                <div className="history-svg-preview">
                                                    {item.svg && (
                                                        <div
                                                            dangerouslySetInnerHTML={{ __html: item.svg }}
                                                            style={{ maxHeight: '150px', overflow: 'hidden' }}
                                                        />
                                                    )}
                                                </div>
                                            </>
                                        )}

                                        {item.status === 'error' && (
                                            <p className="error-message">{item.error}</p>
                                        )}

                                        <div className="history-actions">
                                            {item.status === 'complete' && (
                                                <button
                                                    onClick={() => handleDownloadJSON(item.id, item.filename)}
                                                    className="btn-small btn-download"
                                                >
                                                    Download JSON
                                                </button>
                                            )}
                                            <button
                                                onClick={() => handleDeleteHistory(item.id)}
                                                className="btn-small btn-danger"
                                            >
                                                Delete
                                            </button>
                                        </div>

                                        <p className="history-timestamp">
                                            {new Date(item.created_at).toLocaleString()}
                                        </p>
                                    </div>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <p className="empty-state">No processing history yet.</p>
                    )}
                </div>

                {/* Instructions */}
                <div className="card">
                    <div className="instructions">
                        <h3>To view with Turtle Graphics:</h3>
                        <ol>
                            <li>Download the JSON file from history</li>
                            <li>Open Terminal and navigate to: <code>backend/</code></li>
                            <li>Activate virtual environment: <code>source venv/bin/activate</code></li>
                            <li>Run: <code>python turtle_viewer.py ~/Downloads/plotter-data.json</code></li>
                        </ol>
                    </div>
                </div>
            </div>
        </div>
    );
}

export default App;