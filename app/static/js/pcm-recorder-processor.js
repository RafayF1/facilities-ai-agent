/**
 * PCM Recorder Processor - AudioWorklet for capturing microphone audio
 */

class PCMRecorderProcessor extends AudioWorkletProcessor {
    constructor() {
        super();
        
        // Buffer for collecting samples before sending
        this.bufferSize = 1024; // Send in chunks of 1024 samples
        this.buffer = new Float32Array(this.bufferSize);
        this.bufferIndex = 0;
        
        console.log('PCM Recorder Processor initialized');
    }
    
    process(inputs, outputs, parameters) {
        const input = inputs[0];
        
        if (input && input.length > 0) {
            const inputChannel = input[0]; // Use first channel (mono)
            
            // Process each sample
            for (let i = 0; i < inputChannel.length; i++) {
                // Add sample to buffer
                this.buffer[this.bufferIndex] = inputChannel[i];
                this.bufferIndex++;
                
                // When buffer is full, convert and send
                if (this.bufferIndex >= this.bufferSize) {
                    this.sendAudioData();
                    this.bufferIndex = 0;
                }
            }
        }
        
        // Keep the processor alive
        return true;
    }
    
    sendAudioData() {
        try {
            // Convert Float32 samples to Int16 PCM
            const int16Buffer = new Int16Array(this.bufferSize);
            
            for (let i = 0; i < this.bufferSize; i++) {
                // Clamp and convert from Float32 (-1.0 to 1.0) to Int16 (-32768 to 32767)
                const sample = Math.max(-1.0, Math.min(1.0, this.buffer[i]));
                int16Buffer[i] = Math.round(sample * 32767);
            }
            
            // Send the PCM data to the main thread
            this.port.postMessage(int16Buffer.buffer);
            
        } catch (error) {
            console.error('Error sending audio data:', error);
        }
    }
}

// Register the processor
registerProcessor('pcm-recorder-processor', PCMRecorderProcessor);