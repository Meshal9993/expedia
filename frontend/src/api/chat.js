// Only our backend URL is called here; provider credentials never enter Vue.
export class ChatError extends Error {
  constructor(code = 'unavailable') {
    super(code)
    this.code = code
  }
}

export async function streamChat(apiBaseUrl, messages, { signal, onDelta }) {
  let reader
  try {
    const response = await fetch(`${apiBaseUrl}/api/chat`, {
      method: 'POST', signal,
      headers: { 'Content-Type': 'application/json', Accept: 'application/x-ndjson' },
      body: JSON.stringify({ messages }),
    })
    if (!response.ok) {
      throw new ChatError(({ 422: 'invalid', 429: 'limited', 503: 'configuration' })[response.status])
    }
    if (!response.body) throw new ChatError()
    reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    let hasText = false

    function consume(line) {
      if (!line.trim()) return false
      const event = JSON.parse(line)
      if (event.type === 'error') {
        const codes = ['configuration', 'limited', 'timeout', 'unavailable', 'incomplete']
        throw new ChatError(codes.includes(event.code) ? event.code : 'unavailable')
      }
      if (event.type === 'done') {
        if (!hasText) throw new ChatError()
        return true
      }
      if (event.type !== 'delta' || typeof event.text !== 'string') throw new ChatError()
      hasText ||= Boolean(event.text.trim())
      onDelta(event.text)
      return false
    }

    while (true) {
      const { value, done } = await reader.read()
      buffer += decoder.decode(value, { stream: !done })
      let newline
      while ((newline = buffer.indexOf('\n')) !== -1) {
        const line = buffer.slice(0, newline)
        buffer = buffer.slice(newline + 1)
        if (consume(line)) return
      }
      if (done) {
        if (buffer && consume(buffer)) return
        throw new ChatError('incomplete')
      }
    }
  } catch (error) {
    if (error instanceof ChatError) throw error
    throw new ChatError(error.name === 'AbortError' ? 'timeout' : 'unavailable')
  } finally {
    if (reader) {
      try { await reader.cancel() } catch { /* The connection may already be closed. */ }
      reader.releaseLock()
    }
  }
}
