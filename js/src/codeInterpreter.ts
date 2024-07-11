import { ConnectionConfig, Sandbox } from 'e2b'

import { Result, Execution, ExecutionError, OutputMessage } from './messaging'

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

export class JupyterExtension {
  private static readonly execTimeoutMs = 300_000

  constructor(private readonly url: string, private readonly connectionConfig: ConnectionConfig) { }

  async execCell(
    code: string,
    opts?: {
      kernelID?: string,
      onStdout?: (output: OutputMessage) => (Promise<any> | any),
      onStderr?: (output: OutputMessage) => (Promise<any> | any),
      onResult?: (data: Result) => (Promise<any> | any),
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

    const res = await fetch(`${this.url}/execute`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        code,
        kernel_id: opts?.kernelID,
      }),
      keepalive: true,
    })

    if (!res.ok || !res.body) {
      throw new Error(`Failed to execute code: ${res.statusText} ${await res?.text()}`)
    }

    clearTimeout(reqTimer)

    const bodyTimeout = opts?.timeoutMs ?? JupyterExtension.execTimeoutMs

    const bodyTimer = bodyTimeout
      ? setTimeout(() => {
        controller.abort()
      }, bodyTimeout)
      : undefined

    const results: Result[] = []
    let stdout: string[] = []
    let stderr: string[] = []
    let error: ExecutionError | undefined = undefined
    let executionCount: number | undefined = undefined

    try {
      for await (const chunk of readLines(res.body)) {
        const msg = JSON.parse(chunk)

        switch (msg.type) {
          case 'result':
            const result = new Result({ ...msg, type: undefined, is_main_result: undefined }, msg.is_main_result)
            results.push(result)
            if (opts?.onResult) {
              await opts.onResult(result)
            }
            break
          case 'stdout':
            stdout.push(msg.text)
            if (opts?.onStdout) {
              await opts.onStdout({
                error: false,
                line: msg.text,
                timestamp: new Date().getTime() * 1000,
              })
            }
            break
          case 'stderr':
            stderr.push(msg.text)
            if (opts?.onStderr) {
              await opts.onStderr({
                error: true,
                line: msg.text,
                timestamp: new Date().getTime() * 1000,
              })
            }
            break
          case 'error':
            error = new ExecutionError(msg.name, msg.value, msg.traceback)
            break
          case 'number_of_executions':
            executionCount = msg.execution_count
            break
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
      executionCount,
    )
  }

  async createKernel({
    cwd,
    kernelName,
    requestTimeoutMs,
  }: {
    cwd?: string,
    kernelName?: string,
    requestTimeoutMs?: number,
  } = {}): Promise<string> {
    const res = await fetch(`${this.url}/contexts`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        kernel_name: kernelName,
        cwd: cwd || '/home/user'
      }),
      keepalive: true,
      signal: this.connectionConfig.getSignal(requestTimeoutMs),
    })

    if (!res.ok || !res.body) {
      throw new Error(`Failed to create kernel: ${res.statusText} ${await res?.text()}`)
    }

    const data = await res.json()
    return data.id
  }

  async restartKernel({
    kernelID,
    requestTimeoutMs,
  }: {
    kernelID?: string,
    requestTimeoutMs?: number,
  } = {}): Promise<void> {
    kernelID = kernelID || 'default'
    const res = await fetch(`${this.url}/contexts/${kernelID}/restart`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      keepalive: true,
      signal: this.connectionConfig.getSignal(requestTimeoutMs),
    })

    if (!res.ok) {
      throw new Error(`Failed to restart kernel: ${res.statusText} ${await res?.text()}`)
    }
  }

  async shutdownKernel({
    kernelID,
    requestTimeoutMs,
  }: {
    kernelID?: string,
    requestTimeoutMs?: number,
  } = {}): Promise<void> {
    kernelID = kernelID || 'default'

    const res = await fetch(`${this.url}/contexts/${kernelID}`, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
      },
      keepalive: true,
      signal: this.connectionConfig.getSignal(requestTimeoutMs),
    })

    if (!res.ok) {
      throw new Error(`Failed to shutdown kernel: ${res.statusText} ${await res?.text()}`)
    }
  }

  async listKernels({
    requestTimeoutMs,
  }: {
    requestTimeoutMs?: number,
  } = {}): Promise<{ kernelID: string, name: string }[]> {
    const res = await fetch(`${this.url}/contexts`, {
      keepalive: true,
      signal: this.connectionConfig.getSignal(requestTimeoutMs),
    })

    if (!res.ok) {
      throw new Error(`Failed to list kernels: ${res.statusText} ${await res?.text()}`)
    }

    return (await res.json()).map((kernel: any) => ({ kernelID: kernel.id, name: kernel.name }))
  }
}

export class CodeInterpreter extends Sandbox {
  protected static override readonly defaultTemplate: string = 'ci-no-ws'
  protected static readonly jupyterPort = 49999

  readonly notebook = new JupyterExtension(
    `${this.connectionConfig.debug ? 'http' : 'https'}://${this.getHost(CodeInterpreter.jupyterPort)}`,
    this.connectionConfig,
  )
}
