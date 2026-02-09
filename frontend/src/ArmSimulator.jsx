import React, { useEffect, useRef, useState } from 'react';

function ArmSimulator() {
    const canvasRef = useRef(null);
    const [frames, setFrames] = useState([]);
    const [currentFrame, setCurrentFrame] = useState(0);
    const [playing, setPlaying] = useState(false);

    useEffect(() => {
        // Fetch simulation frames
        fetch('/api/simulate', { method: 'POST' })
            .then(res => res.json())
            .then(data => {
                setFrames(data.frames);
            });
    }, []);

    useEffect(() => {
        if (!playing || !frames.length) return;

        const interval = setInterval(() => {
            setCurrentFrame(prev => {
                if (prev >= frames.length - 1) {
                    setPlaying(false);
                    return prev;
                }
                return prev + 1;
            });
        }, 20);

        return () => clearInterval(interval);
    }, [playing, frames]);

    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas || !frames.length) return;

        const ctx = canvas.getContext('2d');
        const frame = frames[currentFrame];

        // Clear canvas
        ctx.fillStyle = 'white';
        ctx.fillRect(0, 0, canvas.width, canvas.height);

        const scale = 20;
        const originX = canvas.width / 2;
        const originY = canvas.height - 100;

        // Calculate positions
        const innerArm = frame.inner_arm || 8;
        const outerArm = frame.outer_arm || 8;

        const elbowX = originX + innerArm * Math.sin(frame.shoulder) * scale;
        const elbowY = originY - innerArm * Math.cos(frame.shoulder) * scale;

        const penX = elbowX + outerArm * Math.sin(frame.shoulder + frame.elbow) * scale;
        const penY = elbowY - outerArm * Math.cos(frame.shoulder + frame.elbow) * scale;

        // Draw base
        ctx.fillStyle = 'black';
        ctx.beginPath();
        ctx.arc(originX, originY, 10, 0, Math.PI * 2);
        ctx.fill();

        // Draw inner arm
        ctx.strokeStyle = 'blue';
        ctx.lineWidth = 8;
        ctx.beginPath();
        ctx.moveTo(originX, originY);
        ctx.lineTo(elbowX, elbowY);
        ctx.stroke();

        // Draw elbow
        ctx.fillStyle = 'blue';
        ctx.beginPath();
        ctx.arc(elbowX, elbowY, 8, 0, Math.PI * 2);
        ctx.fill();

        // Draw outer arm
        ctx.strokeStyle = 'red';
        ctx.lineWidth = 6;
        ctx.beginPath();
        ctx.moveTo(elbowX, elbowY);
        ctx.lineTo(penX, penY);
        ctx.stroke();

        // Draw pen
        ctx.fillStyle = frame.pen_down ? 'green' : 'gray';
        ctx.beginPath();
        ctx.arc(penX, penY, 6, 0, Math.PI * 2);
        ctx.fill();

    }, [currentFrame, frames]);

    return (
        <div style={{ padding: '20px', background: '#f8f8f8', borderRadius: '8px', marginTop: '20px' }}>
            <h3>Arm Simulator</h3>
            <canvas
                ref={canvasRef}
                width={600}
                height={600}
                style={{ border: '1px solid #ddd', background: 'white', borderRadius: '4px' }}
            />
            <div style={{ marginTop: '15px', display: 'flex', gap: '10px', alignItems: 'center' }}>
                <button
                    onClick={() => setPlaying(!playing)}
                    className="btn"
                    style={{ background: '#333', color: 'white', padding: '10px 20px' }}
                >
                    {playing ? 'Pause' : 'Play'}
                </button>
                <button
                    onClick={() => setCurrentFrame(0)}
                    className="btn"
                    style={{ background: '#666', color: 'white', padding: '10px 20px' }}
                >
                    Reset
                </button>
                <span>Frame: {currentFrame + 1} / {frames.length}</span>
            </div>
        </div>
    );
}

export default ArmSimulator;