import { ProcessMessage, Sandbox, SandboxOpts } from 'e2b'
import { Result, JupyterKernelWebSocket, Execution } from './messaging'
import { createDeferredPromise, id } from './utils'

interface Kernels {
  [kernelID: string]: JupyterKernelWebSocket
}

/**
 * E2B code interpreter sandbox extension.
 */
export class CodeInterpreter extends Sandbox {
  private static template = 'code-interpreter-multikernel'

  readonly notebook = new JupyterExtension(this)

  constructor(opts?: SandboxOpts, createCalled = false) {
    super({ template: opts?.template || CodeInterpreter.template, ...opts }, createCalled)
  }

  override async _open(opts?: { timeout?: number }) {
    await super._open({ timeout: opts?.timeout })
    await this.notebook.connect(opts?.timeout)

    return this
  }

  override async close() {
    await this.notebook.close()
    await super.close()
  }
}

export class JupyterExtension {
  private readonly connectedKernels: Kernels = {}

  private readonly kernelIDPromise = createDeferredPromise<string>()
  private readonly setDefaultKernelID = this.kernelIDPromise.resolve

  private get defaultKernelID() {
    return this.kernelIDPromise.promise
  }

  constructor(private sandbox: CodeInterpreter) {}

  async connect(timeout?: number) {
    return this.startConnectingToDefaultKernel(this.setDefaultKernelID, {
      timeout
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
   * @param onResult A callback function to handle display data messages from the code execution.
   * @param timeout The maximum time to wait for the code execution to complete, in milliseconds.
   * @returns A promise that resolves with the result of the code execution.
   */
  async execCell(
    code: string,
    {
      kernelID,
      onStdout,
      onStderr,
      onResult,
      timeout
    }: {
      kernelID?: string
      onStdout?: (msg: ProcessMessage) => any
      onStderr?: (msg: ProcessMessage) => any
      onResult?: (data: Result) => any
      timeout?: number
    } = {}
  ): Promise<Execution> {
    kernelID = kernelID || (await this.defaultKernelID)
    const ws =
      this.connectedKernels[kernelID] ||
      (await this.connectToKernelWS(kernelID))

    return await ws.sendExecutionMessage(
      code,
      onStdout,
      onStderr,
      onResult,
      timeout
    )
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
   * @param sessionID The unique identifier of the session to connect to.
   * @throws {Error} Throws an error if the connection to the kernel's WebSocket cannot be established.
   */
  private async connectToKernelWS(kernelID: string, sessionID?: string) {
    const url = `${this.sandbox.getProtocol('ws')}://${this.sandbox.getHostname(
      8888
    )}/api/kernels/${kernelID}/channels`

    sessionID = sessionID || id(16)
    const ws = new JupyterKernelWebSocket(url, sessionID)
    await ws.connect()
    this.connectedKernels[kernelID] = ws

    return ws
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
    kernelName = kernelName || 'python3'


    const data = { path: id(16), kernel: {name: kernelName}, type: "notebook", name: id(16) }

    const response = await fetch(
      `${this.sandbox.getProtocol()}://${this.sandbox.getHostname(
        8888
      )}/api/sessions`,
      {
        method: 'POST',
        body: JSON.stringify(data)
      }
    )

    if (!response.ok) {
      throw new Error(`Failed to create kernel: ${response.statusText}`)
    }


    const sessionInfo = await response.json()
    const kernelID = sessionInfo.kernel.id
    const sessionID = sessionInfo.id

    const patchResponse = await fetch(
      `${this.sandbox.getProtocol()}://${this.sandbox.getHostname(
        8888
      )}/api/sessions/${sessionID}`,
      {
        method: 'PATCH',
        body: JSON.stringify({path: cwd})
      }
    )

    if (!patchResponse.ok) {
      throw new Error(`Failed to create kernel: ${response.statusText}`)
    }


    await this.connectToKernelWS(kernelID, sessionID)

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
    for (const kernelID of Object.keys(this.connectedKernels)) {
      this.connectedKernels[kernelID].close()
    }
  }
}
