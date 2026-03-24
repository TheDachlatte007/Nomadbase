import maplibregl from 'maplibre-gl'

export { maplibregl }

export const TYPE_COLORS = {
  park: '#2d7a2d',
  restaurant: '#c86f31',
  cafe: '#8b5e3c',
  cultural: '#5b4a8a',
  attraction: '#0f5c52',
  hiking: '#1a6e4a',
  viewpoint: '#1a5c8a',
  stay: '#8c4f6f',
  essentials: '#7a6336',
  transport: '#355d8a',
}

export function createRasterStyle() {
  return {
    version: 8,
    sources: {
      osm: {
        type: 'raster',
        tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'],
        tileSize: 256,
        attribution: '&copy; OpenStreetMap contributors',
      },
    },
    layers: [
      {
        id: 'osm',
        type: 'raster',
        source: 'osm',
      },
    ],
  }
}

export function boundsToBboxString(bounds) {
  const southWest = bounds.getSouthWest()
  const northEast = bounds.getNorthEast()
  return [southWest.lng, southWest.lat, northEast.lng, northEast.lat]
    .map((value) => Number(value).toFixed(6))
    .join(',')
}

export function fitMapToCoordinates(map, coordinates, options = {}) {
  const valid = (coordinates || []).filter(
    (item) =>
      Array.isArray(item) &&
      item.length === 2 &&
      Number.isFinite(item[0]) &&
      Number.isFinite(item[1])
  )
  if (!map || !valid.length) return

  if (valid.length === 1) {
    map.easeTo({
      center: valid[0],
      zoom: options.singleZoom || 12,
      duration: options.duration || 700,
    })
    return
  }

  let west = valid[0][0]
  let east = valid[0][0]
  let south = valid[0][1]
  let north = valid[0][1]

  for (const [lng, lat] of valid.slice(1)) {
    west = Math.min(west, lng)
    east = Math.max(east, lng)
    south = Math.min(south, lat)
    north = Math.max(north, lat)
  }

  map.fitBounds(
    [
      [west, south],
      [east, north],
    ],
    {
      padding: options.padding || 40,
      maxZoom: options.maxZoom || 13,
      duration: options.duration || 700,
    }
  )
}

export function escapeHtml(value) {
  return String(value ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;')
}

export function featureCollection(features = []) {
  return {
    type: 'FeatureCollection',
    features,
  }
}

export function placeToFeature(place) {
  return {
    type: 'Feature',
    geometry: {
      type: 'Point',
      coordinates: [place.lon, place.lat],
    },
    properties: {
      id: place.id,
      name: place.name,
      place_type: place.place_type,
      description: place.description || '',
      region: place.region || '',
      context_line: place.context_line || place.place_type,
      color: TYPE_COLORS[place.place_type] || '#5f6d69',
      website_url: place.website_url || '',
      wikipedia_url: place.wikipedia_url || '',
    },
  }
}

export function cityToFeature(city) {
  if (city.lat === null || city.lon === null) return null
  return {
    type: 'Feature',
    geometry: {
      type: 'Point',
      coordinates: [city.lon, city.lat],
    },
    properties: {
      id: city.id,
      name: city.name,
      country: city.country || '',
      sort_order: city.sort_order,
      label: `${city.sort_order + 1}. ${city.name}`,
      subtitle: city.country ? `${city.name}, ${city.country}` : city.name,
    },
  }
}

export function routeLineFeature(cities) {
  const coordinates = (cities || [])
    .filter((city) => city.lat !== null && city.lon !== null)
    .map((city) => [city.lon, city.lat])

  if (coordinates.length < 2) return null

  return {
    type: 'Feature',
    geometry: {
      type: 'LineString',
      coordinates,
    },
    properties: {},
  }
}
