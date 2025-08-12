/**
 * Audio player worklet for PCM audio playback
 */

export async function startAudioPlayerWorklet() {
    try {
        // Create audio context with appropriate sample rate for playback
        const audioContext = new (window.AudioContext || window.webkitAudioContext)({
            sampleRate: 24000  // 24kHz for Gemini audio output
        });
        
        // Load the PCM player processor
        await audioContext.audioWorklet.addModule('/static/js/pcm-player-processor.js');
        
        // Create the worklet node
        const playerNode = new AudioWorkletNode(audioContext, 'pcm-player-processor');
        
        // Connect to the audio destination (speakers)
        playerNode.connect(audioContext.destination);
        
        // Resume audio context if it's suspended
        if (audioContext.state === 'suspended') {
            await audioContext.resume();
        }
        
        console.log('Audio player worklet initialized successfully');
        
        return [playerNode, audioContext];
        
    } catch (error) {
        console.error('Error starting audio player worklet:', error);
        throw error;
    }
}