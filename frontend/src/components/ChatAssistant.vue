<script setup>
import { nextTick, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { streamChat } from '../api/chat'
import { createHotelChatState, newHotelConversation, restoreHotelConversation, submitHotelQuestion } from '../api/hotelChat'

const props = defineProps({ apiBaseUrl: { type: String, required: true } })
const question = ref('')
const messages = ref([])
const pending = ref(false)
const errorMessage = ref('')
const questionInput = ref(null)
let activeRequest
const hotel = reactive(createHotelChatState())
const hotelInput = ref(null)
let hotelRequest
const pretty = value => JSON.stringify(value, null, 2)

function browserStorage() {
  try { return window.localStorage } catch { return null }
}

async function askHotelQuestion() {
  if (hotel.pending || hotel.restoring) return
  hotelRequest = new AbortController()
  const timeout = setTimeout(() => hotelRequest?.abort(), 120000)
  try {
    await submitHotelQuestion(hotel, props.apiBaseUrl, { storage: browserStorage(), signal: hotelRequest.signal })
  } finally {
    clearTimeout(timeout)
    hotelRequest = null
    await nextTick()
    hotelInput.value?.focus()
  }
}

async function reloadHotelHistory() {
  hotelRequest = new AbortController()
  const timeout = setTimeout(() => hotelRequest?.abort(), 15000)
  try {
    await restoreHotelConversation(hotel, props.apiBaseUrl, { storage: browserStorage(), signal: hotelRequest.signal })
  } finally {
    clearTimeout(timeout)
    hotelRequest = null
  }
}

function newHotelChat() {
  newHotelConversation(hotel, props.apiBaseUrl, browserStorage())
  hotelInput.value?.focus()
}

onMounted(reloadHotelHistory)

const errors = {
  configuration: 'Chat is not configured. Check the backend OpenAI key and model settings.',
  limited: 'Chat is temporarily limited or its quota has been reached. Please try again later.',
  timeout: 'The reply took too long. Please try again.',
  unavailable: 'The chat service is unavailable. Please try again.',
  incomplete: 'The reply was interrupted. Please try again; any text shown is incomplete.',
  invalid: 'This conversation is too long or invalid. Clear the chat and try again.',
}

async function ask() {
  if (pending.value || !question.value.trim()) return
  const content = question.value.trim()
  const history = messages.value.filter(message => message.complete)
    .slice(-20).map(({ role, content }) => ({ role, content }))
  const user = reactive({ role: 'user', content, complete: false })
  const answer = reactive({ role: 'assistant', content: '', complete: false })
  messages.value.push(user, answer)
  question.value = ''
  errorMessage.value = ''
  pending.value = true
  activeRequest = new AbortController()
  const timeout = setTimeout(() => activeRequest?.abort(), 130000)
  try {
    await streamChat(props.apiBaseUrl, [...history, { role: 'user', content }], {
      signal: activeRequest.signal,
      onDelta: text => { answer.content += text },
    })
    user.complete = true
    answer.complete = true
  } catch (error) {
    errorMessage.value = errors[error.code] || errors.unavailable
    answer.content ||= 'No reply received.'
  } finally {
    clearTimeout(timeout)
    activeRequest = null
    pending.value = false
    await nextTick()
    questionInput.value?.focus()
  }
}

function clearChat() {
  messages.value = []
  errorMessage.value = ''
  questionInput.value?.focus()
}

onBeforeUnmount(() => { activeRequest?.abort(); hotelRequest?.abort() })
</script>

<template>
  <section class="content-section chat-panel" aria-labelledby="chat-title">
    <h2 id="chat-title">Saved hotel assistant</h2>
    <p class="chat-note">Answers use saved local records. Rates and room availability are simulated classroom data.</p>
    <p v-if="hotel.conversationId" class="chat-note">Conversation ID: {{ hotel.conversationId }}</p>
    <p v-if="hotel.restoring" role="status">Loading saved conversation…</p>
    <p v-if="hotel.historyTruncated" role="status">Showing recent events. Older history remains saved in the backend.</p>
    <p v-if="hotel.storageWarning" role="status">{{ hotel.storageWarning }}</p>
    <div class="chat-messages hotel-chat-messages" :aria-busy="hotel.pending || hotel.restoring" aria-label="Saved hotel conversation">
      <article v-for="(turn, index) in hotel.turns" :key="index" class="chat-message">
        <strong>You</strong>
        <p>{{ turn.question }}</p>
        <strong>Hotel assistant</strong>
        <p v-if="turn.state === 'loading'" role="status">Looking up saved hotel records…</p>
        <p v-if="turn.state === 'no_matches'" role="status">No matching saved records.</p>
        <p v-if="turn.state === 'insufficient_data'" role="status">Insufficient data for a complete answer.</p>
        <p v-if="turn.state === 'incomplete'" role="status">This saved turn did not finish.</p>
        <p v-if="turn.answer">{{ turn.answer }}</p>
        <p v-if="turn.error" class="error-message" role="alert">{{ turn.error }}</p>
        <details v-if="turn.trace" class="rag-trace">
          <summary>RAG Trace</summary>
          <p><strong>Proposed SQL</strong></p>
          <pre>{{ turn.trace.proposed_sql || 'No valid query was proposed.' }}</pre>
          <p><strong>Executed SQL</strong></p>
          <pre>{{ turn.trace.executed_sql || 'No query was executed.' }}</pre>
          <p><strong>Parameters</strong></p>
          <pre>{{ pretty(turn.trace.parameters) }}</pre>
          <p><strong>Retrieved records — simulated classroom nights</strong></p>
          <pre>{{ pretty(turn.trace.retrieved_records) }}</pre>
          <template v-if="turn.trace.stay_assessments?.length">
            <p><strong>Required-night checks and totals (cents)</strong></p>
            <pre>{{ pretty(turn.trace.stay_assessments) }}</pre>
          </template>
          <p v-if="turn.trace.truncated">Retrieval was truncated; this is incomplete evidence.</p>
        </details>
      </article>
    </div>
    <p v-if="hotel.error && !hotel.turns.some(turn => turn.error === hotel.error)" class="error-message" role="alert">{{ hotel.error }}</p>
    <form class="chat-form" @submit.prevent="askHotelQuestion">
      <label for="hotel-question">Question about saved hotels</label>
      <textarea id="hotel-question" ref="hotelInput" v-model="hotel.question" rows="3" maxlength="4000"
        placeholder="Which saved hotels in 02108 have rooms from 2026-10-10 to 2026-10-13?"
        :disabled="hotel.pending || hotel.restoring" required />
      <div class="chat-actions">
        <button type="submit" :disabled="hotel.pending || hotel.restoring || !hotel.question.trim()">{{ hotel.pending ? 'Asking…' : 'Ask' }}</button>
        <button type="button" :disabled="hotel.pending || hotel.restoring" @click="newHotelChat">New conversation</button>
        <button v-if="hotel.conversationId" type="button" :disabled="hotel.pending || hotel.restoring" @click="reloadHotelHistory">Reload history</button>
      </div>
    </form>

    <details class="basic-chat">
    <summary>Basic chat — class checkpoint</summary>
    <p class="chat-note">General chat with OpenAI. Saved hotel records are not connected to this chat yet.</p>

    <div v-if="messages.length" class="chat-messages" aria-label="Chat conversation" :aria-busy="pending">
      <article v-for="(message, index) in messages" :key="index" :class="['chat-message', `chat-${message.role}`]">
        <strong>{{ message.role === 'user' ? 'You' : 'Assistant' }}</strong>
        <p>{{ message.content || 'Thinking…' }}</p>
        <span v-if="message.role === 'assistant' && !message.complete && message.content && !pending" class="chat-note">Incomplete reply</span>
      </article>
    </div>

    <p v-if="pending" role="status">Waiting for a reply…</p>
    <p v-if="errorMessage" class="error-message" role="alert">{{ errorMessage }}</p>
    <form class="chat-form" @submit.prevent="ask">
      <label for="chat-question">Your question</label>
      <textarea
        id="chat-question" ref="questionInput" v-model="question" rows="3"
        maxlength="4000" placeholder="Type a question…" :disabled="pending" required
      />
      <div class="chat-actions">
        <button type="submit" :disabled="pending || !question.trim()">{{ pending ? 'Asking…' : 'Ask' }}</button>
        <button type="button" class="secondary-action" :disabled="pending || !messages.length" @click="clearChat">Clear chat</button>
      </div>
    </form>
    </details>
  </section>
</template>
