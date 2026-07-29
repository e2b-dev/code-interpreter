import { expect } from 'vitest'
import { isDebug, sandboxTest, wait } from './setup'

async function waitForHealth(sandbox: any, maxRetries = 10, intervalMs = 100) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      const result = await sandbox.commands.run(
        'curl -s -o /dev/null -w "%{http_code}" http://0.0.0.0:49999/health'
      )
      if (result.stdout.trim() === '200') {
        return true
      }
    } catch {
      // Connection refused or other error, retry
    }
    await wait(intervalMs)
  }
  return false
}

// Recovery has to be judged by running code, not by /health. Killing Jupyter
// leaves the code-interpreter server up but holding dead kernel handles, so it
// answers /health for a few seconds before the process manager recycles it —
// long enough for a health check to pass against a sandbox that cannot execute.
async function waitForWorkingSandbox(
  sandbox: any,
  maxRetries = 60,
  intervalMs = 500
) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      const result = await sandbox.runCode('x = 1; x')
      if (result.text === '1') {
        return true
      }
    } catch {
      // Still restarting, retry
    }
    await wait(intervalMs)
  }
  return false
}

sandboxTest.skipIf(isDebug)(
  'restart after jupyter kill',
  async ({ sandbox }) => {
    // Verify health is up initially
    const initialHealth = await waitForHealth(sandbox)
    expect(initialHealth).toBe(true)

    // Kill the jupyter process as root. The pattern is bracketed so it cannot
    // match the shell running it — `pgrep -f 'jupyter server'` matched its own
    // command line, so this only ever killed itself. pkill exits non-zero when
    // nothing matched, which fails the test rather than passing it vacuously.
    await sandbox.commands.run("pkill -9 -f '[j]upyter-server'", {
      user: 'root',
    })

    // Wait for process-compose to restart both processes
    const recovered = await waitForWorkingSandbox(sandbox)
    expect(recovered).toBe(true)
  }
)

sandboxTest.skipIf(isDebug)(
  'restart after code-interpreter kill',
  async ({ sandbox }) => {
    // Verify health is up initially
    const initialHealth = await waitForHealth(sandbox)
    expect(initialHealth).toBe(true)

    // Kill the code-interpreter process as root
    await sandbox.commands.run("pkill -9 -f '[u]vicorn main:app'", {
      user: 'root',
    })

    // Wait for process-compose to restart it
    const recovered = await waitForWorkingSandbox(sandbox)
    expect(recovered).toBe(true)
  }
)
