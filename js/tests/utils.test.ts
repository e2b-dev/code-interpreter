import { expect, test } from 'vitest'

import { readLines } from '../src/utils'

function streamFromChunks(chunks: Uint8Array[]): ReadableStream<Uint8Array> {
  return new ReadableStream<Uint8Array>({
    start(controller) {
      for (const chunk of chunks) {
        controller.enqueue(chunk)
      }
      controller.close()
    },
  })
}

function encodeChunks(chunks: string[]): Uint8Array[] {
  const encoder = new TextEncoder()
  return chunks.map((chunk) => encoder.encode(chunk))
}

async function collect(stream: ReadableStream<Uint8Array>): Promise<string[]> {
  const lines: string[] = []
  for await (const line of readLines(stream)) {
    lines.push(line)
  }
  return lines
}

test('yields lines split across a single chunk', async () => {
  const lines = await collect(streamFromChunks(encodeChunks(['a\nb\nc\n'])))
  expect(lines).toEqual(['a', 'b', 'c'])
})

test('yields trailing text without a final newline', async () => {
  const lines = await collect(streamFromChunks(encodeChunks(['a\nb'])))
  expect(lines).toEqual(['a', 'b'])
})

test('handles a line spanning multiple chunks', async () => {
  const lines = await collect(
    streamFromChunks(encodeChunks(['first pa', 'rt', ' of line\nsecond\n']))
  )
  expect(lines).toEqual(['first part of line', 'second'])
})

test('handles empty lines', async () => {
  const lines = await collect(streamFromChunks(encodeChunks(['a\n\nb\n'])))
  expect(lines).toEqual(['a', '', 'b'])
})

test('handles chunk boundaries around newlines', async () => {
  const lines = await collect(
    streamFromChunks(encodeChunks(['a', '\n', 'b\n', 'c']))
  )
  expect(lines).toEqual(['a', 'b', 'c'])
})

test('yields nothing for an empty stream', async () => {
  const lines = await collect(streamFromChunks([]))
  expect(lines).toEqual([])
})

test('decodes multi-byte UTF-8 characters split across chunks', async () => {
  // '🚀' is 4 bytes in UTF-8, so split it in the middle of the sequence
  const bytes = new TextEncoder().encode('before 🚀 after\n')
  const splitAt = bytes.indexOf(0xf0) + 2
  const lines = await collect(
    streamFromChunks([bytes.slice(0, splitAt), bytes.slice(splitAt)])
  )
  expect(lines).toEqual(['before 🚀 after'])
})

test('decodes an incomplete multi-byte sequence at stream end', async () => {
  // Stream ends mid-🚀: the decoder should flush a replacement character
  // instead of silently dropping the bytes
  const bytes = new TextEncoder().encode('abc🚀')
  const lines = await collect(
    streamFromChunks([bytes.slice(0, bytes.length - 2)])
  )
  expect(lines).toHaveLength(1)
  expect(lines[0].startsWith('abc')).toBe(true)
})

test('handles large single-line output split into many chunks', async () => {
  // A ~8 MB line delivered in 64 KiB chunks must complete without quadratic
  // buffer rebuilds (this test hangs for minutes with `buffer += chunk`)
  const chunkSize = 64 * 1024
  const chunkCount = 128
  const chunk = 'x'.repeat(chunkSize)
  const chunks = encodeChunks([
    ...Array.from({ length: chunkCount }, () => chunk),
    '\ntail\n',
  ])
  const lines = await collect(streamFromChunks(chunks))
  expect(lines).toEqual(['x'.repeat(chunkSize * chunkCount), 'tail'])
})
