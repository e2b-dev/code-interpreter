import { ProcessMessage } from 'e2b'
import { CodeInterpreter, Result } from '../src'

import { expect, test } from 'vitest'

test('streaming output', async () => {
  const out: ProcessMessage[] = []
  const sandbox = await CodeInterpreter.create()
  await sandbox.notebook.execCell('print(1)', {
    onStdout: (msg) => out.push(msg)
  })

  expect(out.length).toEqual(1)
  expect(out[0].line).toEqual('1\n')
  await sandbox.close()
})

test('streaming error', async () => {
  const out: ProcessMessage[] = []
  const sandbox = await CodeInterpreter.create()
  await sandbox.notebook.execCell('import sys;print(1, file=sys.stderr)', {
    onStderr: (msg) => out.push(msg)
  })

  expect(out.length).toEqual(1)
  expect(out[0].line).toEqual('1\n')
  await sandbox.close()
})

test('streaming result', async () => {
  const out: Result[] = []
  const sandbox = await CodeInterpreter.create()
  const code = `
        import matplotlib.pyplot as plt
        import numpy as np
    
        x = np.linspace(0, 20, 100)
        y = np.sin(x)
    
        plt.plot(x, y)
        plt.show()
        
        x
        `
  await sandbox.notebook.execCell(code, {
    onResult: (result) => out.push(result)
  })

  expect(out.length).toEqual(2)
  await sandbox.close()
})
