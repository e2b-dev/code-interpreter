import IWebSocket from 'isomorphic-ws'
import { ProcessMessage } from 'e2b'

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
    public tracebackRaw: string[],
  ) { }

  /**
   * Returns the traceback of the error as a string.
   */
  traceback(): string {
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
 * This is result returned by ipython kernel: https://ipython.readthedocs.io/en/stable/development/execution.html#execution-semantics
 *
 *
 * The result can contain multiple types of data, such as text, images, plots, etc. Each type of data is represented
 * as a string, and the result can contain multiple types of data. The text representation is always present, and
 * the other representations are optional.
 */
export class Data {
  /**
   * Text representation of the data. Always present.
   */
  readonly text: string
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
      if (![
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
      ].includes(key)) {
        this.extra[key] = data[key]
      }
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
export class Result {
  constructor(
    /**
     * List of result of the cell (interactively interpreted last line), display calls, e.g. matplotlib plots.
     */
    public data: Data[],
    /**
     * Logs printed to stdout and stderr during execution.
     */
    public logs: Logs,
    /**
     * An Error object if an error occurred, null otherwise.
     */
    public error?: ExecutionError,
  ) { }

  /**
   * Returns the text representation of the main result of the cell.
   */
  get text(): string | undefined {
    for (const data of this.data) {
      if (data.isMainResult) {
        return data.text
      }
    }
  }
}

/**
 * Represents the execution of a cell in the Jupyter kernel.
 * It's an internal class used by JupyterKernelWebSocket.
 */
class CellExecution {
  result: Result
  onStdout?: (out: ProcessMessage) => Promise<void> | void
  onStderr?: (out: ProcessMessage) => Promise<void> | void
  inputAccepted: boolean = false

  constructor(
    onStdout?: (out: ProcessMessage) => Promise<void> | void,
    onStderr?: (out: ProcessMessage) => Promise<void> | void
  ) {
    this.result = new Result([], { stdout: [], stderr: [] })
    this.onStdout = onStdout
    this.onStderr = onStderr
  }
}

interface Cells {
  [id: string]: CellExecution
}

export class JupyterKernelWebSocket {
  // native websocket
  private _ws?: IWebSocket

  private set ws(ws: IWebSocket) {
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
    this._ws = new IWebSocket(this.url)
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

      const result = cell.result
      if (message.msg_type == 'error') {
        result.error = new ExecutionError(
          message.content.ename,
          message.content.evalue,
          message.content.traceback,
        )
      } else if (message.msg_type == 'stream') {
        if (message.content.name == 'stdout') {
          result.logs.stdout.push(message.content.text)
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
          result.logs.stderr.push(message.content.text)
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
        result.data.push(new Data(message.content.data, false))
      } else if (message.msg_type == 'execute_result') {
        result.data.push(new Data(message.content.data, true))
      } else if (message.msg_type == 'status') {
        if (message.content.execution_state == 'idle') {
          if (cell.inputAccepted) {
            this.idAwaiter[parentMsgId](result)
          }
        } else if (message.content.execution_state == 'error') {
          result.error = new ExecutionError(
            message.content.ename,
            message.content.evalue,
            message.content.traceback,
          )
          this.idAwaiter[parentMsgId](result)
        }
      } else if (message.msg_type == 'execute_reply') {
        if (message.content.status == 'error') {
          result.error = new ExecutionError(
            message.content.ename,
            message.content.evalue,
            message.content.traceback,
          )
        } else if (message.content.status == 'ok') {
          return
        }
      } else if (message.msg_type == 'execute_input') {
        cell.inputAccepted = true
      } else {
        console.log('[UNHANDLED MESSAGE TYPE]:', message.msg_type)
      }
    }
  }

  // communication
  /**
   * Sends code to be executed by Jupyter kernel.
   * @param code Code to be executed.
   * @param onStdout Callback for stdout messages.
   * @param onStderr Callback for stderr messages.
   * @param timeout Time in milliseconds to wait for response.
   * @returns Promise with execution result.
   */
  public sendExecutionMessage(
    code: string,
    onStdout?: (out: ProcessMessage) => Promise<void> | void,
    onStderr?: (out: ProcessMessage) => Promise<void> | void,
    timeout?: number
  ) {
    return new Promise<Result>((resolve, reject) => {
      const msg_id = crypto.randomUUID()
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
      this.cells[msg_id] = new CellExecution(onStdout, onStderr)
      this.idAwaiter[msg_id] = (responseData: Result) => {
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

      this.ws.onclose = (e: IWebSocket.CloseEvent) => {
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
    const session = crypto.randomUUID()
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
