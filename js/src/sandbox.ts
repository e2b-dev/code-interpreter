import { Sandbox as BaseSandbox, InvalidArgumentError } from 'e2b'

import {
  Result,
  Execution,
  OutputMessage,
  parseOutput,
  extractError,
  ExecutionError,
} from './messaging'
import {
  formatExecutionTimeoutError,
  formatRequestTimeoutError,
  readLines,
} from './utils'
import { JUPYTER_PORT, DEFAULT_TIMEOUT_MS } from './consts'

/**
 * Represents a context for code execution.
 */
export type Context = {
  /**
   * The ID of the context.
   */
  id: string
  /**
   * The language of the context.
   */
  language: string
  /**
   * The working directory of the context.
   */
  cwd: string
}

/**
 * Options for running code.
 */
export interface RunCodeOpts {
  /**
   * Callback for handling stdout messages.
   */
  onStdout?: (output: OutputMessage) => Promise<any> | any
  /**
   * Callback for handling stderr messages.
   */
  onStderr?: (output: OutputMessage) => Promise<any> | any
  /**
   * Callback for handling the final execution result.
   */
  onResult?: (data: Result) => Promise<any> | any
  /**
   * Callback for handling the `ExecutionError` object.
   */
  onError?: (error: ExecutionError) => Promise<any> | any
  /**
   * Custom environment variables for code execution.
   *
   * @default {}
   */
  envs?: Record<string, string>
  /**
   * Timeout for the code execution in **milliseconds**.
   *
   * @default 60_000 // 60 seconds
   */
  timeoutMs?: number
  /**
   * Timeout for the request in **milliseconds**.
   *
   * @default 30_000 // 30 seconds
   */
  requestTimeoutMs?: number
}

/**
 * Options for creating a code context.
 */
export interface CreateCodeContextOpts {
  /**
   * Working directory for the context.
   *
   * @default /home/user
   */
  cwd?: string
  /**
   * Language for the context.
   *
   * @default python
   */
  language?: string
  /**
   * Timeout for the request in **milliseconds**.
   *
   * @default 30_000 // 30 seconds
   */
  requestTimeoutMs?: number
}

/**
 * E2B cloud sandbox is a secure and isolated cloud environment.
 *
 * The sandbox allows you to:
 * - Access Linux OS
 * - Create, list, and delete files and directories
 * - Run commands
 * - Run isolated code
 * - Access the internet
 *
 * Check docs [here](https://e2b.dev/docs).
 *
 * Use {@link Sandbox.create} to create a new sandbox.
 *
 * @example
 * ```ts
 * import { Sandbox } from '@e2b/code-interpreter'
 *
 * const sandbox = await Sandbox.create()
 * ```
 */
export class Sandbox extends BaseSandbox {
  protected static override readonly defaultTemplate: string =
    'code-interpreter-v1'

  /**
   * Run the code as Python.
   *
   * Specify the `language` or `context` option to run the code as a different language or in a different `Context`.
   *
   * You can reference previously defined variables, imports, and functions in the code.
   *
   * @param code code to execute.
   * @param opts options for executing the code.
   *
   * @returns `Execution` result object.
   */
  async runCode(
    code: string,
    opts?: RunCodeOpts & {
      /**
       * Language to use for code execution.
       *
       * If not defined, the default Python context is used.
       */
      language?: 'python'
    }
  ): Promise<Execution>
  /**
   * Run the code for the specified language.
   *
   * Specify the `language` or `context` option to run the code as a different language or in a different `Context`.
   * If no language is specified, Python is used.
   *
   * You can reference previously defined variables, imports, and functions in the code.
   *
   * @param code code to execute.
   * @param opts options for executing the code.
   *
   * @returns `Execution` result object.
   */
  async runCode(
    code: string,
    opts?: RunCodeOpts & {
      /**
       * Language to use for code execution.
       *
       * If not defined, the default Python context is used.
       */
      language?: string
    }
  ): Promise<Execution>
  /**
   * Runs the code in the specified context, if not specified, the default context is used.
   *
   * Specify the `language` or `context` option to run the code as a different language or in a different `Context`.
   *
   * You can reference previously defined variables, imports, and functions in the code.
   *
   * @param code code to execute.
   * @param opts options for executing the code
   *
   * @returns `Execution` result object
   */
  async runCode(
    code: string,
    opts?: RunCodeOpts & {
      /**
       * Context to run the code in.
       */
      context?: Context
    }
  ): Promise<Execution>
  async runCode(
    code: string,
    opts?: RunCodeOpts & {
      language?: string
      context?: Context
    }
  ): Promise<Execution> {
    if (opts?.context && opts?.language) {
      throw new InvalidArgumentError(
        'You can provide context or language, but not both at the same time.'
      )
    }

    const controller = new AbortController()

    const requestTimeout =
      opts?.requestTimeoutMs ?? this.connectionConfig.requestTimeoutMs

    const reqTimer = requestTimeout
      ? setTimeout(() => {
          controller.abort()
        }, requestTimeout)
      : undefined

    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    }
    if (this.envdAccessToken) {
      headers['X-Access-Token'] = this.envdAccessToken
    }

    try {
      const res = await fetch(`${this.jupyterUrl}/execute`, {
        method: 'POST',
        headers,
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
        throw new Error(
          `Not response body: ${res.statusText} ${await res?.text()}`
        )
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
          await parseOutput(
            execution,
            chunk,
            opts?.onStdout,
            opts?.onStderr,
            opts?.onResult,
            opts?.onError
          )
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
   * @param opts options for creating the context.
   *
   * @returns context object.
   */
  async createCodeContext(opts?: CreateCodeContextOpts): Promise<Context> {
    try {
      const res = await fetch(`${this.jupyterUrl}/contexts`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...this.connectionConfig.headers,
        },
        body: JSON.stringify({
          language: opts?.language,
          cwd: opts?.cwd,
        }),
        keepalive: true,
        signal: this.connectionConfig.getSignal(opts?.requestTimeoutMs),
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
    return `${this.connectionConfig.debug ? 'http' : 'https'}://${this.getHost(
      JUPYTER_PORT
    )}`
  }
}
