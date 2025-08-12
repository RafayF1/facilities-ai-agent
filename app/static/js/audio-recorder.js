/**
 * Audio recorder worklet for PCM audio capture
 */

export async function startAudioRecorderWorklet(audioDataCallback) {
    try {
        // Request microphone access
        const stream = await navigator.mediaDevices.getUserMedia({
            audio: {
                sampleRate: 16000,  // 16kHz for Gemini audio input
                channelCount: 1,    // Mono
                echoCancellation: true,
                noiseSuppression: true,
                autoGainControl: true
            }
        });
        
        // Create audio context with appropriate sample rate for recording
        const audioContext = new (window.AudioContext || window.webkitAudioContext)({
            sampleRate: 16000  // 16kHz for recording
        });
        
        // Load the PCM recorder processor
        await audioContext.audioWorklet.addModule('/static/js/pcm-recorder-processor.js');
        
        // Create the worklet node
        const recorderNode = new AudioWorkletNode(audioContext, 'pcm-recorder-processor');
        
        // Set up message handling for audio data
        recorderNode.port.onmessage = (event) => {
            if (event.data && audioDataCallback) {
                audioDataCallback(event.data);
            }
        };
        
        // Connect microphone to the recorder
        const source = audioContext.createMediaStreamSource(stream);
        source.connect(recorderNode);
        
        // Resume audio context if it's suspended
        if (audioContext.state === 'suspended') {
            await audioContext.resume();
        }
        
        console.log('Audio recorder worklet initialized successfully');
        
        return [recorderNode, audioContext, stream];
        
    } catch (error) {
        console.error('Error starting audio recorder worklet:', error);
        throw error;
    }
}