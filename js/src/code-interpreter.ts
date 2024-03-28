import { ProcessMessage, Sandbox, SandboxOpts } from 'e2b'
import { JupyterKernelWebSocket, Cell } from './messaging'
import { createDeferredPromise } from './utils'

interface Kernels {
  [kernelID: string]: JupyterKernelWebSocket
}

export interface CreateKernelProps {
  cwd: string
  kernelName?: string
}

/**
 * E2B code interpreter sandbox extension.
 */
export class CodeInterpreter extends Sandbox {
  private static template = 'code-interpreter-stateful'
  public notebook: JupyterExtension

  constructor(opts?: SandboxOpts) {
    super({ template: opts?.template || CodeInterpreter.template, ...opts })
    this.notebook = new JupyterExtension(this)
  }

  /**
   * Creates a new CodeInterpreter sandbox.
   * @returns New CodeInterpreter sandbox
   *
   * @example
   * ```ts
   * const sandbox = await CodeInterpreter.create()
   * ```
   * @constructs CodeInterpreter
   */
  static async create<S extends typeof CodeInterpreter>(
    this: S
  ): Promise<InstanceType<S>>
  /**
   * Creates a new CodeInterpreter sandbox from the template with the specified ID.
   * @param template Sandbox template ID or name (this extension has some specific requirements for the template, refer to docs for more info)
   * @returns New CodeInterpreter sandbox
   *
   * @example
   * ```ts
   * const sandbox = await CodeInterpreter.create("sandboxTemplateID")
   * ```
   */
  static async create<S extends typeof CodeInterpreter>(
    this: S,
    template: string
  ): Promise<InstanceType<S>>
  /**
   * Creates a new CodeInterpreter from the specified options.
   * @param opts Sandbox options
   * @returns New CodeInterpreter
   *
   * @example
   * ```ts
   * const sandbox = await CodeInterpreter.create({
   *   onStdout: console.log,
   * })
   * ```
   */
  static async create<S extends typeof CodeInterpreter>(
    this: S,
    opts: SandboxOpts
  ): Promise<InstanceType<S>>
  static async create(optsOrTemplate?: string | SandboxOpts) {
    const opts: SandboxOpts | undefined =
      typeof optsOrTemplate === 'string'
        ? { template: optsOrTemplate }
        : optsOrTemplate
    const sandbox = new this(opts)
    await sandbox._open({ timeout: opts?.timeout })

    // Connect to the default kernel, do this in the background
    sandbox.notebook.connect()

    return sandbox
  }

  /**
   * Reconnects to an existing CodeInterpreter.
   * @param sandboxID Sandbox ID
   * @returns Existing CodeInterpreter
   *
   * @example
   * ```ts
   * const sandbox = await CodeInterpreter.create()
   * const sandboxID = sandbox.id
   *
   * await sandbox.keepAlive(300 * 1000)
   * await sandbox.close()
   *
   * const reconnectedSandbox = await CodeInterpreter.reconnect(sandboxID)
   * ```
   */
  static async reconnect<S extends typeof CodeInterpreter>(
    this: S,
    sandboxID: string
  ): Promise<InstanceType<S>>
  /**
   * Reconnects to an existing CodeInterpreter.
   * @param opts Sandbox options
   * @returns Existing CodeInterpreter
   *
   * @example
   * ```ts
   * const sandbox = await CodeInterpreter.create()
   * const sandboxID = sandbox.id
   *
   * await sandbox.keepAlive(300 * 1000)
   * await sandbox.close()
   *
   * const reconnectedSandbox = await CodeInterpreter.reconnect({
   *   sandboxID,
   * })
   * ```
   */
  static async reconnect<S extends typeof CodeInterpreter>(
    this: S,
    opts: Omit<SandboxOpts, 'id' | 'template'> & { sandboxID: string }
  ): Promise<InstanceType<S>>
  static async reconnect<S extends typeof CodeInterpreter>(
    this: S,
    sandboxIDorOpts:
      | string
      | (Omit<SandboxOpts, 'id' | 'template'> & { sandboxID: string })
  ): Promise<InstanceType<S>> {
    let id: string
    let opts: SandboxOpts
    if (typeof sandboxIDorOpts === 'string') {
      id = sandboxIDorOpts
      opts = {}
    } else {
      id = sandboxIDorOpts.sandboxID
      opts = sandboxIDorOpts
    }

    const sandboxIDAndClientID = id.split('-')
    const sandboxID = sandboxIDAndClientID[0]
    const clientID = sandboxIDAndClientID[1]
    opts.__sandbox = { sandboxID, clientID, templateID: 'unknown' }

    const sandbox = new this(opts) as InstanceType<S>
    await sandbox._open({ timeout: opts?.timeout })

    sandbox.notebook.connect()
    return sandbox
  }

  async close() {
    await this.notebook.close()
    await super.close()
  }
}

export class JupyterExtension {
  private readonly defaultKernelID: Promise<string>
  private readonly setDefaultKernelID: (kernelID: string) => void
  private connectedKernels: Kernels = {}
  private sandbox: CodeInterpreter

  constructor(sandbox: CodeInterpreter) {
    this.sandbox = sandbox
    const { promise, resolve } = createDeferredPromise<string>()
    this.defaultKernelID = promise
    this.setDefaultKernelID = resolve
  }

  async connect(timeout?: number) {
    return this.startConnectingToDefaultKernel(this.setDefaultKernelID, {
      timeout: timeout
    })
  }

  /**
   * Executes a code cell in a notebool cell.
   *
   * This method sends the provided code to a specified kernel in a remote notebook for execution.

   * @param code The code to be executed in the notebook cell.
   * @param kernelID The ID of the kernel to execute the code on. If not provided, the default kernel is used.
   * @param onStdout A callback function to handle standard output messages from the code execution.
   * @param onStderr A callback function to handle standard error messages from the code execution.
   * @returns A promise that resolves with the result of the code execution.
   */
  async execCell(
    code: string,
    kernelID?: string,
    onStdout?: (msg: ProcessMessage) => any,
    onStderr?: (msg: ProcessMessage) => any
  ): Promise<Cell> {
    kernelID = kernelID || (await this.defaultKernelID)
    let ws = this.connectedKernels[kernelID]

    if (!ws) {
      const url = `${this.sandbox.getProtocol(
        'ws'
      )}://${this.sandbox.getHostname(8888)}/api/kernels/${kernelID}/channels`
      ws = new JupyterKernelWebSocket(url)
      await ws.connect()
      this.connectedKernels[kernelID] = ws
    }

    return await ws.sendExecutionMessage(code, onStdout, onStderr)
  }

  private async startConnectingToDefaultKernel(
    resolve: (value: string) => void,
    opts?: { timeout?: number }
  ) {
    const kernelID = (
      await this.sandbox.filesystem.read('/root/.jupyter/kernel_id', opts)
    ).trim()
    await this.connectToKernelWS(kernelID)
    resolve(kernelID)
  }

  /**
   * Connects to a kernel's WebSocket.
   *
   * This method establishes a WebSocket connection to the specified kernel. It is used internally
   * to facilitate real-time communication with the kernel, enabling operations such as executing
   * code and receiving output. The connection details are managed within the method, including
   * the retrieval of the necessary WebSocket URL from the kernel's information.
   *
   * @param kernelID The unique identifier of the kernel to connect to.
   * @throws {Error} Throws an error if the connection to the kernel's WebSocket cannot be established.
   */
  private async connectToKernelWS(kernelID: string) {
    const url = `${this.sandbox.getProtocol('ws')}://${this.sandbox.getHostname(
      8888
    )}/api/kernels/${kernelID}/channels`
    const ws = new JupyterKernelWebSocket(url)
    await ws.connect()
    this.connectedKernels[kernelID] = ws
  }

  /**
   * Creates a new Jupyter kernel. It can be useful if you want to have multiple independent code execution environments.
   *
   * The kernel can be optionally configured to start in a specific working directory and/or
   * with a specific kernel name. If no kernel name is provided, the default kernel will be used.
   * Once the kernel is created, this method establishes a WebSocket connection to the new kernel for
   * real-time communication.
   *
   * @param cwd Sets the current working directory where the kernel should start. Defaults to "/home/user".
   * @param kernelName The name of the kernel to create, useful if you have multiple kernel types. If not provided, the default kernel will be used.
   * @returns A promise that resolves with the ID of the newly created kernel.
   * @throws {Error} Throws an error if the kernel creation fails.
   */
  async createKernel(
    cwd: string = '/home/user',
    kernelName?: string
  ): Promise<string> {
    const data: CreateKernelProps = { cwd }
    if (kernelName) {
      data.kernelName = kernelName
    }

    const response = await fetch(
      `${this.sandbox.getProtocol()}://${this.sandbox.getHostname(
        8888
      )}/api/kernels`,
      {
        method: 'POST',
        body: JSON.stringify(data)
      }
    )

    if (!response.ok) {
      throw new Error(`Failed to create kernel: ${response.statusText}`)
    }

    const kernelID = (await response.json()).id
    await this.connectToKernelWS(kernelID)
    return kernelID
  }

  /**
   * Restarts an existing Jupyter kernel. This can be useful to reset the kernel's state or to recover from errors.
   *
   * @param kernelID The unique identifier of the kernel to restart. If not provided, the default kernel is restarted.
   * @throws {Error} Throws an error if the kernel restart fails or if the operation times out.
   */
  async restartKernel(kernelID?: string) {
    kernelID = kernelID || (await this.defaultKernelID)
    this.connectedKernels[kernelID].close()
    delete this.connectedKernels[kernelID]

    const response = await fetch(
      `${this.sandbox.getProtocol()}://${this.sandbox.getHostname(
        8888
      )}/api/kernels/${kernelID}/restart`,
      {
        method: 'POST'
      }
    )

    if (!response.ok) {
      throw new Error(`Failed to restart kernel ${kernelID}`)
    }

    await this.connectToKernelWS(kernelID)
  }

  /**
   * Shuts down an existing Jupyter kernel. This method is used to gracefully terminate a kernel's process.

   * @param kernelID The unique identifier of the kernel to shutdown. If not provided, the default kernel is shutdown.
   * @throws {Error} Throws an error if the kernel shutdown fails or if the operation times out.
   */
  async shutdownKernel(kernelID?: string) {
    kernelID = kernelID || (await this.defaultKernelID)
    this.connectedKernels[kernelID].close()
    delete this.connectedKernels[kernelID]

    const response = await fetch(
      `${this.sandbox.getProtocol()}://${this.sandbox.getHostname(
        8888
      )}/api/kernels/${kernelID}`,
      {
        method: 'DELETE'
      }
    )

    if (!response.ok) {
      throw new Error(`Failed to shutdown kernel ${kernelID}`)
    }
  }

  /**
   * Lists all available Jupyter kernels.
   *
   * This method fetches a list of all currently available Jupyter kernels from the server. It can be used
   * to retrieve the IDs of all kernels that are currently running or available for connection.
   *
   * @returns A promise that resolves to an array of kernel IDs.
   * @throws {Error} Throws an error if the request to list kernels fails.
   */
  async listKernels(): Promise<string[]> {
    const response = await fetch(
      `${this.sandbox.getProtocol()}://${this.sandbox.getHostname(
        8888
      )}/api/kernels`,
      {
        method: 'GET'
      }
    )

    if (!response.ok) {
      throw new Error(`Failed to list kernels: ${response.statusText}`)
    }

    return (await response.json()).map((kernel: { id: string }) => kernel.id)
  }

  /**
   * Close all the websocket connections to the kernels. It doesn't shutdown the kernels.
   */
  async close() {
    for (const kernelID in this.connectedKernels) {
      this.connectedKernels[kernelID].close()
    }
  }
}
