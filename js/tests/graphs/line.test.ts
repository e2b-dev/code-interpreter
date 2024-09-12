import { expect } from 'vitest'

import { sandboxTest } from '../setup'

sandboxTest('line', async ({ sandbox }) => {
  const code = `
import numpy as np
import matplotlib.pyplot as plt

# Generate x values
x = np.linspace(0, 2*np.pi, 100)

# Calculate y values
y_sin = np.sin(x)
y_cos = np.cos(x)

# Create the plot
plt.figure(figsize=(10, 6))
plt.plot(x, y_sin, label='sin(x)')
plt.plot(x, y_cos, label='cos(x)')

# Add labels and title
plt.xlabel("Time (s)")
plt.ylabel("Amplitude (Hz)")
plt.title('Plot of sin(x) and cos(x)')

# Display the plot
plt.show()
`
  const result = await sandbox.notebook.execCell(code)
  const graph = result.results[0].graph

  expect(graph).toBeDefined()

  expect(graph.title).toBe('Plot of sin(x) and cos(x)')
  expect(graph.x_label).toBe('Time (s)')
  expect(graph.y_label).toBe('Amplitude (Hz)')

  expect(graph.x_unit).toBe('s')
  expect(graph.y_unit).toBe('Hz')

  expect(graph.x_ticks.every((tick: number) => typeof tick === 'number')).toBe(
    true
  )
  expect(graph.y_ticks.every((tick: number) => typeof tick === 'number')).toBe(
    true
  )

  expect(
    graph.y_tick_labels.every((label: string) => typeof label === 'string')
  ).toBe(true)
  expect(
    graph.x_tick_labels.every((label: string) => typeof label === 'string')
  ).toBe(true)

  const lines = graph.elements
  expect(lines.length).toBe(2)

  const [firstLine, secondLine] = lines

  expect(firstLine.label).toBe('sin(x)')
  expect(firstLine.points.length).toBe(100)
  expect(
    firstLine.points.every(
      (point: [number, number]) =>
        typeof point[0] === 'number' && typeof point[1] === 'number'
    )
  ).toBe(true)

  expect(secondLine.label).toBe('cos(x)')
  expect(secondLine.points.length).toBe(100)
  expect(
    secondLine.points.every(
      (point: [number, number]) =>
        typeof point[0] === 'number' && typeof point[1] === 'number'
    )
  ).toBe(true)
})
