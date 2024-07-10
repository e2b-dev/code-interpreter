/**
 * A message from a process.
 */
export class CellMessage {
  constructor(
    public readonly line: string,
    /**
     * Unix epoch in nanoseconds
     */
    public readonly timestamp: number,
    public readonly error: boolean,
  ) {
  }

  public toString() {
    return this.line
  }
}


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
    public error?: ExecutionError,
    /**
     * Execution count of the cell.
     */
    public executionCount?: number
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
  onStdout?: (out: CellMessage) => any
  onStderr?: (out: CellMessage) => any
  onResult?: (data: Result) => any
  inputAccepted: boolean = false

  constructor(
    onStdout?: (out: CellMessage) => any,
    onStderr?: (out: CellMessage) => any,
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
