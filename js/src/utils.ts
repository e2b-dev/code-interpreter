import { TimeoutError } from 'e2b'

export function formatRequestTimeoutError(error: unknown) {
  if (error instanceof Error && error.name === 'AbortError') {
    return new TimeoutError(
      "Request timed out — the 'requestTimeoutMs' option can be used to increase this timeout"
    )
  }

  return error
}

export function formatExecutionTimeoutError(error: unknown) {
  if (error instanceof Error && error.name === 'AbortError') {
    return new TimeoutError(
      "Execution timed out — the 'timeoutMs' option can be used to increase this timeout"
    )
  }

  return error
}

export async function* readLines(stream: ReadableStream<Uint8Array>) {
  const reader = stream.getReader()
  const decoder = new TextDecoder()
  const pending: string[] = []

  try {
    while (true) {
      const { done, value } = await reader.read()

      if (done) {
        if (pending.length > 0) {
          yield pending.join('')
        }
        break
      }

      if (value !== undefined) {
        const chunk = decoder.decode(value, { stream: true })

        if (chunk.indexOf('\n') === -1) {
          // No newline — accumulate in O(1)
          pending.push(chunk)
          continue
        }

        // Chunk contains newline(s) — split and yield complete lines
        const parts = chunk.split('\n')

        // First part completes the pending line
        pending.push(parts[0])
        yield pending.join('')
        pending.length = 0

        // Middle parts are already complete lines
        for (let i = 1; i < parts.length - 1; i++) {
          yield parts[i]
        }

        // Last part starts a new pending line (may be empty)
        const last = parts[parts.length - 1]
        if (last.length > 0) {
          pending.push(last)
        }
      }
    }
  } finally {
    reader.releaseLock()
  }
}
