import IWebSocket from 'isomorphic-ws'
import { ProcessMessage } from 'e2b'

/**
 * Represents an error that occurred during the execution of a cell.
 * The error contains the name of the error, the value of the error, and the traceback.
 *
 * @property {string} name - Name of the error.
 * @property {string} value - Value of the error.
 * @property {string} traceback - The traceback of the error.
 */
export class Error {
  name: string
  value: string
  tracebackRaw: string[]

  constructor(name: string, value: string, tracebackRaw: string[]) {
      this.name = name
      this.value = value
      this.tracebackRaw = tracebackRaw
  }

  public traceback(): string {
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
 *
 * @property {string} text - Text representation of the data. Always present.
 * @property {string} [html] - HTML representation of the data.
 * @property {string} [markdown] - Markdown representation of the data.
 * @property {string} [svg] - SVG representation of the data.
 * @property {string} [png] - PNG representation of the data.
 * @property {string} [jpeg] - JPEG representation of the data.
 * @property {string} [pdf] - PDF representation of the data.
 * @property {string} [latex] - LaTeX representation of the data.
 * @property {string} [json] - JSON representation of the data.
 * @property {string} [javascript] - JavaScript representation of the data.
 * @property {object} [extra] - Extra data that can be included. Not part of the standard types.
 * @property {boolean} isMainResult - Whether this data is the main result of the cell. There can be multiple display calls in a cell.
 * @property {RawData} raw - Dictionary that maps MIME types to their corresponding string representations of the data.
 */

export class Data {
  readonly text: string
  readonly html?: string
  readonly markdown?: string
  readonly svg?  : string
  readonly png?: string
  readonly jpeg?: string
  readonly pdf?: string
  readonly latex?: string
  readonly json?: string
  readonly javascript?: string
  readonly extra?: object

  isMainResult: boolean

  raw: RawData
}

/**
 * Data printed to stdout and stderr during execution, usually by print statements, logs, warnings, subprocesses, etc.
 *
 * @property {string[]} stdout - List of strings printed to stdout by prints, subprocesses, etc.
 * @property {string[]} stderr - List of strings printed to stderr by prints, subprocesses, etc.
 */
export type Logs = {
  stdout: string[]
    stderr: string[]
}
/**
 * Represents the result of a cell execution.
 * @property {Data} data - List of result of the cell (interactively interpreted last line), display calls, e.g. matplotlib plots.
 * @property {Logs} logs - "Logs printed to stdout and stderr during execution."
 * @property {Error | null} error - An Error object if an error occurred, null otherwise.
 */
export class Result {
  constructor(
    public data: Data[],
    public logs: Logs,
    public error?: Error
  ) {}

  public text(): string | undefined {
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
  public result: Result
  public onStdout?: (out: ProcessMessage) => Promise<void> | void
  public onStderr?: (out: ProcessMessage) => Promise<void> | void
  public inputAccepted: boolean = false

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
  private ws: IWebSocket
  private readonly url: string
  private idAwaiter: {
    [id: string]: (data?: any) => void
  } = {}

  private cells: Cells = {}

  // constructor
  /**
   * Does not start WebSocket connection!
   * You need to call connect() method first.
   */
  public constructor(url: string) {
    this.ws = undefined as any
    this.url = url
  }

  // public
  /**
   * Starts WebSocket connection.
   */
  public connect() {
    this.ws = new IWebSocket(this.url)
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
        result.error = {
          name: message.content.ename,
          value: message.content.evalue,
          tracebackRaw: message.content.traceback
        }
      } else if (message.msg_type == 'stream') {
        if (message.content.name == 'stdout') {
          result.stdout.push(message.content.text)
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
          result.stderr.push(message.content.text)
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
        result.displayData.push(message.content.data)
      } else if (message.msg_type == 'execute_result') {
        result.result = message.content.data
      } else if (message.msg_type == 'status') {
        if (message.content.execution_state == 'idle') {
          if (cell.inputAccepted) {
            this.idAwaiter[parentMsgId](result)
          }
        } else if (message.content.execution_state == 'error') {
          result.error = {
            name: message.content.ename,
            value: message.content.evalue,
            tracebackRaw: message.content.traceback
          }
          this.idAwaiter[parentMsgId](result)
        }
      } else if (message.msg_type == 'execute_reply') {
        if (message.content.status == 'error') {
          result.error = {
            name: message.content.ename,
            value: message.content.evalue,
            tracebackRaw: message.content.traceback
          }
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
      // @ts-ignore
      this.ws.onopen = (e: IWebSocket.OpenEvent) => {
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
  public close() {
    this.ws.close()
  }
}
