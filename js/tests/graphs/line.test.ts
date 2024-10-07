import { expect } from 'vitest'

import { sandboxTest } from '../setup'

sandboxTest('line', async ({ sandbox }) => {
  const code = `
import numpy as np
import matplotlib.pyplot as plt
import datetime

# Generate x values
dates = [datetime.date(2023, 9, 1) + datetime.timedelta(seconds=i) for i in range(100)]

x = np.linspace(0, 2*np.pi, 100)
# Calculate y values
y_sin = np.sin(x)
y_cos = np.cos(x)

# Create the plot
plt.figure(figsize=(10, 6))
plt.plot(dates, y_sin, label='sin(x)')
plt.plot(dates, y_cos, label='cos(x)')

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
  expect(graph.type).toBe('line')

  expect(graph.title).toBe('Plot of sin(x) and cos(x)')
  expect(graph.x_label).toBe('Time (s)')
  expect(graph.y_label).toBe('Amplitude (Hz)')

  expect(graph.x_unit).toBe('s')
  expect(graph.y_unit).toBe('Hz')

  expect(graph.x_ticks.every((tick: number) => typeof tick === 'string')).toBe(
    true,
  )
  expect(new Date(graph.x_ticks[0])).toBeInstanceOf(Date)
  expect(graph.y_ticks.every((tick: number) => typeof tick === 'number')).toBe(
    true,
  )

  expect(
    graph.y_tick_labels.every((label: string) => typeof label === 'string'),
  ).toBe(true)
  expect(
    graph.x_tick_labels.every((label: string) => typeof label === 'string'),
  ).toBe(true)

  const lines = graph.elements
  expect(lines.length).toBe(2)

  const [firstLine, secondLine] = lines

  expect(firstLine.label).toBe('sin(x)')
  expect(firstLine.points.length).toBe(100)
  expect(
    firstLine.points.every(
      (point: [number, number]) =>
        typeof point[0] === 'string' && typeof point[1] === 'number',
    ),
  ).toBe(true)
  expect(new Date(firstLine.points[0][0])).toEqual(
    new Date('2023-09-01T00:00:00.000Z'),
  )

  expect(secondLine.label).toBe('cos(x)')
  expect(secondLine.points.length).toBe(100)
  expect(
    secondLine.points.every(
      (point: [number, number]) =>
        typeof point[0] === 'string' && typeof point[1] === 'number',
    ),
  ).toBe(true)
})
