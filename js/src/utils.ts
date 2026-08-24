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

const CONNECTION_CLOSED_CODES = ['ECONNRESET', 'EPIPE', 'UND_ERR_SOCKET']

/**
 * Checks if the error means the connection was closed/reset while the request
 * was in flight. The shape of this error is runtime-specific — Bun and Deno
 * set a `code` directly, while Node's fetch (undici) wraps the socket error
 * in the `cause` of a generic `TypeError`.
 */
export function isConnectionClosedError(error: unknown): boolean {
  if (!(error instanceof Error)) {
    return false
  }

  const code = (error as { code?: unknown }).code
  if (typeof code === 'string' && CONNECTION_CLOSED_CODES.includes(code)) {
    return true
  }

  if (error.name === 'ConnectionReset' || error.name === 'ConnectionClosed') {
    return true
  }

  if (error.cause) {
    return isConnectionClosedError(error.cause)
  }

  return false
}

export async function* readLines(stream: ReadableStream<Uint8Array>) {
  const reader = stream.getReader()
  const decoder = new TextDecoder()
  // Text accumulated since the last newline, kept as an array of fragments:
  // appending is O(1), so total work stays linear even when a single line
  // spans many chunks (growing a string with `buffer += chunk` re-copies the
  // whole buffer on every chunk, which is O(n²) and can OOM on large stdout).
  const pending: string[] = []

  try {
    while (true) {
      const { done, value } = await reader.read()

      if (value !== undefined) {
        // { stream: true } keeps multi-byte UTF-8 sequences split across
        // chunk boundaries intact instead of decoding them as U+FFFD.
        const chunk = decoder.decode(value, { stream: true })
        let newlineIdx = chunk.indexOf('\n')

        if (newlineIdx === -1) {
          if (chunk.length > 0) {
            pending.push(chunk)
          }
        } else {
          pending.push(chunk.slice(0, newlineIdx))
          yield pending.join('')
          pending.length = 0

          let start = newlineIdx + 1
          while ((newlineIdx = chunk.indexOf('\n', start)) !== -1) {
            yield chunk.slice(start, newlineIdx)
            start = newlineIdx + 1
          }

          if (start < chunk.length) {
            pending.push(chunk.slice(start))
          }
        }
      }

      if (done) {
        const trailing = decoder.decode()
        if (trailing) {
          pending.push(trailing)
        }
        if (pending.length > 0) {
          yield pending.join('')
        }
        break
      }
    }
  } finally {
    reader.releaseLock()
  }
}
