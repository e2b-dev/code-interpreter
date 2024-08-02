import { expect } from 'vitest'

import { isDebug, sandboxTest } from './setup'

sandboxTest('create new kernel', async ({ sandbox }) => {
  await sandbox.notebook.createKernel()
})

sandboxTest('independence of kernels', async ({ sandbox }) => {
  await sandbox.notebook.execCell('x = 1')
  const kernelID = await sandbox.notebook.createKernel()
  const output = await sandbox.notebook.execCell('x', { kernelID })

  expect(output.error!.value).toEqual("name 'x' is not defined")
})

sandboxTest('restart kernel', async ({ sandbox }) => {
  await sandbox.notebook.execCell('x = 1')
  await sandbox.notebook.restartKernel()

  const output = await sandbox.notebook.execCell('x')

  expect(output.error!.value).toEqual("name 'x' is not defined")
})

// Skip this test if we are running in debug mode — we don't know how many kernels are in the local debug testing container.
sandboxTest.skipIf(isDebug)('list kernels', async ({ sandbox }) => {
  let kernels = await sandbox.notebook.listKernels()
  expect(kernels.length).toEqual(1)

  const kernelID = await sandbox.notebook.createKernel()
  kernels = await sandbox.notebook.listKernels()
  expect(kernels.map(kernel => kernel.kernelID)).toContain(kernelID)
  expect(kernels.length).toEqual(2)
})

// Skip this test if we are running in debug mode — we don't know how many kernels are in the local debug testing container.
sandboxTest.skipIf(isDebug)('shutdown kernel', async ({ sandbox }) => {
  let kernels = await sandbox.notebook.listKernels()
  expect(kernels.length).toEqual(1)

  const kernelID = await sandbox.notebook.shutdownKernel()
  kernels = await sandbox.notebook.listKernels()
  expect(kernels).not.toContain(kernelID)
  expect(kernels.length).toEqual(0)
})
