import { expect } from 'vitest'

import { sandboxTest } from '../setup'

sandboxTest('box-and-whisker', async ({ sandbox }) => {
  const code = `
import matplotlib.pyplot as plt
import numpy as np

# Sample data
data = {
    'Class A': [85, 90, 78, 92, 88],
    'Class B': [95, 89, 76, 91, 84, 87],
    'Class C': [75, 82, 88, 79, 86]
}

# Create figure and axis
fig, ax = plt.subplots(figsize=(10, 6))

# Plot box plot
ax.boxplot(data.values(), labels=data.keys())

# Customize plot
ax.set_title('Exam Scores Distribution')
ax.set_xlabel('Class')
ax.set_ylabel('Score')

# Set custom colors
ax.boxplot(data.values(), labels=data.keys(), patch_artist=True)

# Add legend
ax.legend()

# Adjust layout and show plot
plt.tight_layout()
plt.show()
`
  const result = await sandbox.notebook.execCell(code)
  const graph = result.results[0].graph

  expect(graph).toBeDefined()

  expect(graph.type).toBe('box_and_whisker')
  expect(graph.title).toBe('Exam Scores Distribution')

  expect(graph.x_label).toBe('Class')
  expect(graph.y_label).toBe('Score')

  expect(graph.x_unit).toBeNull()
  expect(graph.y_unit).toBeNull()

  const bars = graph.elements
  expect(bars.length).toBe(3)

  bars.forEach((bar: any) => {
    expect(typeof bar.min).toBe('number')
    expect(typeof bar.first_quartile).toBe('number')
    expect(typeof bar.median).toBe('number')
    expect(typeof bar.third_quartile).toBe('number')
    expect(typeof bar.max).toBe('number')
    expect(typeof bar.label).toBe('string')
  })
})
