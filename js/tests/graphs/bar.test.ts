import { expect } from 'vitest'

import { sandboxTest } from '../setup'

// Skip this test if we are running in debug mode — the pwd and user in the testing docker container are not the same as in the actual sandbox.
sandboxTest('bar', async ({ sandbox }) => {
  const code = `
import matplotlib.pyplot as plt

# Prepare data
authors = ['Author A', 'Author B', 'Author C', 'Author D']
sales = [100, 200, 300, 400]

# Create and customize the bar graph
plt.figure(figsize=(10, 6))
plt.bar(authors, sales, label='Books Sold', color='blue')
plt.xlabel('Authors')
plt.ylabel('Number of Books Sold')
plt.title('Book Sales by Authors')

# Display the graph
plt.tight_layout()
plt.show()
`
  const result = await sandbox.runCode(code)
  const graph = result.results[0].graph

  expect(graph).toBeDefined()
  expect(graph.type).toBe('bar')
  expect(graph.title).toBe('Book Sales by Authors')

  expect(graph.x_label).toBe('Authors')
  expect(graph.y_label).toBe('Number of Books Sold')

  expect(graph.x_unit).toBeNull()
  expect(graph.y_unit).toBeNull()

  const bars = graph.elements
  expect(bars.length).toBe(4)

  expect(bars.map((bar) => bar.value)).toEqual([100, 200, 300, 400])
  expect(bars.map((bar) => bar.group)).toEqual([
    'Books Sold',
    'Books Sold',
    'Books Sold',
    'Books Sold',
  ])
  expect(bars.map((bar) => bar.label)).toEqual([
    'Author A',
    'Author B',
    'Author C',
    'Author D',
  ])
})
