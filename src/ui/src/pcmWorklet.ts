class PCMProcessor extends AudioWorkletProcessor {
  private readonly inputSampleRate = sampleRate;
  private readonly outputSampleRate = 16000;

  process(inputs: Float32Array[][]) {
    const input = inputs[0][0];
    if (!input) {
      return true;
    }

    const ratio = this.inputSampleRate / this.outputSampleRate;
    const outputLength = Math.floor(input.length / ratio);
    const output = new Int16Array(outputLength);
    for (let i = 0; i < outputLength; i++) {
      const idx = Math.floor(i * ratio);
      let s = input[idx];
      s = Math.max(-1, Math.min(1, s));
      output[i] = s * 0x7fff;
    }
    this.port.postMessage(output.buffer);
    return true;
  }
}

registerProcessor('pcm-processor', PCMProcessor);
export {};

