import assert from 'node:assert/strict'
import { test } from 'node:test'
import { lookupHotels, removeHotel, saveHotel } from '../src/api/localHotels.js'

const center = { requested_zip: '02108', resolved_postcode: '02108', latitude: 42.36, longitude: -71.06 }
const hotel = { place_id: '001/Case +ID ', name: 'Hotel', latitude: 42.36, longitude: -71.06 }
const found = { search_center: center, hotels: [hotel] }
const empty = { search_center: null, hotels: [] }

function responses(t, values) {
  const calls = []
  t.mock.method(globalThis, 'fetch', async (url, options) => {
    calls.push({ url, options })
    const next = values.shift()
    assert.ok(next, 'Unexpected HTTP call')
    if (next instanceof Error) throw next
    return new Response(JSON.stringify(next.body), { status: next.status || 200 })
  })
  return calls
}

test('saved ZIP results bypass provider and retain leading-zero context and nights', async t => {
  const local = { ...found, hotels: [{ ...hotel, demo_nights: [{ stay_date: '2026-10-10', nightly_rate_cents: 10000, rooms_available: 20 }] }] }
  const calls = responses(t, [{ body: local }])
  const loaded = await lookupHotels('http://backend', '02108')
  assert.equal(loaded.source, 'local')
  assert.deepEqual(loaded.result, local)
  assert.deepEqual(loaded.savedIds, [hotel.place_id])
  assert.equal(calls.length, 1)
  assert.equal(new URL(calls[0].url).searchParams.get('zip'), '02108')
})

test('only an empty local success uses Part 1 API and database status by exact ID', async t => {
  const calls = responses(t, [{ body: empty }, { body: found }, { body: { saved_ids: [hotel.place_id] } }])
  const loaded = await lookupHotels('http://backend', '02108')
  assert.equal(loaded.source, 'api')
  assert.deepEqual(loaded.savedIds, [hotel.place_id])
  assert.equal(new URL(calls[1].url).pathname, '/api/live-hotels')
  assert.equal(new URL(calls[2].url).searchParams.get('place_id'), hotel.place_id)
})

test('local failure never spends provider quota', async t => {
  const calls = responses(t, [{ status: 503, body: { detail: 'Unavailable' } }])
  await assert.rejects(lookupHotels('http://backend', '02108'), error => error.state === 'localFailure')
  assert.equal(calls.length, 1)
})

test('malformed local success does not fall back', async t => {
  const calls = responses(t, [{ body: { hotels: [] } }])
  await assert.rejects(lookupHotels('http://backend', '02108'), error => error.state === 'localFailure')
  assert.equal(calls.length, 1)
})

test('provider error state is preserved', async t => {
  responses(t, [{ body: empty }, { status: 429, body: {} }])
  await assert.rejects(lookupHotels('http://backend', '02108'), error => error.state === 'limited')
})

test('failed database status is not treated as unsaved', async t => {
  responses(t, [{ body: empty }, { body: found }, { status: 503, body: {} }])
  await assert.rejects(lookupHotels('http://backend', '02108'), error => error.state === 'statusFailure')
})

test('save includes only provider fields and the result context; checks acknowledgment', async t => {
  const calls = responses(t, [{ body: { saved: true, hotel } }])
  await saveHotel('http://backend', { ...hotel, demo_nights: [] }, center)
  const sent = JSON.parse(calls[0].options.body)
  assert.deepEqual(sent.search_center, center)
  assert.equal(sent.hotel.place_id, hotel.place_id)
  assert.ok(!('demo_nights' in sent.hotel))
})

test('failed or mismatched saves never acknowledge success', async t => {
  responses(t, [{ status: 503, body: {} }, { body: { saved: true, hotel: { place_id: 'wrong' } } }])
  await assert.rejects(saveHotel('http://backend', hotel, center), error => error.state === 'saveFailure')
  await assert.rejects(saveHotel('http://backend', hotel, center), error => error.state === 'saveFailure')
})

test('removal preserves opaque IDs and requires a successful acknowledgment', async t => {
  const calls = responses(t, [{ status: 503, body: {} }, { body: { removed: true, place_id: hotel.place_id } }])
  await assert.rejects(removeHotel('http://backend', hotel.place_id), error => error.state === 'removeFailure')
  await removeHotel('http://backend', hotel.place_id)
  assert.equal(calls[1].options.method, 'DELETE')
  assert.equal(new URL(calls[1].url).searchParams.get('place_id'), hotel.place_id)
})
