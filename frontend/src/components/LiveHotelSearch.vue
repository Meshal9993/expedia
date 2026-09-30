<script setup>
import { computed, onBeforeUnmount, ref } from 'vue'
import HotelMap from './HotelMap.vue'

const props = defineProps({ apiBaseUrl: { type: String, required: true } })
const zip = ref('')
const state = ref('idle')
const result = ref(null)
const selectedHotelId = ref(null)
const hotelButtons = new Map()
let activeRequest

const messages = {
  idle: 'Enter a five-digit U.S. ZIP code to find hotel locations nearby.',
  loading: 'Searching for hotels…',
  invalid: 'Enter exactly five digits for a U.S. ZIP code, including any leading zero.',
  unresolved: 'That ZIP code could not be resolved. Check the ZIP and try again.',
  empty: 'No nearby hotels were found within 5 km of this ZIP location.',
  failure: 'The hotel search service is unavailable. Please try again later.',
  limited: 'Hotel searches are temporarily limited. Please try again later.',
}
const isLoading = computed(() => state.value === 'loading')
const isError = computed(() => ['invalid', 'unresolved', 'failure', 'limited'].includes(state.value))
const feedback = computed(() => state.value === 'results'
  ? `${result.value.hotels.length} hotel places returned. Select a hotel to see it on the map.`
  : messages[state.value])
const locationLabel = computed(() => [result.value?.search_center.city, result.value?.search_center.state].filter(Boolean).join(', '))

async function searchHotels() {
  if (isLoading.value) return
  result.value = null
  selectedHotelId.value = null
  hotelButtons.clear()

  if (!/^[0-9]{5}$/.test(zip.value)) {
    state.value = 'invalid'
    return
  }

  state.value = 'loading'
  activeRequest = new AbortController()
  const timeout = setTimeout(() => activeRequest?.abort(), 20000)
  try {
    const response = await fetch(`${props.apiBaseUrl}/api/live-hotels?zip=${encodeURIComponent(zip.value)}`, {
      signal: activeRequest.signal,
    })
    if (!response.ok) {
      state.value = ({ 422: 'invalid', 404: 'unresolved', 429: 'limited' })[response.status] || 'failure'
      return
    }
    const data = await response.json()
    if (!data?.search_center || !Array.isArray(data.hotels)) {
      state.value = 'failure'
      return
    }
    result.value = data
    state.value = data.hotels.length ? 'results' : 'empty'
  } catch {
    state.value = 'failure'
  } finally {
    clearTimeout(timeout)
    activeRequest = null
  }
}

function rememberButton(id, element) {
  if (element) hotelButtons.set(id, element)
  else hotelButtons.delete(id)
}

function selectFromMap(id) {
  selectedHotelId.value = id
  hotelButtons.get(id)?.scrollIntoView({ block: 'nearest', inline: 'nearest' })
}

onBeforeUnmount(() => activeRequest?.abort())
</script>

<template>
  <section class="content-section live-search-panel" aria-labelledby="live-title">
    <div class="live-search-header">
      <div>
        <h1 id="live-title">Live Hotel Search</h1>
        <p class="live-intro">Find hotel locations near a U.S. ZIP code.</p>
      </div>
      <form class="search-form live-search-form" novalidate @submit.prevent="searchHotels">
        <label for="live-zip">ZIP code</label>
        <div class="search-controls">
          <input
            id="live-zip"
            v-model="zip"
            name="zip"
            type="text"
            inputmode="numeric"
            autocomplete="postal-code"
            placeholder="e.g. 16801"
            aria-describedby="live-zip-help live-search-feedback"
            :aria-invalid="state === 'invalid'"
            :disabled="isLoading"
          />
          <button type="submit" aria-label="Search live hotels" :disabled="isLoading">
            {{ isLoading ? 'Searching…' : 'Search' }}
          </button>
        </div>
        <p id="live-zip-help" class="field-hint">Five digits, including any leading zero.</p>
      </form>
    </div>

    <p
      id="live-search-feedback"
      :class="['message-card', 'live-feedback', { 'error-message': isError }]"
      :role="isError ? 'alert' : 'status'"
      :aria-busy="isLoading"
    >{{ feedback }}</p>

    <div v-if="result" class="live-results">
      <div class="section-heading live-results-heading">
        <div>
          <h2>Hotels near {{ result.search_center.requested_zip }}</h2>
          <p v-if="locationLabel" class="live-location">{{ locationLabel }}</p>
        </div>
        <p>Hotels returned by the provider within 5 km of the resolved ZIP location.</p>
      </div>

      <div class="live-results-grid">
        <div class="live-list-column">
          <h3>Hotel places</h3>
          <ul v-if="result.hotels.length" class="live-hotel-list" aria-label="Live hotel results">
            <li v-for="hotel in result.hotels" :key="hotel.place_id">
              <button
                :ref="(element) => rememberButton(hotel.place_id, element)"
                type="button"
                :class="['live-hotel-card', { 'is-selected': selectedHotelId === hotel.place_id }]"
                :aria-pressed="selectedHotelId === hotel.place_id"
                @click="selectedHotelId = hotel.place_id"
              >
                <span class="live-hotel-details">
                  <strong>{{ hotel.name }}</strong>
                  <span v-if="hotel.formatted_address">{{ hotel.formatted_address }}</span>
                  <span class="live-selection-label">{{ selectedHotelId === hotel.place_id ? 'Selected on map' : 'Show on map' }}</span>
                </span>
              </button>
            </li>
          </ul>
          <p v-else class="section-placeholder">No hotel places returned for this search.</p>
        </div>

        <div class="live-map-column">
          <h3>Map <span>· within 5 km</span></h3>
          <HotelMap
            :search-center="result.search_center"
            :hotels="result.hotels"
            :selected-hotel-id="selectedHotelId"
            @select="selectFromMap"
          />
        </div>
      </div>
      <p class="live-data-note">
        Hotel data: <a href="https://www.geoapify.com/">Geoapify</a>.
        These place results do not confirm room availability and may not include every nearby hotel.
      </p>
    </div>
  </section>
</template>
