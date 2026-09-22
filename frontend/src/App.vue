<script setup>
import { onMounted, ref } from 'vue'

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'

const demoTravelers = [
  { user_id: 'U001', display_name: 'Demo Traveler 1' },
  { user_id: 'U002', display_name: 'Demo Traveler 2' },
  { user_id: 'U003', display_name: 'Demo Traveler 3' },
  { user_id: 'U004', display_name: 'Demo Traveler 4' },
  { user_id: 'U005', display_name: 'Demo Traveler 5' },
  { user_id: 'U006', display_name: 'Demo Traveler 6' },
]

const hotelName = ref('')
const searchedName = ref('')
const results = ref([])
const hasSearched = ref(false)
const isSearching = ref(false)
const searchError = ref('')

const selectedStay = ref(null)
const selectedTravelerId = ref(demoTravelers[0].user_id)
const isCreatingBooking = ref(false)
const bookingMessage = ref('')
const bookingMessageType = ref('')

const bookings = ref([])
const historyFilter = ref('')
const isLoadingHistory = ref(false)
const historyMessage = ref('')
const historyMessageType = ref('')
const bookingActionId = ref('')
const pendingDeleteId = ref('')

const dateFormatter = new Intl.DateTimeFormat('en-US', {
  month: 'short',
  day: 'numeric',
  year: 'numeric',
  timeZone: 'UTC',
})

const currencyFormatter = new Intl.NumberFormat('en-US', {
  style: 'currency',
  currency: 'USD',
  maximumFractionDigits: 0,
})

function formatDate(value) {
  return dateFormatter.format(new Date(`${value}T00:00:00Z`))
}

function todayIsoDate() {
  return new Date().toISOString().slice(0, 10)
}

function errorDetail(data, fallback) {
  if (typeof data?.detail === 'string') {
    return data.detail
  }
  if (Array.isArray(data?.detail) && data.detail[0]?.msg) {
    return data.detail[0].msg
  }
  return fallback
}

async function requestJson(path, options = {}, fallbackMessage = 'The request failed.') {
  const response = await fetch(`${apiBaseUrl}${path}`, options)
  let data = null

  try {
    data = await response.json()
  } catch {
    // The fallback below keeps non-JSON server failures readable.
  }

  if (!response.ok) {
    throw new Error(errorDetail(data, fallbackMessage))
  }
  return data
}

async function searchHotels() {
  const query = hotelName.value.trim()

  searchedName.value = query
  results.value = []
  searchError.value = ''
  hasSearched.value = true

  if (!query) {
    searchError.value = 'Enter a hotel name to search.'
    return
  }

  isSearching.value = true

  try {
    const data = await requestJson(
      `/api/hotels?name=${encodeURIComponent(query)}`,
      {},
      'The hotel search is unavailable. Please try again.',
    )
    results.value = data.results
  } catch (error) {
    searchError.value = error.message
  } finally {
    isSearching.value = false
  }
}

function chooseStay(stay) {
  selectedStay.value = stay
  bookingMessage.value = ''
  bookingMessageType.value = ''
}

function clearSelectedStay() {
  selectedStay.value = null
}

async function confirmBooking() {
  if (!selectedStay.value) {
    bookingMessage.value = 'Choose an available stay before confirming a booking.'
    bookingMessageType.value = 'error'
    return
  }

  isCreatingBooking.value = true
  bookingMessage.value = ''
  bookingMessageType.value = ''

  try {
    const data = await requestJson(
      '/api/bookings',
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: selectedTravelerId.value,
          trip_id: selectedStay.value.trip_id,
          booked_on: todayIsoDate(),
        }),
      },
      'The booking could not be created. Please try again.',
    )
    bookingMessage.value = `Booking ${data.booking.booking_id} was confirmed.`
    bookingMessageType.value = 'success'
    selectedStay.value = null
    await loadBookingHistory(false)
  } catch (error) {
    bookingMessage.value = error.message
    bookingMessageType.value = 'error'
  } finally {
    isCreatingBooking.value = false
  }
}

async function loadBookingHistory(announce = true) {
  isLoadingHistory.value = true
  pendingDeleteId.value = ''
  if (announce) {
    historyMessage.value = ''
    historyMessageType.value = ''
  }

  const query = historyFilter.value
    ? `?user_id=${encodeURIComponent(historyFilter.value)}`
    : ''

  try {
    const data = await requestJson(
      `/api/bookings${query}`,
      {},
      'Booking history could not be loaded. Please try again.',
    )
    bookings.value = data.bookings
  } catch (error) {
    bookings.value = []
    historyMessage.value = error.message
    historyMessageType.value = 'error'
  } finally {
    isLoadingHistory.value = false
  }
}

async function cancelBooking(bookingId) {
  bookingActionId.value = bookingId
  historyMessage.value = ''
  historyMessageType.value = ''

  try {
    const updated = await requestJson(
      `/api/bookings/${encodeURIComponent(bookingId)}`,
      {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: 'cancelled' }),
      },
      `Booking ${bookingId} could not be cancelled.`,
    )
    bookings.value = bookings.value.map((item) =>
      item.booking.booking_id === bookingId ? updated : item,
    )
    historyMessage.value = `Booking ${bookingId} was cancelled and remains in history.`
    historyMessageType.value = 'success'
  } catch (error) {
    historyMessage.value = error.message
    historyMessageType.value = 'error'
  } finally {
    bookingActionId.value = ''
  }
}

function requestDelete(bookingId) {
  pendingDeleteId.value = bookingId
  historyMessage.value = ''
  historyMessageType.value = ''
}

function keepBooking() {
  pendingDeleteId.value = ''
}

async function deleteBooking(bookingId) {
  bookingActionId.value = bookingId
  historyMessage.value = ''
  historyMessageType.value = ''

  try {
    await requestJson(
      `/api/bookings/${encodeURIComponent(bookingId)}`,
      { method: 'DELETE' },
      `Booking ${bookingId} could not be deleted.`,
    )
    bookings.value = bookings.value.filter(
      (item) => item.booking.booking_id !== bookingId,
    )
    pendingDeleteId.value = ''
    historyMessage.value = `Test booking ${bookingId} was deleted.`
    historyMessageType.value = 'success'
  } catch (error) {
    historyMessage.value = error.message
    historyMessageType.value = 'error'
  } finally {
    bookingActionId.value = ''
  }
}

onMounted(() => loadBookingHistory(false))
</script>

<template>
  <main class="page-shell">
    <section class="search-panel" aria-labelledby="page-title">
      <div class="heading-block">
        <p class="eyebrow">Hotel search</p>
        <h1 id="page-title">Find your next stay</h1>
        <p class="intro">Search by hotel name, choose an available stay, and book for a demo traveler.</p>
      </div>

      <form class="search-form" @submit.prevent="searchHotels">
        <label for="hotel-name">Hotel name</label>
        <div class="search-controls">
          <input
            id="hotel-name"
            v-model="hotelName"
            name="hotel-name"
            type="search"
            placeholder="Enter a hotel name"
            autocomplete="off"
          />
          <button type="submit" :disabled="isSearching">
            {{ isSearching ? 'Searching…' : 'Search' }}
          </button>
        </div>
      </form>
    </section>

    <section class="content-section results-panel" aria-live="polite" :aria-busy="isSearching">
      <p v-if="isSearching" class="message-card">Searching for available stays…</p>

      <div v-else-if="searchError" class="message-card error-message" role="alert">
        {{ searchError }}
      </div>

      <template v-else-if="results.length">
        <div class="section-heading">
          <div>
            <p class="eyebrow">Search results</p>
            <h2>Available stays</h2>
          </div>
          <p>{{ results.length }} {{ results.length === 1 ? 'stay' : 'stays' }} found</p>
        </div>

        <div class="table-scroll">
          <table class="stays-table">
            <thead>
              <tr>
                <th scope="col">Hotel</th>
                <th scope="col">Location</th>
                <th scope="col">Stay</th>
                <th scope="col">Check-in</th>
                <th scope="col">Check-out</th>
                <th scope="col">Nightly rate</th>
                <th scope="col">Action</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="stay in results" :key="stay.trip_id">
                <td class="hotel-name">{{ stay.hotel_name }}</td>
                <td>{{ stay.city }}, {{ stay.state }}</td>
                <td>{{ stay.trip_name }}</td>
                <td>{{ formatDate(stay.check_in) }}</td>
                <td>{{ formatDate(stay.check_out) }}</td>
                <td>{{ currencyFormatter.format(stay.nightly_rate_usd) }}</td>
                <td>
                  <button class="table-action primary-action" type="button" @click="chooseStay(stay)">
                    Book this stay
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </template>

      <div v-else-if="hasSearched" class="message-card">
        No hotels found for “{{ searchedName }}”. Try another hotel name.
      </div>

      <div v-else class="section-placeholder">
        Search for a hotel to see available stays.
      </div>
    </section>

    <section id="make-booking" class="content-section booking-panel" aria-labelledby="booking-title">
      <div class="section-heading">
        <div>
          <p class="eyebrow">Make a booking</p>
          <h2 id="booking-title">Confirm a stay</h2>
        </div>
        <p>Choose a result first. Selecting a stay does not create a booking.</p>
      </div>

      <div
        v-if="bookingMessage"
        :class="['message-card', 'compact-message', `${bookingMessageType}-message`]"
        role="status"
      >
        {{ bookingMessage }}
      </div>

      <form v-if="selectedStay" class="booking-card" @submit.prevent="confirmBooking">
        <div class="selected-stay">
          <span class="selection-label">Selected hotel and stay</span>
          <strong>{{ selectedStay.hotel_name }}</strong>
          <span>{{ selectedStay.trip_name }}</span>
          <span>
            {{ formatDate(selectedStay.check_in) }}–{{ formatDate(selectedStay.check_out) }}
            · {{ currencyFormatter.format(selectedStay.nightly_rate_usd) }} nightly
          </span>
        </div>

        <div class="booking-fields">
          <div class="field-group">
            <label for="demo-traveler">Demo traveler</label>
            <select id="demo-traveler" v-model="selectedTravelerId">
              <option
                v-for="traveler in demoTravelers"
                :key="traveler.user_id"
                :value="traveler.user_id"
              >
                {{ traveler.display_name }} ({{ traveler.user_id }})
              </option>
            </select>
          </div>
          <p class="booking-date">Booking date: {{ formatDate(todayIsoDate()) }}</p>
        </div>

        <div class="button-row">
          <button class="primary-action" type="submit" :disabled="isCreatingBooking">
            {{ isCreatingBooking ? 'Confirming…' : 'Confirm Booking' }}
          </button>
          <button class="secondary-action" type="button" :disabled="isCreatingBooking" @click="clearSelectedStay">
            Choose another stay
          </button>
        </div>
      </form>

      <div v-else class="section-placeholder">
        Select “Book this stay” beside an available hotel stay to begin.
      </div>
    </section>

    <section class="content-section history-panel" aria-labelledby="history-title">
      <div class="section-heading history-heading">
        <div>
          <p class="eyebrow">Booking history</p>
          <h2 id="history-title">Saved bookings</h2>
        </div>

        <div class="history-controls">
          <div class="field-group compact-field">
            <label for="history-traveler">Traveler</label>
            <select id="history-traveler" v-model="historyFilter" @change="loadBookingHistory">
              <option value="">All demo travelers</option>
              <option
                v-for="traveler in demoTravelers"
                :key="traveler.user_id"
                :value="traveler.user_id"
              >
                {{ traveler.display_name }}
              </option>
            </select>
          </div>
          <button class="secondary-action" type="button" :disabled="isLoadingHistory" @click="loadBookingHistory">
            {{ isLoadingHistory ? 'Loading…' : 'Refresh history' }}
          </button>
        </div>
      </div>

      <div
        v-if="historyMessage"
        :class="['message-card', 'compact-message', `${historyMessageType}-message`]"
        role="status"
      >
        {{ historyMessage }}
      </div>

      <p v-if="isLoadingHistory" class="message-card">Loading booking history…</p>

      <div v-else-if="bookings.length" class="table-scroll">
        <table class="history-table">
          <thead>
            <tr>
              <th scope="col">Booking ID</th>
              <th scope="col">Traveler</th>
              <th scope="col">Hotel</th>
              <th scope="col">Trip / stay</th>
              <th scope="col">Check-in</th>
              <th scope="col">Check-out</th>
              <th scope="col">Status</th>
              <th scope="col">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in bookings" :key="item.booking.booking_id">
              <td class="booking-id">{{ item.booking.booking_id }}</td>
              <td>{{ item.traveler.display_name }}</td>
              <td>{{ item.hotel.hotel_name }}</td>
              <td>{{ item.trip.trip_name }}</td>
              <td>{{ formatDate(item.trip.check_in) }}</td>
              <td>{{ formatDate(item.trip.check_out) }}</td>
              <td>
                <span :class="['status-badge', `status-${item.booking.status}`]">
                  {{ item.booking.status }}
                </span>
              </td>
              <td class="actions-cell">
                <div class="actions-wrap">
                  <button
                    v-if="item.booking.status === 'confirmed'"
                    class="table-action secondary-action"
                    type="button"
                    :disabled="bookingActionId === item.booking.booking_id"
                    @click="cancelBooking(item.booking.booking_id)"
                  >
                    Cancel
                  </button>
                  <button
                    class="table-action delete-action"
                    type="button"
                    :disabled="bookingActionId === item.booking.booking_id"
                    @click="requestDelete(item.booking.booking_id)"
                  >
                    Delete
                  </button>
                </div>

                <div
                  v-if="pendingDeleteId === item.booking.booking_id"
                  class="delete-confirmation"
                  role="alert"
                >
                  <p>Delete {{ item.booking.booking_id }} permanently? Use this only for a test booking.</p>
                  <div class="confirmation-actions">
                    <button class="secondary-action" type="button" @click="keepBooking">Keep booking</button>
                    <button
                      class="danger-action"
                      type="button"
                      :disabled="bookingActionId === item.booking.booking_id"
                      @click="deleteBooking(item.booking.booking_id)"
                    >
                      {{ bookingActionId === item.booking.booking_id ? 'Deleting…' : 'Confirm delete' }}
                    </button>
                  </div>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div v-else class="section-placeholder">
        No booking history found for this traveler.
      </div>
    </section>
  </main>
</template>
