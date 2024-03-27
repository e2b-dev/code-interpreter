import { expect, test } from 'vitest'
import { CodeInterpreter } from '../src'

test('create new kernel', async () => {
  const sandbox = await CodeInterpreter.create()

  await sandbox.notebook.createKernel()

  await sandbox.close()
})

test('independence of kernels', async () => {
  const sandbox = await CodeInterpreter.create()
  await sandbox.notebook.execCell('x = 1')
  const kernelID = await sandbox.notebook.createKernel()
  const output = await sandbox.notebook.execCell('x', kernelID)

  expect(output.error!.value).toEqual("name 'x' is not defined")

  await sandbox.close()
})

test('restart kernel', async () => {
  const sandbox = await CodeInterpreter.create()

  await sandbox.notebook.execCell('x = 1')
  await sandbox.notebook.restartKernel()

  const output = await sandbox.notebook.execCell('x')

  expect(output.error!.value).toEqual("name 'x' is not defined")

  await sandbox.close()
})

test('list kernels', async () => {
  const sandbox = await CodeInterpreter.create()

  let kernels = await sandbox.notebook.listKernels()
  expect(kernels.length).toEqual(1)

  const kernelID = await sandbox.notebook.createKernel()
  kernels = await sandbox.notebook.listKernels()
  expect(kernels).toContain(kernelID)
  expect(kernels.length).toEqual(2)

  await sandbox.close()
})
