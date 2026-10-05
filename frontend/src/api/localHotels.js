// HTTP calls stay in the View; the backend owns persistence and provider calls.
export class HotelSearchError extends Error {
  constructor(state) {
    super(state)
    this.state = state
  }
}

async function requestJson(url, options, failureState) {
  try {
    const response = await fetch(url, options)
    if (!response.ok) {
      const state = failureState === 'failure'
        ? ({ 422: 'invalid', 404: 'unresolved', 429: 'limited' })[response.status] || 'failure'
        : failureState
      throw new HotelSearchError(state)
    }
    return await response.json()
  } catch (error) {
    throw error instanceof HotelSearchError ? error : new HotelSearchError(failureState)
  }
}

function validResult(data, zip, allowEmptyCenter = false) {
  return Array.isArray(data?.hotels)
    && ((allowEmptyCenter && data.hotels.length === 0 && data.search_center === null)
      || (data.search_center?.requested_zip === zip && data.search_center.resolved_postcode === zip))
}

export async function lookupHotels(apiBaseUrl, zip, signal) {
  const query = new URLSearchParams({ zip })
  const local = await requestJson(`${apiBaseUrl}/api/saved-hotels?${query}`, { signal }, 'localFailure')
  if (!validResult(local, zip, true)) throw new HotelSearchError('localFailure')
  if (local.hotels.length) {
    return { result: local, source: 'local', savedIds: local.hotels.map(hotel => hotel.place_id) }
  }

  // A local error never falls back to the provider; only an empty success does.
  const api = await requestJson(`${apiBaseUrl}/api/live-hotels?${query}`, { signal }, 'failure')
  if (!validResult(api, zip)) throw new HotelSearchError('failure')
  if (!api.hotels.length) return { result: api, source: 'api', savedIds: [] }
  const ids = new URLSearchParams()
  api.hotels.forEach(hotel => ids.append('place_id', hotel.place_id))
  const status = await requestJson(`${apiBaseUrl}/api/saved-hotels/status?${ids}`, { signal }, 'statusFailure')
  if (!Array.isArray(status?.saved_ids) || status.saved_ids.some(id => typeof id !== 'string')) {
    throw new HotelSearchError('statusFailure')
  }
  return { result: api, source: 'api', savedIds: status.saved_ids }
}

export async function saveHotel(apiBaseUrl, hotel, searchCenter, signal) {
  const data = await requestJson(`${apiBaseUrl}/api/saved-hotels`, {
    method: 'POST', signal, headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      hotel: {
        place_id: hotel.place_id, name: hotel.name ?? null,
        formatted_address: hotel.formatted_address ?? null,
        latitude: hotel.latitude, longitude: hotel.longitude,
      },
      search_center: searchCenter,
    }),
  }, 'saveFailure')
  if (data?.saved !== true || data.hotel?.place_id !== hotel.place_id) {
    throw new HotelSearchError('saveFailure')
  }
  return data
}

export async function removeHotel(apiBaseUrl, placeId, signal) {
  const query = new URLSearchParams({ place_id: placeId })
  const data = await requestJson(`${apiBaseUrl}/api/saved-hotels?${query}`, {
    method: 'DELETE', signal,
  }, 'removeFailure')
  if (data?.removed !== true || data.place_id !== placeId) throw new HotelSearchError('removeFailure')
  return data
}
