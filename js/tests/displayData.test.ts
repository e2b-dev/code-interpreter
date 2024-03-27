import { CodeInterpreter } from '../src'

import { expect, test } from 'vitest'

test('display data', async () => {
  const sandbox = await CodeInterpreter.create()

  // plot random graph
  const result = await sandbox.notebook.execCell(`
        import matplotlib.pyplot as plt
        import numpy as np

        x = np.linspace(0, 20, 100)
        y = np.sin(x)

        plt.plot(x, y)
        plt.show()
        `)

  // there's your image
  const image = result.displayData[0]
  expect(image['image/png']).toBeDefined()
  expect(image['text/plain']).toBeDefined()

  await sandbox.close()
})
