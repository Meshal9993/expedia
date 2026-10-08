// Hotel questions and trace history use our backend only. Storage keeps an ID, not messages or keys.
const validId = value => typeof value === 'string' && /^[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}$/i.test(value)
const errors = {
  invalid: 'Enter a hotel question of at most 4,000 characters.',
  configuration: 'The hotel assistant is not configured. Check the backend settings.',
  limited: 'The model is temporarily limited or its quota has been reached.',
  timeout: 'The request took too long. Please try again.',
  unavailable: 'The model request failed. Please try again.',
  model_invalid: 'The model answer could not be verified against the retrieved hotels.',
  rejected_sql: 'The proposed query was rejected. No hotel answer can be inferred from it.',
  retrieval_failed: 'The local hotel query could not complete. Please try again.',
  history_failed: 'Conversation history could not be saved or loaded.',
  conversation_not_found: 'This saved conversation was not found. Start a new conversation.',
}

export class HotelChatError extends Error {
  constructor(code = 'unavailable', conversationId = null) {
    super(errors[code] || errors.unavailable)
    this.code = Object.hasOwn(errors, code) ? code : 'unavailable'
    this.conversationId = validId(conversationId) ? conversationId : null
  }
}

async function jsonRequest(url, options) {
  try {
    const response = await fetch(url, options)
    const body = await response.json()
    if (!response.ok) throw new HotelChatError(body.code || (response.status === 422 ? 'invalid' : 'unavailable'), body.conversation_id)
    return body
  } catch (error) {
    if (error instanceof HotelChatError) throw error
    throw new HotelChatError(error.name === 'AbortError' ? 'timeout' : 'unavailable')
  }
}

export async function askHotel(apiBaseUrl, question, conversationId, signal) {
  const payload = { question }
  if (conversationId) payload.conversation_id = conversationId
  const result = await jsonRequest(`${apiBaseUrl}/api/hotel-chat`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload), signal,
  })
  if (!validId(result.conversation_id) || result.question !== question
      || !['answer', 'no_matches', 'insufficient_data'].includes(result.state)
      || !result.answer || typeof result.answer !== 'string'
      || typeof result.proposed_sql !== 'string' || typeof result.executed_sql !== 'string'
      || !Array.isArray(result.parameters) || !Array.isArray(result.retrieved_records)
      || result.simulated_data !== true) throw new HotelChatError()
  return result
}

export function createHotelChatState() {
  return { question: '', conversationId: null, turns: [], pending: false, restoring: false,
    error: '', historyTruncated: false, storageWarning: '' }
}

const storageKey = apiBaseUrl => `expedia.hotelChatConversation.${apiBaseUrl}`

function remember(state, apiBaseUrl, storage) {
  try { storage?.setItem(storageKey(apiBaseUrl), state.conversationId) }
  catch { state.storageWarning = 'Browser storage is unavailable. Keep the conversation ID to find its saved backend history.' }
}

export async function submitHotelQuestion(state, apiBaseUrl, { storage, signal } = {}) {
  if (state.pending || state.restoring) return
  const question = state.question.trim()
  if (!question || question.length > 4000) {
    state.error = errors.invalid
    return
  }
  const turn = { question, state: 'loading', answer: '', trace: null, error: '' }
  state.turns.push(turn)
  state.question = ''
  state.error = ''
  state.pending = true
  try {
    const result = await askHotel(apiBaseUrl, question, state.conversationId, signal)
    state.conversationId = result.conversation_id
    remember(state, apiBaseUrl, storage)
    Object.assign(turn, { answer: result.answer, trace: result, state: result.state })
  } catch (error) {
    if (error.conversationId) {
      state.conversationId = error.conversationId
      remember(state, apiBaseUrl, storage)
    }
    turn.state = 'error'
    turn.error = error.message
    state.error = error.message
  } finally {
    state.pending = false
  }
}

export async function restoreHotelConversation(state, apiBaseUrl, { storage, signal } = {}) {
  if (state.pending || state.restoring) return
  try {
    const id = state.conversationId || storage?.getItem(storageKey(apiBaseUrl))
    if (!validId(id)) return
    state.conversationId = id
    state.restoring = true
    state.error = ''
    const history = await jsonRequest(`${apiBaseUrl}/api/hotel-chat/${encodeURIComponent(id)}`, { signal, cache: 'no-store' })
    if (history.conversation?.conversation_id !== id || !Array.isArray(history.events)) throw new HotelChatError('history_failed')
    const turns = new Map()
    for (const event of history.events) {
      if (!event.turn_id || !event.content || typeof event.content !== 'object') throw new HotelChatError('history_failed')
      let turn = turns.get(event.turn_id)
      if (!turn) {
        turn = { question: '', state: 'incomplete', answer: '', trace: {
          proposed_sql: '', executed_sql: '', parameters: [], retrieved_records: [], stay_assessments: [],
        }, error: '' }
        turns.set(event.turn_id, turn)
      }
      if (event.stage === 'user') turn.question = event.content.question
      if (event.stage === 'proposed_sql') Object.assign(turn.trace, { proposed_sql: event.content.sql, parameters: event.content.parameters })
      if (event.stage === 'executed_sql') turn.trace.executed_sql = event.content.sql
      if (event.stage === 'retrieval_result') Object.assign(turn.trace, {
        retrieved_records: event.content.records, stay_assessments: event.content.stay_assessments,
        truncated: event.content.truncated,
      })
      if (event.stage === 'assistant') Object.assign(turn, { answer: event.content.answer, state: event.content.state, trace: event.content })
      if (['model_error', 'retrieval_error'].includes(event.stage)) {
        turn.state = 'error'
        turn.error = errors[event.content.code] || errors.unavailable
      }
    }
    state.turns = [...turns.values()].filter(turn => turn.question)
    state.historyTruncated = Boolean(history.truncated)
  } catch (error) {
    state.error = error instanceof HotelChatError ? error.message : errors.history_failed
  } finally {
    state.restoring = false
  }
}

export function newHotelConversation(state, apiBaseUrl, storage) {
  if (state.pending || state.restoring) return
  Object.assign(state, createHotelChatState())
  try { storage?.removeItem(storageKey(apiBaseUrl)) } catch { /* Saved backend history is retained. */ }
}
