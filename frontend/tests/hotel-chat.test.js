import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { test } from 'node:test'
import { createSSRApp } from 'vue'
import { renderToString } from '@vue/server-renderer'
import { parse } from '@vue/compiler-sfc'
import { createHotelChatState, newHotelConversation, restoreHotelConversation, submitHotelQuestion } from '../src/api/hotelChat.js'

const id = '11111111-1111-4111-8111-111111111111'
const answer = {
  conversation_id: id, question: 'Saved hotels in 02108?', state: 'answer', simulated_data: true,
  proposed_sql: 'SELECT hotel_id, name FROM saved_hotels',
  executed_sql: 'SELECT * FROM (SELECT hotel_id, name FROM saved_hotels) AS rag_rows LIMIT 51',
  parameters: ['02108'], retrieved_records: [{ hotel_id: 'fixture-alpha', name: 'Fixture Alpha Hotel' }],
  answer: 'Fixture Alpha Hotel. Rates and rooms are simulated classroom data.', stay_assessments: [],
}

function storage() {
  const values = new Map()
  return { getItem: key => values.get(key), setItem: (key, value) => values.set(key, value),
    removeItem: key => values.delete(key), values }
}

async function renderHotel(state) {
  const { descriptor } = parse(readFileSync(new URL('../src/components/ChatAssistant.vue', import.meta.url), 'utf8'))
  const app = createSSRApp({ template: descriptor.template.content, setup: () => ({
    hotel: state, pretty: value => JSON.stringify(value, null, 2),
    widgetOpen: true, toggleWidget() {}, closeWidget() {},
    question: '', messages: [], pending: false, errorMessage: '',
    askHotelQuestion() {}, newHotelChat() {}, reloadHotelHistory() {}, ask() {}, clearChat() {},
  }) })
  return renderToString(app)
}

test('question submission goes to FastAPI only; pending state disables input and Ask', async t => {
  let resolve
  let observed
  t.mock.method(globalThis, 'fetch', (url, options) => {
    observed = { url, options }
    return new Promise(done => { resolve = done })
  })
  const state = createHotelChatState()
  state.question = answer.question
  const local = storage()
  const pending = submitHotelQuestion(state, 'http://backend', { storage: local })
  assert.equal(state.pending, true)
  assert.equal(state.turns[0].state, 'loading')
  const loading = await renderHotel(state)
  assert.match(loading, /Looking up saved hotel records/)
  assert.match(loading, /<textarea[^>]*disabled/)
  assert.match(loading, /<button[^>]*disabled[^>]*>Asking/)
  assert.equal(observed.url, 'http://backend/api/hotel-chat')
  assert.deepEqual(JSON.parse(observed.options.body), { question: answer.question })
  assert.equal(observed.options.headers.Authorization, undefined)
  resolve(Response.json(answer))
  await pending
  assert.equal(state.pending, false)
  assert.equal(state.conversationId, id)
  assert.equal(state.turns[0].state, 'answer')
  assert.deepEqual([...local.values.values()], [id])
})

test('actual Vue template displays answer, SQL, parameters, records and escaped plain text', async t => {
  t.mock.method(globalThis, 'fetch', async () => Response.json({ ...answer, answer: '<script>unsafe</script> simulated classroom data' }))
  const state = createHotelChatState()
  state.question = answer.question
  await submitHotelQuestion(state, '')
  const html = await renderHotel(state)
  assert.match(html, /RAG Trace/)
  assert.match(html, /Proposed SQL/)
  assert.match(html, /Executed SQL/)
  assert.match(html, /SELECT hotel_id, name/)
  assert.match(html, /02108/)
  assert.match(html, /Fixture Alpha Hotel/)
  assert.match(html, /&lt;script&gt;unsafe/)
  assert.doesNotMatch(html, /<script>unsafe/)
  assert.match(html, /Basic chat — class checkpoint/)
})

for (const stateName of ['no_matches', 'insufficient_data']) {
  test(`${stateName} is shown as a successful distinct state`, async t => {
    t.mock.method(globalThis, 'fetch', async () => Response.json({ ...answer, state: stateName, answer: 'Not enough matching saved evidence.' }))
    const state = createHotelChatState()
    state.question = answer.question
    await submitHotelQuestion(state, '')
    assert.equal(state.turns[0].state, stateName)
    assert.equal(state.error, '')
    const html = await renderHotel(state)
    assert.match(html, stateName === 'no_matches' ? /No matching saved records/ : /Insufficient data/)
  })
}

test('rejected SQL feedback is not presented as no matches or a raw provider error', async t => {
  t.mock.method(globalThis, 'fetch', async () => Response.json({ code: 'rejected_sql', detail: 'raw credential', conversation_id: id }, { status: 422 }))
  const state = createHotelChatState()
  state.question = answer.question
  await submitHotelQuestion(state, '', { storage: storage() })
  assert.equal(state.turns[0].state, 'error')
  const html = await renderHotel(state)
  assert.match(html, /query was rejected/)
  assert.doesNotMatch(html, /raw credential|No matching saved records/)
})

test('refresh restores question, answer and trace from backend using only persisted conversation ID', async t => {
  const local = storage()
  const calls = []
  t.mock.method(globalThis, 'fetch', async (url, options) => {
    calls.push({ url, options })
    if (options.method === 'POST') return Response.json(answer)
    return Response.json({ conversation: { conversation_id: id }, truncated: false, events: [
      { turn_id: 'turn-1', stage: 'user', content: { question: answer.question } },
      { turn_id: 'turn-1', stage: 'assistant', content: answer },
    ] })
  })
  const original = createHotelChatState()
  original.question = answer.question
  await submitHotelQuestion(original, 'http://backend', { storage: local })
  const refreshed = createHotelChatState()
  await restoreHotelConversation(refreshed, 'http://backend', { storage: local })
  assert.equal(calls[1].url, `http://backend/api/hotel-chat/${id}`)
  assert.equal(refreshed.turns[0].answer, answer.answer)
  assert.deepEqual(refreshed.turns[0].trace.retrieved_records, answer.retrieved_records)
  assert.equal(refreshed.conversationId, id)
  newHotelConversation(refreshed, 'http://backend', local)
  assert.equal(refreshed.conversationId, null)
  assert.equal(local.values.size, 0)
})

test('a follow-up submits the saved conversation ID and a failed restore leaves a useful error', async t => {
  const calls = []
  t.mock.method(globalThis, 'fetch', async (url, options) => {
    calls.push({ url, options })
    if (options.method === 'POST') return Response.json(answer)
    return Response.json({ code: 'history_failed' }, { status: 503 })
  })
  const state = createHotelChatState()
  state.conversationId = id
  state.question = answer.question
  await submitHotelQuestion(state, 'http://backend')
  assert.equal(JSON.parse(calls[0].options.body).conversation_id, id)
  await restoreHotelConversation(state, 'http://backend')
  assert.equal(state.restoring, false)
  assert.match(state.error, /history/)
  assert.equal(state.turns.length, 1)
})

test('invalid local question and malformed successful response never become answers', async t => {
  let calls = 0
  t.mock.method(globalThis, 'fetch', async () => { calls++; return Response.json({ answer: 'incomplete' }) })
  const state = createHotelChatState()
  state.question = ' '
  await submitHotelQuestion(state, '')
  assert.equal(calls, 0)
  state.question = answer.question
  await submitHotelQuestion(state, '')
  assert.equal(state.turns[0].state, 'error')
})
