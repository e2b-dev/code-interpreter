import { ConnectionConfig, Sandbox as BaseSandbox, TimeoutError } from 'e2b'

import { Result, Execution, OutputMessage, parseOutput, extractError } from './messaging'

function formatRequestTimeoutError(error: unknown) {
  if (error instanceof Error && error.name === 'AbortError') {
    return new TimeoutError('Request timed out — the \'requestTimeoutMs\' option can be used to increase this timeout')
  }

  return error
}

function formatExecutionTimeoutError(error: unknown) {
  if (error instanceof Error && error.name === 'AbortError') {
    return new TimeoutError('Execution timed out — the \'timeoutMs\' option can be used to increase this timeout')
  }

  return error
}

async function* readLines(stream: ReadableStream<Uint8Array>) {
  const reader = stream.getReader();
  let buffer = ''

  try {
    while (true) {
      const { done, value } = await reader.read();

      if (value !== undefined) {
        buffer += new TextDecoder().decode(value)
      }

      if (done) {
        if (buffer.length > 0) {
          yield buffer
        }
        break
      }

      let newlineIdx = -1

      do {
        newlineIdx = buffer.indexOf('\n')
        if (newlineIdx !== -1) {
          yield buffer.slice(0, newlineIdx)
          buffer = buffer.slice(newlineIdx + 1)
        }
      } while (newlineIdx !== -1)
    }
  } finally {
    reader.releaseLock()
  }
}

/**
 * Code interpreter module for executing code in a stateful context.
 */
export class JupyterExtension {
  private static readonly execTimeoutMs = 300_000
  private static readonly defaultKernelID = 'default'

  constructor(private readonly url: string, private readonly connectionConfig: ConnectionConfig) { }

  /**
   * Runs the code in the specified context, if not specified, the default context is used.
   * You can reference previously defined variables, imports, and functions in the code.
   *
   * @param code The code to execute
   * @param opts Options for executing the code
   * @param opts.kernelID The context ID to run the code in
   * @param opts.onStdout Callback for handling stdout messages
   * @param opts.onStderr Callback for handling stderr messages
   * @param opts.onResult Callback for handling the final result
   * @param opts.envs Environment variables to set for the execution
   * @param opts.timeoutMs Max time to wait for the execution to finish
   * @param opts.requestTimeoutMs Max time to wait for the request to finish
   * @returns Execution object
   */
  async execCell(
    code: string,
    opts?: {
      kernelID?: string,
      onStdout?: (output: OutputMessage) => (Promise<any> | any),
      onStderr?: (output: OutputMessage) => (Promise<any> | any),
      onResult?: (data: Result) => (Promise<any> | any),
      envs?: Record<string, string>,
      timeoutMs?: number,
      requestTimeoutMs?: number,
    },
  ): Promise<Execution> {
    const controller = new AbortController()

    const requestTimeout = opts?.requestTimeoutMs ?? this.connectionConfig.requestTimeoutMs

    const reqTimer = requestTimeout ? setTimeout(() => {
      controller.abort()
    }, requestTimeout)
      : undefined

    try {
      const res = await fetch(`${this.url}/execute`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          code,
          context_id: opts?.kernelID,
          env_vars: opts?.envs,
        }),
        signal: controller.signal,
        keepalive: true,
      })

      const error = await extractError(res)
      if (error) {
        throw error
      }

      if (!res.body) {
        throw new Error(`Not response body: ${res.statusText} ${await res?.text()}`)
      }

      clearTimeout(reqTimer)

      const bodyTimeout = opts?.timeoutMs ?? JupyterExtension.execTimeoutMs

      const bodyTimer = bodyTimeout
        ? setTimeout(() => {
          controller.abort()
        }, bodyTimeout)
        : undefined

      const execution = new Execution()


      try {
        for await (const chunk of readLines(res.body)) {
          await parseOutput(execution, chunk, opts?.onStdout, opts?.onStderr, opts?.onResult)
        }
      } catch (error) {
        throw formatExecutionTimeoutError(error)
      } finally {
        clearTimeout(bodyTimer)
      }

      return execution
    } catch (error) {
      throw formatRequestTimeoutError(error)
    }
  }

  /**
   * Creates a new context to run code in.
   *
   * @param cwd The working directory for the context
   * @param kernelName The name of the context
   * @param requestTimeoutMs Max time to wait for the request to finish
   * @returns The context ID
   */
  async createKernel({
    cwd,
    kernelName,
    requestTimeoutMs,
  }: {
    cwd?: string,
    kernelName?: string,
    requestTimeoutMs?: number,
  } = {}): Promise<string> {
    try {

      const res = await fetch(`${this.url}/contexts`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name: kernelName,
          cwd,
        }),
        keepalive: true,
        signal: this.connectionConfig.getSignal(requestTimeoutMs),
      })

      const error = await extractError(res)
      if (error) {
        throw error
      }

      const data = await res.json()
      return data.id
    } catch (error) {
      throw formatRequestTimeoutError(error)
    }
  }

  /**
   * Restarts the context.
   * Restarting will clear all variables, imports, and other settings set during previous executions.
   *
   * @param kernelID The context ID to restart
   * @param requestTimeoutMs Max time to wait for the request to finish
   */
  async restartKernel({
    kernelID,
    requestTimeoutMs,
  }: {
    kernelID?: string,
    requestTimeoutMs?: number,
  } = {}): Promise<void> {
    try {
      kernelID = kernelID || JupyterExtension.defaultKernelID
      const res = await fetch(`${this.url}/contexts/${kernelID}/restart`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        keepalive: true,
        signal: this.connectionConfig.getSignal(requestTimeoutMs),
      })

      const error = await extractError(res)
      if (error) {
        throw error
      }
    } catch (error) {
      throw formatRequestTimeoutError(error)
    }
  }

  /**
   * Shuts down the context.
   *
   * @param kernelID The context ID to shut down
   * @param requestTimeoutMs Max time to wait for the request to finish
   */
  async shutdownKernel({
    kernelID,
    requestTimeoutMs,
  }: {
    kernelID?: string,
    requestTimeoutMs?: number,
  } = {}): Promise<void> {
    try {

      kernelID = kernelID || JupyterExtension.defaultKernelID

      const res = await fetch(`${this.url}/contexts/${kernelID}`, {
        method: 'DELETE',
        keepalive: true,
        signal: this.connectionConfig.getSignal(requestTimeoutMs),
      })

      const error = await extractError(res)
      if (error) {
        throw error
      }
    } catch (error) {
      throw formatRequestTimeoutError(error)
    }
  }

  /**
   * Lists all available contexts.
   *
   * @param requestTimeoutMs Max time to wait for the request to finish
   * @returns List of context IDs and names
   */
  async listKernels({
    requestTimeoutMs,
  }: {
    requestTimeoutMs?: number,
  } = {}): Promise<{ kernelID: string, name: string }[]> {
    try {
      const res = await fetch(`${this.url}/contexts`, {
        keepalive: true,
        signal: this.connectionConfig.getSignal(requestTimeoutMs),
      })

      const error = await extractError(res)
      if (error) {
        throw error
      }

      return (await res.json()).map((kernel: any) => ({ kernelID: kernel.id, name: kernel.name }))
    } catch (error) {
      throw formatRequestTimeoutError(error)
    }
  }
}

/**
 * Code interpreter module for executing code in a stateful context.
 */
export class Sandbox extends BaseSandbox {
  protected static override readonly defaultTemplate: string = 'code-interpreter-beta'
  protected static readonly jupyterPort = 49999

  readonly notebook = new JupyterExtension(
    `${this.connectionConfig.debug ? 'http' : 'https'}://${this.getHost(Sandbox.jupyterPort)}`,
    this.connectionConfig,
  )
}
