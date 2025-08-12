/**
 * PCM Player Processor - AudioWorklet for playing PCM audio data with interruption support
 */

class PCMPlayerProcessor extends AudioWorkletProcessor {
    constructor() {
        super();
        
        // Initialize circular buffer for 180 seconds of 24kHz audio
        this.bufferSize = 24000 * 180; // 180 seconds at 24kHz
        this.ringBuffer = new Float32Array(this.bufferSize);
        this.writeIndex = 0;
        this.readIndex = 0;
        this.availableSamples = 0;
        
        // Set up message port for receiving audio data and commands
        this.port.onmessage = (event) => {
            if (event.data && event.data.command === 'clear_buffer') {
                this.clearBuffer();
            } else {
                this.handleIncomingAudio(event.data);
            }
        };
        
        console.log('PCM Player Processor initialized with interruption support');
    }
    
    clearBuffer() {
        // Immediately clear all buffered audio to stop playback
        this.availableSamples = 0;
        this.readIndex = this.writeIndex;
        console.log('Audio buffer cleared due to interruption');
    }
    
    handleIncomingAudio(audioData) {
        if (!audioData || audioData.byteLength === 0) {
            return;
        }
        
        try {
            // Convert Int16 PCM data to Float32
            const int16Data = new Int16Array(audioData);
            const float32Data = new Float32Array(int16Data.length);
            
            // Convert from Int16 (-32768 to 32767) to Float32 (-1.0 to 1.0)
            for (let i = 0; i < int16Data.length; i++) {
                float32Data[i] = int16Data[i] / 32768.0;
            }
            
            // Write to circular buffer
            this.writeToBuffer(float32Data);
            
        } catch (error) {
            console.error('Error processing incoming audio:', error);
        }
    }
    
    writeToBuffer(samples) {
        for (let i = 0; i < samples.length; i++) {
            this.ringBuffer[this.writeIndex] = samples[i];
            this.writeIndex = (this.writeIndex + 1) % this.bufferSize;
            
            // If buffer is full, advance read index (overwrite oldest samples)
            if (this.availableSamples < this.bufferSize) {
                this.availableSamples++;
            } else {
                this.readIndex = (this.readIndex + 1) % this.bufferSize;
            }
        }
    }
    
    readFromBuffer(output, samplesNeeded) {
        const samplesToRead = Math.min(samplesNeeded, this.availableSamples);
        
        for (let i = 0; i < samplesToRead; i++) {
            const sample = this.ringBuffer[this.readIndex];
            output[i] = sample;
            this.readIndex = (this.readIndex + 1) % this.bufferSize;
        }
        
        this.availableSamples -= samplesToRead;
        
        // Fill remaining with silence if not enough samples
        for (let i = samplesToRead; i < samplesNeeded; i++) {
            output[i] = 0.0;
        }
        
        return samplesToRead;
    }
    
    process(inputs, outputs, parameters) {
        const output = outputs[0];
        
        if (output && output.length > 0) {
            const channelData = output[0];
            const samplesNeeded = channelData.length;
            
            // Read samples from buffer
            this.readFromBuffer(channelData, samplesNeeded);
            
            // Copy to all output channels (for mono to stereo conversion if needed)
            for (let channel = 1; channel < output.length; channel++) {
                output[channel].set(channelData);
            }
        }
        
        // Keep the processor alive
        return true;
    }
}

// Register the processor
registerProcessor('pcm-player-processor', PCMPlayerProcessor);