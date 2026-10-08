import assert from 'node:assert/strict'
import { test } from 'node:test'
import { streamChat } from '../src/api/chat.js'

const messages = [{ role: 'user', content: 'Hello' }]
const encoder = new TextEncoder()
function mockStream(t, parts, status = 200) {
  const requests = []
  t.mock.method(globalThis, 'fetch', async (url, options) => {
    requests.push({ url, options })
    return new Response(new ReadableStream({
      start(controller) {
        for (const part of parts) controller.enqueue(encoder.encode(part))
        controller.close()
      },
    }), { status })
  })
  return requests
}

test('chat calls only our backend and handles split/coalesced events with plain text', async t => {
  const calls = mockStream(t, ['{"type":"del', 'ta","text":"Hello <b>"}\n{"type":"delta","text":"世界"}\n', '{"type":"done"}\n'])
  let answer = ''
  await streamChat('http://backend', messages, { onDelta: text => { answer += text } })
  assert.equal(answer, 'Hello <b>世界')
  assert.equal(calls[0].url, 'http://backend/api/chat')
  assert.equal(calls[0].options.method, 'POST')
  assert.deepEqual(JSON.parse(calls[0].options.body), { messages })
  assert.equal(calls[0].options.headers.Authorization, undefined)
})

test('safe backend stream errors are preserved', async t => {
  mockStream(t, ['{"type":"error","code":"limited","message":"raw secret"}\n'])
  await assert.rejects(streamChat('', messages, { onDelta() {} }), error => error.code === 'limited' && !error.message.includes('secret'))
})

test('an interrupted reply does not complete successfully', async t => {
  mockStream(t, ['{"type":"delta","text":"Partial"}\n'])
  await assert.rejects(streamChat('', messages, { onDelta() {} }), error => error.code === 'incomplete')
})

test('an empty completion is rejected', async t => {
  mockStream(t, ['{"type":"done"}\n'])
  await assert.rejects(streamChat('', messages, { onDelta() {} }), error => error.code === 'unavailable')
})

test('malformed stream content is not shown as a raw error', async t => {
  mockStream(t, ['raw secret\n'])
  await assert.rejects(streamChat('', messages, { onDelta() {} }), error => error.code === 'unavailable')
})

test('missing configuration has useful feedback without using the response body', async t => {
  mockStream(t, ['raw secret'], 503)
  await assert.rejects(streamChat('', messages, { onDelta() {} }), error => error.code === 'configuration')
})

test('network and cancellation failures are safe', async t => {
  t.mock.method(globalThis, 'fetch', async () => { throw new DOMException('raw secret', 'AbortError') })
  await assert.rejects(streamChat('', messages, { onDelta() {} }), error => error.code === 'timeout')
})
