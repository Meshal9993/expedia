<script setup>
import { computed, onBeforeUnmount, ref } from 'vue'
import HotelMap from './HotelMap.vue'
import { lookupHotels, removeHotel, saveHotel } from '../api/localHotels'

const props = defineProps({ apiBaseUrl: { type: String, required: true } })
const zip = ref('')
const state = ref('idle')
const result = ref(null)
const selectedHotelId = ref(null)
const source = ref('api')
const savedIds = ref(new Set())
const pendingIds = ref(new Set())
const actionMessage = ref('')
const actionFailed = ref(false)
const mutationRequests = new Set()
const currency = new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' })
const mapHotels = computed(() => (result.value?.hotels || []).map(hotel => ({
  ...hotel, name: hotel.name || 'Name unavailable',
})))
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
  localFailure: 'Saved hotels could not be loaded. Please try again.',
  statusFailure: 'Saved hotel status could not be checked. Please try again.',
}
const isLoading = computed(() => state.value === 'loading')
const isError = computed(() => ['invalid', 'unresolved', 'failure', 'limited', 'localFailure', 'statusFailure'].includes(state.value))
const feedback = computed(() => {
  if (state.value === 'results') return `${result.value.hotels.length} hotel places returned. Select a hotel to see it on the map.`
  if (state.value === 'empty' && source.value === 'local') return 'No saved hotels remain for this ZIP. Search again to check API results.'
  return messages[state.value]
})
const locationLabel = computed(() => [result.value?.search_center.city, result.value?.search_center.state].filter(Boolean).join(', '))

async function searchHotels() {
  if (isLoading.value || pendingIds.value.size) return
  result.value = null
  selectedHotelId.value = null
  hotelButtons.clear()
  savedIds.value = new Set()
  actionMessage.value = ''

  if (!/^[0-9]{5}$/.test(zip.value)) {
    state.value = 'invalid'
    return
  }

  state.value = 'loading'
  activeRequest = new AbortController()
  const timeout = setTimeout(() => activeRequest?.abort(), 20000)
  try {
    const loaded = await lookupHotels(props.apiBaseUrl, zip.value, activeRequest.signal)
    result.value = loaded.result
    source.value = loaded.source
    savedIds.value = new Set(loaded.savedIds)
    state.value = loaded.result.hotels.length ? 'results' : 'empty'
  } catch (error) {
    state.value = error.state || 'failure'
  } finally {
    clearTimeout(timeout)
    activeRequest = null
  }
}

async function changeLocalHotel(hotel, remove = false) {
  const id = hotel.place_id
  if (pendingIds.value.has(id) || isLoading.value || (remove ? !savedIds.value.has(id) : savedIds.value.has(id))) return
  pendingIds.value.add(id)
  actionMessage.value = ''
  const controller = new AbortController()
  mutationRequests.add(controller)
  const timeout = setTimeout(() => controller.abort(), 20000)
  try {
    if (remove) {
      await removeHotel(props.apiBaseUrl, id, controller.signal)
      savedIds.value.delete(id)
      if (source.value === 'local') {
        result.value = { ...result.value, hotels: result.value.hotels.filter(item => item.place_id !== id) }
        if (selectedHotelId.value === id) selectedHotelId.value = null
        if (!result.value.hotels.length) state.value = 'empty'
      }
      actionMessage.value = 'Hotel removed from local storage, including its saved ZIPs and demo nights.'
    } else {
      await saveHotel(props.apiBaseUrl, hotel, result.value.search_center, controller.signal)
      savedIds.value.add(id)
      actionMessage.value = 'Hotel saved locally. Its October 10–14 demo nights use simulated classroom values.'
    }
    actionFailed.value = false
  } catch {
    actionFailed.value = true
    actionMessage.value = remove
      ? 'Hotel could not be removed. It remains marked as saved; please try again.'
      : 'Hotel could not be saved. Please try again.'
  } finally {
    clearTimeout(timeout)
    mutationRequests.delete(controller)
    pendingIds.value.delete(id)
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

onBeforeUnmount(() => {
  activeRequest?.abort()
  mutationRequests.forEach(controller => controller.abort())
})
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
            :disabled="isLoading || pendingIds.size > 0"
          />
          <button type="submit" aria-label="Search live hotels" :disabled="isLoading || pendingIds.size > 0">
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

    <p
      v-if="actionMessage"
      :class="['message-card', 'compact-message', { 'error-message': actionFailed }]"
      :role="actionFailed ? 'alert' : 'status'"
    >{{ actionMessage }}</p>

    <div v-if="result" class="live-results">
      <div class="section-heading live-results-heading">
        <div>
          <h2>Hotels near {{ result.search_center.requested_zip }}</h2>
          <p class="live-source-label">{{ source === 'local' ? 'Saved locally' : 'API results' }}</p>
          <p v-if="locationLabel" class="live-location">{{ locationLabel }}</p>
        </div>
        <p>{{ source === 'local'
          ? 'Saved hotels for this ZIP; this is not a complete list of nearby hotels.'
          : 'Hotels returned by the provider within 5 km of the resolved ZIP location.' }}</p>
      </div>

      <div class="live-results-grid">
        <div class="live-list-column">
          <h3>Hotel places</h3>
          <ul v-if="result.hotels.length" class="live-hotel-list" aria-label="Live hotel results">
            <li v-for="hotel in result.hotels" :key="hotel.place_id" class="live-hotel-row">
              <button
                :ref="(element) => rememberButton(hotel.place_id, element)"
                type="button"
                :class="['live-hotel-card', { 'is-selected': selectedHotelId === hotel.place_id }]"
                :aria-pressed="selectedHotelId === hotel.place_id"
                @click="selectedHotelId = hotel.place_id"
              >
                <span class="live-hotel-details">
                  <strong>{{ hotel.name || 'Name unavailable' }}</strong>
                  <span v-if="hotel.formatted_address">{{ hotel.formatted_address }}</span>
                  <span class="live-selection-label">{{ selectedHotelId === hotel.place_id ? 'Selected on map' : 'Show on map' }}</span>
                </span>
              </button>
              <div class="live-hotel-actions" :aria-busy="pendingIds.has(hotel.place_id)">
                <button
                  class="secondary-action" type="button"
                  :aria-label="`Add ${hotel.name || 'unnamed hotel'} to local storage`"
                  :disabled="savedIds.has(hotel.place_id) || pendingIds.has(hotel.place_id)"
                  @click="changeLocalHotel(hotel)"
                >{{ pendingIds.has(hotel.place_id) && !savedIds.has(hotel.place_id) ? 'Saving…' : 'Add to Local' }}</button>
                <span v-if="savedIds.has(hotel.place_id)">Saved locally</span>
                <button
                  v-if="savedIds.has(hotel.place_id)"
                  class="secondary-action" type="button"
                  :aria-label="`Remove ${hotel.name || 'unnamed hotel'} from local storage`"
                  :disabled="pendingIds.has(hotel.place_id)"
                  @click="changeLocalHotel(hotel, true)"
                >{{ pendingIds.has(hotel.place_id) ? 'Removing…' : 'Remove from Local' }}</button>
              </div>
              <div v-if="source === 'local'" class="live-demo-nights">
                <p><strong>Simulated classroom data</strong> — not API rates or actual availability.</p>
                <table v-if="hotel.demo_nights?.length">
                  <caption>Demo nightly rates and available rooms</caption>
                  <thead><tr><th scope="col">Date</th><th scope="col">Demo rate</th><th scope="col">Demo rooms</th></tr></thead>
                  <tbody>
                    <tr v-for="night in hotel.demo_nights" :key="night.stay_date">
                      <td>{{ night.stay_date }}</td>
                      <td>{{ currency.format(night.nightly_rate_cents / 100) }}</td>
                      <td>{{ night.rooms_available }}</td>
                    </tr>
                  </tbody>
                </table>
                <p v-else>No demo nights stored for this hotel.</p>
              </div>
            </li>
          </ul>
          <p v-else class="section-placeholder">{{ source === 'local' ? 'No saved hotels remain for this ZIP. Search again to check API results.' : 'No hotel places returned for this search.' }}</p>
        </div>

        <div class="live-map-column">
          <h3>Map <span>· within 5 km</span></h3>
          <HotelMap
            :search-center="result.search_center"
            :hotels="mapHotels"
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
