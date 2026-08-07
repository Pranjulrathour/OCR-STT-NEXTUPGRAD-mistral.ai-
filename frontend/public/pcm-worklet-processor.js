const LEVEL_UPDATE_EVERY_N_BLOCKS = 4; // ~30fps at a 128-sample render quantum

class PCMWorkletProcessor extends AudioWorkletProcessor {
  constructor() {
    super();
    this._blockCount = 0;
  }

  process(inputs) {
    const channelData = inputs[0]?.[0];
    if (channelData && channelData.length > 0) {
      const pcm16 = new Int16Array(channelData.length);
      let sumSquares = 0;
      for (let i = 0; i < channelData.length; i++) {
        const sample = Math.max(-1, Math.min(1, channelData[i]));
        sumSquares += sample * sample;
        pcm16[i] = sample < 0 ? sample * 32768 : sample * 32767;
      }
      this.port.postMessage({ type: "audio", buffer: pcm16.buffer }, [pcm16.buffer]);

      this._blockCount = (this._blockCount + 1) % LEVEL_UPDATE_EVERY_N_BLOCKS;
      if (this._blockCount === 0) {
        const rms = Math.sqrt(sumSquares / channelData.length);
        this.port.postMessage({ type: "level", value: rms });
      }
    }
    return true;
  }
}

registerProcessor("pcm-worklet-processor", PCMWorkletProcessor);
