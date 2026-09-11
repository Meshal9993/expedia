<script setup>
import { ref } from 'vue'

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'

const hotelName = ref('')
const searchedName = ref('')
const results = ref([])
const hasSearched = ref(false)
const isLoading = ref(false)
const errorMessage = ref('')

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

function formatDate(date) {
  return dateFormatter.format(new Date(`${date}T00:00:00Z`))
}

async function searchHotels() {
  const query = hotelName.value.trim()

  searchedName.value = query
  results.value = []
  errorMessage.value = ''
  hasSearched.value = true

  if (!query) {
    errorMessage.value = 'Enter a hotel name to search.'
    return
  }

  isLoading.value = true

  try {
    const response = await fetch(`${apiBaseUrl}/api/hotels?name=${encodeURIComponent(query)}`)
    if (!response.ok) {
      throw new Error('Search request failed')
    }

    const data = await response.json()
    results.value = data.results
  } catch {
    errorMessage.value = 'The hotel search is unavailable. Please try again.'
  } finally {
    isLoading.value = false
  }
}
</script>

<template>
  <main class="page-shell">
    <section class="search-panel" aria-labelledby="page-title">
      <div class="heading-block">
        <p class="eyebrow">Hotel stays</p>
        <h1 id="page-title">Find a hotel</h1>
        <p class="intro">Search by hotel name to see its available stays.</p>
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
          <button type="submit" :disabled="isLoading">
            {{ isLoading ? 'Searching…' : 'Search' }}
          </button>
        </div>
      </form>
    </section>

    <section class="results-panel" aria-live="polite" aria-busy="isLoading">
      <p v-if="isLoading" class="status-message">Searching for available stays…</p>

      <div v-else-if="errorMessage" class="message-card" role="alert">
        {{ errorMessage }}
      </div>

      <template v-else-if="results.length">
        <div class="results-heading">
          <div>
            <p class="eyebrow">Search results</p>
            <h2>Available stays</h2>
          </div>
          <p>{{ results.length }} {{ results.length === 1 ? 'stay' : 'stays' }} found</p>
        </div>

        <div class="table-scroll">
          <table>
            <thead>
              <tr>
                <th scope="col">Hotel</th>
                <th scope="col">Location</th>
                <th scope="col">Stay</th>
                <th scope="col">Check-in</th>
                <th scope="col">Check-out</th>
                <th scope="col">Nightly rate</th>
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
              </tr>
            </tbody>
          </table>
        </div>
      </template>

      <div v-else-if="hasSearched" class="message-card">
        No hotels found for “{{ searchedName }}”. Try another hotel name.
      </div>
    </section>
  </main>
</template>
