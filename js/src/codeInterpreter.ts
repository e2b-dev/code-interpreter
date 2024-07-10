import { ConnectionConfig, Sandbox } from 'e2b'

import { Result, Execution, ExecutionError } from './messaging'

async function* readLines(stream: ReadableStream<Uint8Array>) {
  const reader = stream.getReader();
  let buffer = ''

  try {
    while (true) {
      const { done, value } = await reader.read();

      if (done) {
        yield buffer
        break
      }

      buffer += new TextDecoder().decode(value)
      const newlineIdx = buffer.indexOf('\n')
      if (newlineIdx !== -1) {
        yield buffer.slice(0, newlineIdx)
        buffer = buffer.slice(newlineIdx + 1)
      }
    }
  } finally {
    reader.releaseLock()
  }
}

export class JupyterExtension {
  private static readonly defaultTimeoutMs = 300_000

  constructor(private readonly url: string, private readonly connectionConfig: ConnectionConfig) { }

  async execCell(
    code: string,
    opts: {
      kernelID?: string,
      language?: string,
      onStdout?: (output: string) => (Promise<void> | void),
      onStderr?: (output: string) => (Promise<void> | void),
      onResult?: (data: Result) => (Promise<void> | void),
      timeoutMs?: number,
      requestTimeoutMs?: number,
    } = {}
  ): Promise<Execution> {
    const controller = new AbortController()

    const requestTimeout = opts?.requestTimeoutMs ?? this.connectionConfig.requestTimeoutMs

    const reqTimer = requestTimeout ? setTimeout(() => {
      controller.abort()
    }, requestTimeout)
      : undefined

    const res = await fetch(`${this.url}/execute`, {
      method: 'POST',
      body: JSON.stringify({
        code,
        // language: opts.language,
        // kernel_id: opts.kernelID,
      }),
      keepalive: true,
    })

    if (!res.ok || !res.body) {
      throw new Error(`Failed to execute code: ${res.statusText}`)
    }

    clearTimeout(reqTimer)

    const bodyTimeout = opts.timeoutMs ?? JupyterExtension.defaultTimeoutMs

    const bodyTimer = bodyTimeout
      ? setTimeout(() => {
        controller.abort()
      }, bodyTimeout)
      : undefined

    const results: Result[] = []
    let stdout: string[] = []
    let stderr: string[] = []
    let error: ExecutionError | undefined = undefined

    try {

      for await (const chunk of readLines(res.body)) {
        const msg = JSON.parse(chunk)

        switch (msg.type) {
          case 'result':
            const result = new Result(msg.data, true)
            results.push(result)
            if (opts.onResult) {
              await opts.onResult(result)
            }
            break
          case 'stdout':
            stdout.push(msg.value)
            if (opts.onStdout) {
              await opts.onStdout(msg.value)
            }
            break
          case 'stderr':
            stderr.push(msg.value)
            if (opts.onStderr) {
              await opts.onStderr(msg.value)
            }
            break
          case 'error':
            error = new ExecutionError(msg.name, msg.value, msg.traceback)
            break
          default:
            console.warn(`Unhandled message type: ${msg.type}`)
        }
      }
    } finally {
      clearTimeout(bodyTimer)
    }

    return new Execution(
      results,
      {
        stdout,
        stderr,
      },
      error,
    )
  }
}

export class CodeInterpreter extends Sandbox {
  protected static override readonly defaultTemplate: string = 'ci-no-ws'
  protected static readonly jupyterPort = 8000

  readonly notebook = new JupyterExtension(
    `${this.connectionConfig.debug ? 'http' : 'https'}://${this.getHost(CodeInterpreter.jupyterPort)}`,
    this.connectionConfig,
  )
}
