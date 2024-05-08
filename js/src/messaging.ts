import IWebSocket, { WebSocket } from 'isows'
import { ProcessMessage } from 'e2b'
import { id } from './utils'

/**
 * Represents an error that occurred during the execution of a cell.
 * The error contains the name of the error, the value of the error, and the traceback.
 */
export class ExecutionError {
  constructor(
    /**
     * Name of the error.
     **/
    public name: string,
    /**
     * Value of the error.
     **/
    public value: string,
    /**
     * The raw traceback of the error.
     **/
    public tracebackRaw: string[]
  ) { }

  /**
   * Returns the traceback of the error as a string.
   */
  get traceback(): string {
    return this.tracebackRaw.join('\n')
  }
}

/**
 * Represents a MIME type.
 */
export type MIMEType = string

/**
 * Dictionary that maps MIME types to their corresponding string representations of the data.
 */
export type RawData = {
  [key: MIMEType]: string
}

/**
 * Represents the data to be displayed as a result of executing a cell in a Jupyter notebook.
 * The result is similar to the structure returned by ipython kernel: https://ipython.readthedocs.io/en/stable/development/execution.html#execution-semantics
 *
 *
 * The result can contain multiple types of data, such as text, images, plots, etc. Each type of data is represented
 * as a string, and the result can contain multiple types of data. The display calls don't have to have text representation,
 * for the actual result the representation is always present for the result, the other representations are always optional.
 */
export class Result {
  /**
   * Text representation of the result.
   */
  readonly text?: string
  /**
   * HTML representation of the data.
   */
  readonly html?: string
  /**
   * Markdown representation of the data.
   */
  readonly markdown?: string
  /**
   * SVG representation of the data.
   */
  readonly svg?: string
  /**
   * PNG representation of the data.
   */
  readonly png?: string
  /**
   * JPEG representation of the data.
   */
  readonly jpeg?: string
  /**
   * PDF representation of the data.
   */
  readonly pdf?: string
  /**
   * LaTeX representation of the data.
   */
  readonly latex?: string
  /**
   * JSON representation of the data.
   */
  readonly json?: string
  /**
   * JavaScript representation of the data.
   */
  readonly javascript?: string
  /**
   * Extra data that can be included. Not part of the standard types.
   */
  readonly extra?: any

  readonly raw: RawData

  constructor(data: RawData, public readonly isMainResult: boolean) {
    this.text = data['text/plain']
    this.html = data['text/html']
    this.markdown = data['text/markdown']
    this.svg = data['image/svg+xml']
    this.png = data['image/png']
    this.jpeg = data['image/jpeg']
    this.pdf = data['application/pdf']
    this.latex = data['text/latex']
    this.json = data['application/json']
    this.javascript = data['application/javascript']
    this.isMainResult = isMainResult
    this.raw = data

    this.extra = {}
    for (const key of Object.keys(data)) {
      if (
        ![
          'text/plain',
          'text/html',
          'text/markdown',
          'image/svg+xml',
          'image/png',
          'image/jpeg',
          'application/pdf',
          'text/latex',
          'application/json',
          'application/javascript'
        ].includes(key)
      ) {
        this.extra[key] = data[key]
      }
    }
  }

  /**
   * Returns all the formats available for the result.
   *
   * @returns Array of strings representing the formats available for the result.
   */
  formats(): string[] {
    const formats = []
    if (this.html) {
      formats.push('html')
    }
    if (this.markdown) {
      formats.push('markdown')
    }
    if (this.svg) {
      formats.push('svg')
    }
    if (this.png) {
      formats.push('png')
    }
    if (this.jpeg) {
      formats.push('jpeg')
    }
    if (this.pdf) {
      formats.push('pdf')
    }
    if (this.latex) {
      formats.push('latex')
    }
    if (this.json) {
      formats.push('json')
    }
    if (this.javascript) {
      formats.push('javascript')
    }

    for (const key of Object.keys(this.extra)) {
      formats.push(key)
    }

    return formats
  }

  /**
   * Returns the serializable representation of the result.
   */
  toJSON() {
    return {
      text: this.text,
      html: this.html,
      markdown: this.markdown,
      svg: this.svg,
      png: this.png,
      jpeg: this.jpeg,
      pdf: this.pdf,
      latex: this.latex,
      json: this.json,
      javascript: this.javascript,
      ...(Object.keys(this.extra).length > 0 ? { extra: this.extra } : {})
    }
  }
}

/**
 * Data printed to stdout and stderr during execution, usually by print statements, logs, warnings, subprocesses, etc.
 */
export type Logs = {
  /**
   * List of strings printed to stdout by prints, subprocesses, etc.
   */
  stdout: string[]
  /**
   * List of strings printed to stderr by prints, subprocesses, etc.
   */
  stderr: string[]
}

/**
 * Represents the result of a cell execution.
 */
export class Execution {
  constructor(
    /**
     * List of result of the cell (interactively interpreted last line), display calls (e.g. matplotlib plots).
     */
    public results: Result[],
    /**
     * Logs printed to stdout and stderr during execution.
     */
    public logs: Logs,
    /**
     * An Error object if an error occurred, null otherwise.
     */
    public error?: ExecutionError
  ) { }

  /**
   * Returns the text representation of the main result of the cell.
   */
  get text(): string | undefined {
    for (const data of this.results) {
      if (data.isMainResult) {
        return data.text
      }
    }
  }

  /**
   * Returns the serializable representation of the execution result.
   */
  toJSON() {
    return {
      results: this.results,
      logs: this.logs,
      error: this.error
    }
  }
}

/**
 * Represents the execution of a cell in the Jupyter kernel.
 * It's an internal class used by JupyterKernelWebSocket.
 */
class CellExecution {
  execution: Execution
  onStdout?: (out: ProcessMessage) => any
  onStderr?: (out: ProcessMessage) => any
  onResult?: (data: Result) => any
  inputAccepted: boolean = false

  constructor(
    onStdout?: (out: ProcessMessage) => any,
    onStderr?: (out: ProcessMessage) => any,
    onResult?: (data: Result) => any
  ) {
    this.execution = new Execution([], { stdout: [], stderr: [] })
    this.onStdout = onStdout
    this.onStderr = onStderr
    this.onResult = onResult
  }
}

interface Cells {
  [id: string]: CellExecution
}

export class JupyterKernelWebSocket {
  // native websocket
  private _ws?: any

  private set ws(ws: any) {
    this._ws = ws
  }

  private get ws() {
    if (!this._ws) {
      throw new Error('WebSocket is not connected.')
    }
    return this._ws
  }

  private idAwaiter: {
    [id: string]: (data?: any) => void
  } = {}

  private cells: Cells = {}

  // constructor
  /**
   * Does not start WebSocket connection!
   * You need to call connect() method first.
   */
  constructor(private readonly url: string) { }

  // public
  /**
   * Starts WebSocket connection.
   */
  connect() {
    this._ws = new WebSocket(this.url)
    return this.listen()
  }

  // events
  /**
   * Listens for messages from WebSocket server.
   *
   * Message types:
   * https://jupyter-client.readthedocs.io/en/stable/messaging.html
   *
   */
  public listenMessages() {
    this.ws.onmessage = (e: IWebSocket.MessageEvent) => {
      const message = JSON.parse(e.data.toString())
      const parentMsgId = message.parent_header.msg_id
      const cell = this.cells[parentMsgId]
      if (!cell) {
        return
      }

      const execution = cell.execution
      if (message.msg_type == 'error') {
        execution.error = new ExecutionError(
          message.content.ename,
          message.content.evalue,
          message.content.traceback
        )
      } else if (message.msg_type == 'stream') {
        if (message.content.name == 'stdout') {
          execution.logs.stdout.push(message.content.text)
          if (cell?.onStdout) {
            cell.onStdout(
              new ProcessMessage(
                message.content.text,
                new Date().getTime() * 1_000_000,
                false
              )
            )
          }
        } else if (message.content.name == 'stderr') {
          execution.logs.stderr.push(message.content.text)
          if (cell?.onStderr) {
            cell.onStderr(
              new ProcessMessage(
                message.content.text,
                new Date().getTime() * 1_000_000,
                true
              )
            )
          }
        }
      } else if (message.msg_type == 'display_data') {
        const result = new Result(message.content.data, false)
        execution.results.push(result)
        if (cell.onResult) {
          cell.onResult(result)
        }
      } else if (message.msg_type == 'execute_result') {
        const result = new Result(message.content.data, true)
        execution.results.push(result)
        if (cell.onResult) {
          cell.onResult(result)
        }
      } else if (message.msg_type == 'status') {
        if (message.content.execution_state == 'idle') {
          if (cell.inputAccepted) {
            this.idAwaiter[parentMsgId](execution)
          }
        } else if (message.content.execution_state == 'error') {
          execution.error = new ExecutionError(
            message.content.ename,
            message.content.evalue,
            message.content.traceback
          )
          this.idAwaiter[parentMsgId](execution)
        }
      } else if (message.msg_type == 'execute_reply') {
        if (message.content.status == 'error') {
          execution.error = new ExecutionError(
            message.content.ename,
            message.content.evalue,
            message.content.traceback
          )
        } else if (message.content.status == 'ok') {
          return
        }
      } else if (message.msg_type == 'execute_input') {
        cell.inputAccepted = true
      } else {
        console.warn('[UNHANDLED MESSAGE TYPE]:', message.msg_type)
      }
    }
  }

  // communication
  /**
   * Sends code to be executed by Jupyter kernel.
   * @param code Code to be executed.
   * @param onStdout Callback for stdout messages.
   * @param onStderr Callback for stderr messages.
   * @param onResult Callback function to handle the result and display calls of the code execution.
   * @param timeout Time in milliseconds to wait for response.
   * @returns Promise with execution result.
   */
  public sendExecutionMessage(
    code: string,
    onStdout?: (out: ProcessMessage) => any,
    onStderr?: (out: ProcessMessage) => any,
    onResult?: (data: Result) => any,
    timeout?: number
  ) {
    return new Promise<Execution>((resolve, reject) => {
      const msg_id = id(16)
      const data = this.sendExecuteRequest(msg_id, code)

      // give limited time for response
      let timeoutSet: number | NodeJS.Timeout
      if (timeout) {
        timeoutSet = setTimeout(() => {
          // stop waiting for response
          delete this.idAwaiter[msg_id]
          reject(
            new Error(
              `Awaiting response to "${code}" with id: ${msg_id} timed out.`
            )
          )
        }, timeout)
      }

      // expect response
      this.cells[msg_id] = new CellExecution(onStdout, onStderr, onResult)
      this.idAwaiter[msg_id] = (responseData: Execution) => {
        // stop timeout
        clearInterval(timeoutSet as number)
        // stop waiting for response
        delete this.idAwaiter[msg_id]

        resolve(responseData)
      }

      const json = JSON.stringify(data)
      this.ws.send(json)
    })
  }

  /**
   * Listens for messages from WebSocket server.
   */
  private listen() {
    return new Promise((resolve, reject) => {
      this.ws.onopen = (e: unknown) => {
        resolve(e)
      }

      // listen for messages
      this.listenMessages()

      this.ws.onclose = (e: any) => {
        reject(
          new Error(
            `WebSocket closed with code: ${e.code} and reason: ${e.reason}`
          )
        )
      }
    })
  }

  /**
   * Creates a websocket message for code execution.
   * @param msg_id Unique message id.
   * @param code Code to be executed.
   */
  private sendExecuteRequest(msg_id: string, code: string) {
    const session = id(16)
    return {
      header: {
        msg_id: msg_id,
        username: 'e2b',
        session: session,
        msg_type: 'execute_request',
        version: '5.3'
      },
      parent_header: {},
      metadata: {},
      content: {
        code: code,
        silent: false,
        store_history: false,
        user_expressions: {},
        allow_stdin: false
      }
    }
  }

  /**
   * Closes WebSocket connection.
   */
  close() {
    this.ws.close()
  }
}
