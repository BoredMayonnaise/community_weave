/**
 * Geolocation & Reverse Geocoding Utility for Community Weave
 * Uses HTML5 Geolocation API and OpenStreetMap Nominatim (Free, no API key needed).
 */

const NEIGHBORHOOD_CENTROIDS = {
  'downtown': [37.7749, -122.4194],
  'north hills': [37.7950, -122.4180],
  'riverside': [37.7600, -122.4350],
  'west end': [37.7650, -122.4550],
  'oakridge': [37.7450, -122.4200],
  'manila': [14.5995, 120.9842],
  'pasay': [14.5378, 120.9998],
  'caloocan': [14.6571, 120.9841],
  'cadiz': [10.9570, 123.2980],
  'talisay': [10.7300, 122.9660],
  'bacolod': [10.6766, 122.9510],
  'cebu': [10.3157, 123.8854],
  'davao': [7.0707, 125.6087],
  'quezon city': [14.6760, 121.0437]
}

export const geo = {
  /**
   * Request device GPS coordinates
   */
  async getPosition() {
    return new Promise((resolve, reject) => {
      if (!navigator.geolocation) {
        return reject(new Error('Geolocation is not supported by your browser.'))
      }

      navigator.geolocation.getCurrentPosition(
        (pos) => {
          resolve({
            latitude: pos.coords.latitude,
            longitude: pos.coords.longitude,
            accuracy: pos.coords.accuracy
          })
        },
        (err) => {
          let msg = 'Could not access location.'
          if (err.code === err.PERMISSION_DENIED) {
            msg = 'Location permission was denied. Please allow location access in your browser or phone settings.'
          } else if (err.code === err.POSITION_UNAVAILABLE) {
            msg = 'Location information is currently unavailable.'
          } else if (err.code === err.TIMEOUT) {
            msg = 'Location request timed out.'
          }
          reject(new Error(msg))
        },
        {
          enableHighAccuracy: true,
          timeout: 10000,
          maximumAge: 60000
        }
      )
    })
  },

  /**
   * Reverse-geocode coordinates into neighborhood and address using OpenStreetMap Nominatim
   */
  async reverseGeocode(lat, lon) {
    try {
      const url = `https://nominatim.openstreetmap.org/reverse?format=json&lat=${encodeURIComponent(lat)}&lon=${encodeURIComponent(lon)}&zoom=18&addressdetails=1`
      const res = await fetch(url, {
        headers: {
          'Accept': 'application/json'
        }
      })
      if (!res.ok) throw new Error('Geocoding service unavailable')
      const data = await res.json()
      const addr = data.address || {}

      const isPH = addr.country_code === 'ph' || (addr.country && addr.country.toLowerCase() === 'philippines')

      // Local divisions in order of specificity
      const localCandidates = [
        addr.village,
        addr.quarter,
        addr.neighbourhood,
        addr.suburb,
        addr.residential,
        addr.city_district
      ].map(s => (s || '').trim()).filter(Boolean)

      // Municipality / City / Town / Province
      const city = (
        addr.city ||
        addr.municipality ||
        addr.town ||
        (localCandidates.length > 1 ? addr.suburb : '') ||
        addr.county ||
        addr.province ||
        addr.state ||
        ''
      ).trim()

      // Detect if this location should be formatted as a Philippine Barangay
      let brgyCandidate = localCandidates.find(c =>
        /^(barangay|brgy\.?|zone)/i.test(c) || /^\d+$/.test(c)
      )

      const looksLikeBarangay = isPH || Boolean(brgyCandidate)

      let neighborhood = ''

      if (looksLikeBarangay) {
        const raw = brgyCandidate || localCandidates[0] || ''
        let clean = raw.replace(/^(barangay|brgy\.?)\s*/i, '').trim()

        if (clean) {
          neighborhood = `Brgy. ${clean}`
        } else {
          neighborhood = city ? `Brgy. ${city}` : 'Barangay'
        }

        // Always append city/municipality to avoid duplicate names like "Zone 15"
        if (city && !neighborhood.toLowerCase().includes(city.toLowerCase())) {
          neighborhood += `, ${city}`
        }
      } else {
        // Non-PH / other states: e.g. "Mission District, San Francisco" or "Greenwich, London"
        const local = localCandidates[0] || ''
        if (local && city && !local.toLowerCase().includes(city.toLowerCase())) {
          neighborhood = `${local}, ${city}`
        } else if (local) {
          neighborhood = local
        } else if (city) {
          neighborhood = city
        } else {
          neighborhood = 'Local Area'
        }
      }

      // Street level address or landmark (e.g. "Rizal St.", "123 Main St.", "City Hall")
      const road = addr.road || addr.pedestrian || addr.street || ''
      const houseNumber = addr.house_number || ''
      let streetAddress = [houseNumber, road].filter(Boolean).join(' ')
      const landmark = addr.amenity || addr.shop || addr.building || ''

      if (!streetAddress && landmark) {
        streetAddress = landmark
      } else if (streetAddress && landmark && !streetAddress.toLowerCase().includes(landmark.toLowerCase())) {
        streetAddress = `${streetAddress} (${landmark})`
      }

      return {
        neighborhood,
        address: streetAddress || '',
        city,
        displayName: data.display_name || ''
      }
    } catch (err) {
      // Fallback if network blip
      return {
        neighborhood: 'My Neighborhood',
        address: '',
        city: '',
        displayName: ''
      }
    }
  },

  /**
   * One-touch locate user: gets GPS coordinates and reverse-geocodes
   */
  async locateUser() {
    const coords = await this.getPosition()
    const geoDetails = await this.reverseGeocode(coords.latitude, coords.longitude)
    return {
      latitude: coords.latitude,
      longitude: coords.longitude,
      neighborhood: geoDetails.neighborhood,
      address: geoDetails.address,
      city: geoDetails.city
    }
  },

  /**
   * Get default or estimated coordinates for a post/neighborhood
   */
  getCoordinatesForPost(post, index = 0) {
    if (post.latitude && post.longitude) {
      return [post.latitude, post.longitude]
    }

    const key = (post.neighborhood || '').toLowerCase().trim()
    let base = NEIGHBORHOOD_CENTROIDS[key]
    if (!base) {
      const match = Object.keys(NEIGHBORHOOD_CENTROIDS).find(k => key.includes(k))
      if (match) {
        base = NEIGHBORHOOD_CENTROIDS[match]
      }
    }
    if (!base) {
      base = [37.7749, -122.4194]
    }

    // Add tiny deterministic jitter so markers with same neighborhood don't perfectly stack
    const id = post.id || index || 1
    const jitterLat = ((id * 17) % 100 - 50) * 0.00015
    const jitterLng = ((id * 23) % 100 - 50) * 0.00015

    return [base[0] + jitterLat, base[1] + jitterLng]
  }
}
