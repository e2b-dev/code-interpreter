import { expect } from 'vitest'

import { sandboxTest } from '../setup'

sandboxTest('supergraph', async ({ sandbox }) => {
  const code = `
import matplotlib.pyplot as plt
import numpy as np

# Data for plotting
x1 = np.linspace(0, 10, 100)
y1 = np.sin(x1)

# Create a figure with multiple subplots
fig, axs = plt.subplots(1, 2, figsize=(10, 8))
fig.suptitle('Multiple Graphs Example', fontsize=16)

# Plotting on the different axes
axs[0].plot(x1, y1, 'r')
axs[0].set_title('Sine Wave')
axs[0].grid(True)

N = 5
x2 = np.random.rand(N)
y2 = np.random.rand(N)

axs[1].scatter(x2, y2, c='blue', label='Dataset 1')
axs[1].set_xlabel('X')
axs[1].set_ylabel('Y')
axs[1].set_title('Scatter Plot')
axs[1].grid(True)

plt.show()
`
  const result = await sandbox.runCode(code)
  const graph = result.results[0].graph

  expect(graph).toBeDefined()
  expect(graph.type).toBe('supergraph')
  expect(graph.title).toBe('Multiple Graphs Example')

  const graphs = graph.elements
  expect(graphs.length).toBe(2)

  const [firstGraph, secondGraph] = graphs

  // Check the first graph (LineGraph)
  expect(firstGraph.title).toBe('Sine Wave')
  expect(firstGraph.type).toBe('line')

  expect(firstGraph.x_label).toBeNull()
  expect(firstGraph.y_label).toBeNull()
  expect(firstGraph.elements.length).toBe(1)
  expect(firstGraph.elements[0].points.length).toBe(100)

  // Check the second graph (ScatterGraph)
  expect(secondGraph.title).toBe('Scatter Plot')
  expect(secondGraph.type).toBe('scatter')

  expect(secondGraph.x_label).toBe('X')
  expect(secondGraph.y_label).toBe('Y')
  expect(secondGraph.elements.length).toBe(1)
  expect(secondGraph.elements[0].points.length).toBe(5)
})
