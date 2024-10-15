import { Sandbox as BaseSandbox } from 'e2b'

import { Result, Execution, OutputMessage, parseOutput, extractError } from './messaging'
import { formatExecutionTimeoutError, formatRequestTimeoutError, readLines } from "./utils";
import { JUPYTER_PORT, DEFAULT_TIMEOUT_MS } from './consts'
export type Context = {
  id: string
  language: string
  cwd: string
}

/**
 * Code interpreter module for executing code in a stateful context.
 */
export class Sandbox extends BaseSandbox {
  protected static override readonly defaultTemplate: string = 'code-interpreter-beta'

  /**
   * Runs the code in the specified context, if not specified, the default context is used.
   * You can reference previously defined variables, imports, and functions in the code.
   *
   * @param code The code to execute
   * @param opts Options for executing the code
   * @param opts.language Based on the value, a default context for the language is used. If not defined and no context is provided, the default Python context is used.
   * @param opts.context Concrete context to run the code in. If not specified, the default context for the language is used. It's mutually exclusive with the language.
   * @param opts.onStdout Callback for handling stdout messages
   * @param opts.onStderr Callback for handling stderr messages
   * @param opts.onResult Callback for handling the final result
   * @param opts.envs Environment variables to set for the execution
   * @param opts.timeoutMs Max time to wait for the execution to finish
   * @param opts.requestTimeoutMs Max time to wait for the request to finish
   * @returns Execution object
   */
  async runCode(
    code: string,
    opts?: {
      language?: string,
      context?: Context,
      onStdout?: (output: OutputMessage) => (Promise<any> | any),
      onStderr?: (output: OutputMessage) => (Promise<any> | any),
      onResult?: (data: Result) => (Promise<any> | any),
      envs?: Record<string, string>,
      timeoutMs?: number,
      requestTimeoutMs?: number,
    },
  ): Promise<Execution> {
    if (opts?.context && opts?.language) {
      throw new Error("You can provide context or language, but not both at the same time.")
    }

    const controller = new AbortController()

    const requestTimeout = opts?.requestTimeoutMs ?? this.connectionConfig.requestTimeoutMs

    const reqTimer = requestTimeout ? setTimeout(() => {
      controller.abort()
    }, requestTimeout)
      : undefined

    try {
      const res = await fetch(`${this.jupyterUrl}/execute`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          code,
          context_id: opts?.context?.id,
          language: opts?.language,
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

      const bodyTimeout = opts?.timeoutMs ?? DEFAULT_TIMEOUT_MS

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
   * @param language The name of the context
   * @param requestTimeoutMs Max time to wait for the request to finish
   * @returns The context ID
   */
  async createCodeContext({
    cwd,
    language,
    requestTimeoutMs,
  }: {
    cwd?: string,
    language?: string,
    requestTimeoutMs?: number,
  } = {}): Promise<Context> {
    try {

      const res = await fetch(`${this.jupyterUrl}/contexts`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          language: language,
          cwd,
        }),
        keepalive: true,
        signal: this.connectionConfig.getSignal(requestTimeoutMs),
      })

      const error = await extractError(res)
      if (error) {
        throw error
      }

      return await res.json()
    } catch (error) {
      throw formatRequestTimeoutError(error)
    }
  }

  protected get jupyterUrl(): string {
    return  `${this.connectionConfig.debug ? 'http' : 'https'}://${this.getHost(JUPYTER_PORT)}`
  }
}
