import { expect } from 'vitest'

import { sandboxTest } from '../setup'

sandboxTest('log', async ({ sandbox }) => {
  const code = `
import numpy as np
import matplotlib.pyplot as plt

# Generate x values
x = np.linspace(0, 100, 100)
# Calculate y values
y = np.exp(x)

# Create the plot
plt.figure(figsize=(10, 6))
plt.plot(x, y, label='y = e^x')

# Set log scale for the y-axis
plt.yscale('log')

# Add labels and title
plt.xlabel('X-axis')
plt.ylabel('Y-axis (log scale)')
plt.title('Graph with Log Scale on Y-axis')

plt.legend()
plt.grid(True)
plt.show()
`

  const result = await sandbox.notebook.execCell(code)
  const graph = result.results[0].graph
  expect(graph).toBeDefined()
  expect(graph.type).toBe('line')

  expect(graph.title).toBe('Graph with Log Scale on Y-axis')

  expect(graph.x_label).toBe('X-axis')
  expect(graph.y_label).toBe('Y-axis (log scale)')

  expect(graph.x_unit).toBeNull()
  expect(graph.y_unit).toBe('log scale')

  expect(graph.x_scale).toBe('linear')
  expect(graph.y_scale).toBe('log')

  expect(graph.x_ticks.every((x) => typeof x === 'number')).toBe(true)
  expect(graph.y_ticks.every((y) => typeof y === 'number')).toBe(true)

  expect(graph.x_tick_labels.every((x) => typeof x === 'string')).toBe(true)
  expect(graph.y_tick_labels.every((y) => typeof y === 'string')).toBe(true)

  const lines = graph.elements
  expect(lines.length).toBe(1)

  const line = lines[0]
  expect(line.label).toBe('y = e^x')
  expect(line.points.length).toBe(100)

  expect(
    line.points.every(
      ([x, y]) => typeof x === 'number' && typeof y === 'number'
    )
  ).toBe(true)
})
