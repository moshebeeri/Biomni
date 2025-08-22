import { PythonShell, Options } from 'python-shell';
import { EventEmitter } from 'events';
import path from 'path';
import fs from 'fs';

export interface BiomniMessage {
  type: string;
  content?: string;
  tool_execution?: {
    name: string;
    status: string;
    category: string;
  };
  insight?: string;
  code_artifact?: {
    language: string;
    content: string;
  };
  error?: string;
  [key: string]: any;
}

export class BiomniAgent extends EventEmitter {
  private pythonShell: PythonShell | null = null;
  private agentId: string;
  private userId: string;
  private isInitialized: boolean = false;
  private messageQueue: any[] = [];

  constructor(userId: string, agentId?: string) {
    super();
    this.userId = userId;
    this.agentId = agentId || `agent_${userId}_${Date.now()}`;
  }

  async initialize(): Promise<void> {
    return new Promise((resolve, reject) => {
      // Ensure data directories exist
      const dataDir = `/tmp/nibr_data/agents/${this.userId}`;
      if (!fs.existsSync(dataDir)) {
        fs.mkdirSync(dataDir, { recursive: true });
      }

      // Path to Python wrapper script
      const scriptPath = path.join(
        process.cwd(),
        'scripts',
        'biomni_wrapper.py'
      );

      // Check if script exists, if not use the one from nibr/canvas
      const actualScriptPath = fs.existsSync(scriptPath) 
        ? scriptPath 
        : path.join(__dirname, '../../../../scripts/biomni_wrapper.py');

      const options: Options = {
        mode: 'json' as any,
        pythonOptions: ['-u'], // Unbuffered output
        scriptPath: path.dirname(actualScriptPath),
        args: [this.agentId, this.userId],
        env: {
          ...process.env,
          PYTHONPATH: process.env.PYTHONPATH || '',
          // Use temp directory for local development
          DATA_PATH: '/tmp/nibr_data'
        }
      };

      try {
        this.pythonShell = new PythonShell(
          path.basename(actualScriptPath),
          options
        );

        this.pythonShell.on('message', (message: BiomniMessage) => {
          this.handleMessage(message);
        });

        this.pythonShell.on('error', (err) => {
          console.error('Python shell error:', err);
          this.emit('error', err);
        });

        this.pythonShell.on('close', () => {
          console.log('Python shell closed');
          this.emit('close');
        });

        // Wait for initialization
        const initHandler = (message: BiomniMessage) => {
          if (message.type === 'initialized' || message.type === 'ready') {
            this.isInitialized = true;
            this.removeListener('message', initHandler);
            
            // Process queued messages
            while (this.messageQueue.length > 0) {
              const queuedMsg = this.messageQueue.shift();
              this.send(queuedMsg);
            }
            
            resolve();
          } else if (message.type === 'error') {
            this.removeListener('message', initHandler);
            reject(new Error(message.message || 'Failed to initialize'));
          }
        };

        this.on('message', initHandler);

        // Set timeout for initialization
        setTimeout(() => {
          if (!this.isInitialized) {
            this.removeListener('message', initHandler);
            reject(new Error('Initialization timeout'));
          }
        }, 30000); // 30 second timeout

      } catch (error) {
        reject(error);
      }
    });
  }

  private handleMessage(message: BiomniMessage) {
    // console.log('Received from Python:', message);
    this.emit('message', message);

    // Emit specific events based on message type
    switch (message.type) {
      case 'step':
        this.emit('step', message);
        break;
      case 'complete':
        this.emit('complete', message);
        break;
      case 'error':
        this.emit('error', new Error(message.message || 'Unknown error'));
        break;
      case 'tool_execution':
        this.emit('tool', message.tool_execution);
        break;
      case 'insight':
        this.emit('insight', message.insight);
        break;
      case 'code_artifact':
        this.emit('code', message.code_artifact);
        break;
    }
  }

  private send(message: any): void {
    if (!this.isInitialized && message.type !== 'ping') {
      // Queue messages until initialized
      this.messageQueue.push(message);
      return;
    }

    if (this.pythonShell) {
      this.pythonShell.send(message);
    } else {
      throw new Error('Python shell not initialized');
    }
  }

  async execute(prompt: string): Promise<AsyncGenerator<BiomniMessage>> {
    const self = this;
    
    return async function* () {
      const messages: BiomniMessage[] = [];
      let isComplete = false;

      // Set up listeners
      const messageHandler = (msg: BiomniMessage) => {
        messages.push(msg);
        if (msg.type === 'complete') {
          isComplete = true;
        }
      };

      self.on('message', messageHandler);

      // Send execute command
      self.send({ type: 'execute', prompt });

      // Yield messages as they come
      while (!isComplete) {
        if (messages.length > 0) {
          const msg = messages.shift()!;
          yield msg;
          
          if (msg.type === 'complete') {
            break;
          }
        } else {
          // Wait a bit for more messages
          await new Promise(resolve => setTimeout(resolve, 100));
        }
      }

      // Clean up listener
      self.removeListener('message', messageHandler);
    }();
  }

  async executeSync(prompt: string): Promise<string> {
    return new Promise((resolve, reject) => {
      const results: string[] = [];
      let timeout: NodeJS.Timeout;

      const messageHandler = (msg: BiomniMessage) => {
        if (msg.type === 'step' && msg.content) {
          results.push(msg.content);
        } else if (msg.type === 'complete') {
          clearTimeout(timeout);
          this.removeListener('message', messageHandler);
          resolve(results.join('\n'));
        } else if (msg.type === 'error') {
          clearTimeout(timeout);
          this.removeListener('message', messageHandler);
          reject(new Error(msg.message || 'Execution failed'));
        }
      };

      this.on('message', messageHandler);
      this.send({ type: 'execute', prompt });

      // Set execution timeout
      timeout = setTimeout(() => {
        this.removeListener('message', messageHandler);
        reject(new Error('Execution timeout'));
      }, 600000); // 10 minute timeout
    });
  }

  async addTool(toolCode: string, toolName: string, description?: string): Promise<void> {
    return new Promise((resolve, reject) => {
      const handler = (msg: BiomniMessage) => {
        if (msg.type === 'tool_added') {
          this.removeListener('message', handler);
          resolve();
        } else if (msg.type === 'error') {
          this.removeListener('message', handler);
          reject(new Error(msg.message || 'Failed to add tool'));
        }
      };

      this.on('message', handler);
      this.send({
        type: 'add_tool',
        code: toolCode,
        name: toolName,
        description: description || ''
      });

      // Timeout
      setTimeout(() => {
        this.removeListener('message', handler);
        reject(new Error('Add tool timeout'));
      }, 10000);
    });
  }

  async addData(dataPath: string, description: string): Promise<void> {
    return new Promise((resolve, reject) => {
      const handler = (msg: BiomniMessage) => {
        if (msg.type === 'data_added') {
          this.removeListener('message', handler);
          resolve();
        } else if (msg.type === 'error') {
          this.removeListener('message', handler);
          reject(new Error(msg.message || 'Failed to add data'));
        }
      };

      this.on('message', handler);
      this.send({
        type: 'add_data',
        path: dataPath,
        description: description
      });

      // Timeout
      setTimeout(() => {
        this.removeListener('message', handler);
        reject(new Error('Add data timeout'));
      }, 10000);
    });
  }

  async listTools(): Promise<any[]> {
    return new Promise((resolve, reject) => {
      const handler = (msg: BiomniMessage) => {
        if (msg.type === 'tools_list') {
          this.removeListener('message', handler);
          resolve(msg.tools || []);
        } else if (msg.type === 'error') {
          this.removeListener('message', handler);
          reject(new Error(msg.message || 'Failed to list tools'));
        }
      };

      this.on('message', handler);
      this.send({ type: 'list_tools' });

      // Timeout
      setTimeout(() => {
        this.removeListener('message', handler);
        reject(new Error('List tools timeout'));
      }, 5000);
    });
  }

  terminate(): void {
    if (this.pythonShell) {
      this.pythonShell.kill();
      this.pythonShell = null;
    }
    this.isInitialized = false;
  }

  isReady(): boolean {
    return this.isInitialized;
  }
}