import { NotFoundError, SandboxError, TimeoutError } from 'e2b'

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
    public traceback: string
  ) {}
}

/**
 * Converts a non-OK response from the sandbox into a typed error.
 */
export async function extractError(res: Response) {
  if (res.ok) {
    return
  }

  switch (res.status) {
    case 502:
      return new TimeoutError(
        `${await res.text()}: This error is likely due to sandbox timeout. You can modify the sandbox timeout by passing 'timeoutMs' when starting the sandbox or calling '.setTimeout' on the sandbox with the desired timeout.`
      )
    case 404:
      return new NotFoundError(await res.text())
    default:
      return new SandboxError(`${res.status} ${res.statusText}`)
  }
}

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
