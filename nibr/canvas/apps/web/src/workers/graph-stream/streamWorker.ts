import { StreamWorkerMessage, StreamConfig } from "./streamWorker.types";

export class StreamWorkerService {
  private worker: Worker | null = null;

  constructor() {
    // Check if we're in a browser environment
    if (typeof window !== 'undefined' && typeof Worker !== 'undefined') {
      try {
        // Use the correct syntax for Next.js worker loading
        this.worker = new Worker(
          new URL('./stream.worker.ts', import.meta.url),
          { type: 'module' }
        );
      } catch (error) {
        console.error('Failed to initialize Web Worker:', error);
        // Fallback: worker will be null, handle in streamData
      }
    }
  }

  async *streamData(config: StreamConfig): AsyncGenerator<any, void, unknown> {
    if (!this.worker) {
      throw new Error('Web Worker is not available or failed to initialize');
    }

    this.worker.postMessage(config);

    while (true) {
      const event: MessageEvent<StreamWorkerMessage> = await new Promise(
        (resolve) => {
          if (this.worker) {
            this.worker.onmessage = resolve;
          }
        }
      );

      const { type, data, error } = event.data;

      if (type === "error") {
        throw new Error(error);
      }

      if (type === "chunk" && data) {
        try {
          // Add error handling for JSON parsing
          yield JSON.parse(data);
        } catch (parseError) {
          console.error('Failed to parse chunk data:', data, parseError);
          // Continue processing other chunks instead of throwing
          continue;
        }
      }

      if (type === "done") {
        break;
      }
    }
  }

  terminate() {
    if (this.worker) {
      this.worker.terminate();
      this.worker = null;
    }
  }
}
