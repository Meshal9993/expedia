<script setup>
import { nextTick, onBeforeUnmount, reactive, ref } from 'vue'
import { streamChat } from '../api/chat'

const props = defineProps({ apiBaseUrl: { type: String, required: true } })
const question = ref('')
const messages = ref([])
const pending = ref(false)
const errorMessage = ref('')
const questionInput = ref(null)
let activeRequest

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

onBeforeUnmount(() => activeRequest?.abort())
</script>

<template>
  <section class="content-section chat-panel" aria-labelledby="chat-title">
    <h2 id="chat-title">AI Chat</h2>
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
  </section>
</template>
