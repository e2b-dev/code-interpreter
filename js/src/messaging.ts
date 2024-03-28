import IWebSocket from 'isomorphic-ws'
import { ProcessMessage } from 'e2b'
import { randomBytes } from 'crypto'

export interface Error {
  name: string
  value: string
  traceback: string[]
}

export type MIMEType = string

/**
 * Represents the data to be displayed as a result of executing a cell in a Jupyter notebook.
 * This interface maps MIME types to their corresponding string representations of the data.
 * MIME types are used to specify the nature and format of the data, allowing for the representation
 * of various types of content such as text, images, and more. Each key in the interface is a MIME type
 * string, and its value is the data associated with that MIME type, formatted as a string.
 */
export interface DisplayData {
  [key: MIMEType]: string
}

/**
 * Represents the result of a cell execution.
 * @property {DisplayData} result - Result of the last line executed interactively. It's a dictionary containing MIME type as key and data as value. The string representation of the result is stored under the key 'text/plain'.
 * @property {DisplayData[]} displayData - List of display calls, e.g., matplotlib plots. Each element is a dictionary containing MIME type as key and data as value.
 * @property {string[]} stdout - List of strings printed to stdout by prints, subprocesses, etc.
 * @property {string[]} stderr - List of strings printed to stderr by prints, subprocesses, etc.
 * @property {Error | null} error - An Error object if an error occurred, null otherwise.
 */
export interface Cell {
  result: DisplayData
  displayData: DisplayData[]
  stdout: string[]
  stderr: string[]
  error?: Error
}

/**
 * Represents the execution of a cell in the Jupyter kernel.
 * It's an internal class used by JupyterKernelWebSocket.
 */
class CellExecution {
  public result: Cell
  public onStdout?: (out: ProcessMessage) => Promise<void> | void
  public onStderr?: (out: ProcessMessage) => Promise<void> | void
  public inputAccepted: boolean = false

  constructor(
    onStdout?: (out: ProcessMessage) => Promise<void> | void,
    onStderr?: (out: ProcessMessage) => Promise<void> | void
  ) {
    this.result = {
      stdout: [],
      stderr: [],
      displayData: [],
      result: {}
    }
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
          traceback: message.content.traceback
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
            traceback: message.content.traceback
          }
          this.idAwaiter[parentMsgId](result)
        }
      } else if (message.msg_type == 'execute_reply') {
        if (message.content.status == 'error') {
          result.error = {
            name: message.content.ename,
            value: message.content.evalue,
            traceback: message.content.traceback
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
    return new Promise<Cell>((resolve, reject) => {
      const msg_id = randomBytes(16).toString('hex')
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
      this.idAwaiter[msg_id] = (responseData: Cell) => {
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
    const session = randomBytes(16).toString('hex')
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
