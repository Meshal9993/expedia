<script setup>
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

const props = defineProps({
  searchCenter: { type: Object, required: true },
  hotels: { type: Array, required: true },
  selectedHotelId: { type: String, default: null },
})
const emit = defineEmits(['select'])
const mapElement = ref(null)
const markers = new Map()
let map
let markerLayer
let resizeObserver

function popupContent(hotel) {
  // DOM text nodes keep provider names/addresses out of HTML interpretation.
  const content = document.createElement('div')
  const name = document.createElement('strong')
  name.textContent = hotel.name
  content.append(name)
  if (hotel.formatted_address) {
    const address = document.createElement('p')
    address.textContent = hotel.formatted_address
    content.append(address)
  }
  return content
}

function syncSelection() {
  for (const [id, marker] of markers) {
    const selected = id === props.selectedHotelId
    marker.getElement()?.classList.toggle('is-selected', selected)
    marker.getElement()?.setAttribute('aria-pressed', String(selected))
    marker.setZIndexOffset(selected ? 1000 : 0)
  }
  const selected = markers.get(props.selectedHotelId)
  if (selected) {
    map.panTo(selected.getLatLng(), { animate: false })
    selected.openPopup()
  } else {
    map.closePopup()
  }
}

function showResults() {
  if (!map) return
  markerLayer.clearLayers()
  markers.clear()
  const center = L.latLng(props.searchCenter.latitude, props.searchCenter.longitude)
  const furthestHotel = Math.max(0, ...props.hotels.map(hotel =>
    center.distanceTo([hotel.latitude, hotel.longitude]),
  ))
  // Keep the postcode at the center while fitting all returned hotel markers.
  const viewWidth = props.hotels.length ? Math.max(1500, furthestHotel * 2.4) : 11000
  map.fitBounds(center.toBounds(viewWidth), { padding: [12, 12], animate: false })
  props.hotels.forEach((hotel, index) => {
    const badge = document.createElement('span')
    badge.className = 'hotel-marker-badge'
    badge.textContent = String(index + 1)
    const marker = L.marker([hotel.latitude, hotel.longitude], {
      icon: L.divIcon({ className: 'hotel-map-marker', html: badge, iconSize: [32, 32], iconAnchor: [16, 16] }),
      title: `${index + 1}. ${hotel.name}`,
      keyboard: true,
    }).bindPopup(popupContent(hotel)).addTo(markerLayer)
    marker.getElement()?.setAttribute('aria-label', `${index + 1}. ${hotel.name}`)
    marker.on('click', () => emit('select', hotel.place_id))
    markers.set(hotel.place_id, marker)
  })
  syncSelection()
}

onMounted(() => {
  map = L.map(mapElement.value, { scrollWheelZoom: false })
  L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap contributors</a>',
  }).addTo(map)
  markerLayer = L.layerGroup().addTo(map)
  showResults()
  resizeObserver = new ResizeObserver(() => map?.invalidateSize({ pan: false }))
  resizeObserver.observe(mapElement.value)
})

watch(() => [props.searchCenter, props.hotels], showResults)
watch(() => props.selectedHotelId, () => { if (map) syncSelection() })

onBeforeUnmount(() => {
  resizeObserver?.disconnect()
  map?.remove()
  markers.clear()
  map = null
})
</script>

<template>
  <div ref="mapElement" class="live-hotel-map" role="region" aria-label="Hotel locations map" />
</template>
