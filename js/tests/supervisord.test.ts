import { expect } from 'vitest'
import { sandboxTest, wait } from './setup'

async function waitForHealth(sandbox: any, maxRetries = 10, intervalMs = 100) {
  for (let i = 0; i < maxRetries; i++) {
    const result = await sandbox.commands.run(
      'curl -s -o /dev/null -w "%{http_code}" http://0.0.0.0:49999/health'
    )
    if (result.stdout.trim() === '200') {
      return true
    }
    await wait(intervalMs)
  }
  return false
}

sandboxTest('restart after jupyter kill', async ({ sandbox }) => {
  // Verify health is up initially
  const initialHealth = await waitForHealth(sandbox)
  expect(initialHealth).toBe(true)

  // Kill the jupyter process as root
  await sandbox.commands.run("kill -9 $(pgrep -f 'jupyter server')", {
    user: 'root',
  })

  // Wait for supervisord to restart it and health to come back
  const recovered = await waitForHealth(sandbox, 10, 100)
  expect(recovered).toBe(true)

  // Verify code execution works after recovery
  const result = await sandbox.runCode('x = 1; x')
  expect(result.text).toEqual('1')
})

sandboxTest('restart after code-interpreter kill', async ({ sandbox }) => {
  // Verify health is up initially
  const initialHealth = await waitForHealth(sandbox)
  expect(initialHealth).toBe(true)

  // Kill the code-interpreter process as root
  await sandbox.commands.run('kill -9 $(cat /var/run/code-interpreter.pid)', {
    user: 'root',
  })

  // Wait for supervisord to restart it and health to come back
  const recovered = await waitForHealth(sandbox, 10, 100)
  expect(recovered).toBe(true)

  // Verify code execution works after recovery
  const result = await sandbox.runCode('x = 1; x')
  expect(result.text).toEqual('1')
})
