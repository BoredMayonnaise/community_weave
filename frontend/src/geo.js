/**
 * Geolocation & Reverse Geocoding Utility for Community Weave
 * Uses HTML5 Geolocation API, OpenStreetMap Nominatim, and IP-fallback for 100% resilience.
 */

const NEIGHBORHOOD_CENTROIDS = {
  // Metro Manila & Philippines
  'caloocan': [14.6571, 120.9841],
  'zone 15': [14.7330, 121.0300],
  'manila': [14.5995, 120.9842],
  'quezon city': [14.6760, 121.0437],
  'quezon': [14.6760, 121.0437],
  'makati': [14.5547, 121.0244],
  'taguig': [14.5176, 121.0509],
  'bgc': [14.5505, 121.0494],
  'pasig': [14.5764, 121.0851],
  'mandaluyong': [14.5794, 121.0359],
  'pasay': [14.5378, 120.9998],
  'marikina': [14.6507, 121.1029],
  'valenzuela': [14.7011, 120.9830],
  'malabon': [14.6625, 120.9566],
  'navotas': [14.6667, 120.9417],
  'las piñas': [14.4445, 120.9939],
  'parañaque': [14.4793, 121.0198],
  'muntinlupa': [14.4081, 121.0415],
  'san juan': [14.6019, 121.0355],
  'cadiz': [10.9570, 123.2980],
  'cadiz city': [10.9570, 123.2980],
  'talisay': [10.7300, 122.9660],
  'bacolod': [10.6766, 122.9510],
  'cebu': [10.3157, 123.8854],
  'cebu city': [10.3157, 123.8854],
  'davao': [7.0707, 125.6087],
  'davao city': [7.0707, 125.6087],
  'iloilo': [10.7202, 122.5621],
  'iloilo city': [10.7202, 122.5621],

  // International / Demo centroids
  'downtown': [14.5995, 120.9842],
  'north hills': [14.6650, 121.0200],
  'riverside': [14.5800, 121.0100],
  'west end': [14.5600, 120.9950],
  'oakridge': [14.6100, 121.0400]
}

export const geo = {
  /**
   * Helper to query navigator.geolocation with custom timeout
   */
  _queryNavigatorGeo(options) {
    return new Promise((resolve, reject) => {
      if (!navigator.geolocation) {
        return reject(new Error('Geolocation not supported by this browser.'))
      }
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          resolve({
            latitude: pos.coords.latitude,
            longitude: pos.coords.longitude,
            accuracy: pos.coords.accuracy,
            source: options.enableHighAccuracy ? 'gps' : 'network'
          })
        },
        (err) => reject(err),
        options
      )
    })
  },

  /**
   * IP-based fallback geolocation for when GPS is unavailable, denied, or indoors
   */
  async _getIpLocation() {
    try {
      const res = await fetch('https://ipwho.is/', { signal: AbortSignal.timeout(5000) })
      if (!res.ok) throw new Error('IP service error')
      const data = await res.json()
      if (data && data.success && typeof data.latitude === 'number' && typeof data.longitude === 'number') {
        return {
          latitude: data.latitude,
          longitude: data.longitude,
          accuracy: 5000,
          city: data.city || '',
          region: data.region || '',
          country: data.country || '',
          source: 'ip'
        }
      }
    } catch {
      // Ignore network timeout on IP fallback
    }

    // Default fallback to Manila / PH centroid
    return {
      latitude: 14.5995,
      longitude: 120.9842,
      accuracy: 10000,
      city: 'Manila',
      region: 'Metro Manila',
      country: 'Philippines',
      source: 'fallback'
    }
  },

  /**
   * Progressive device GPS coordinates query
   */
  async getPosition() {
    // 1. Try GPS with high accuracy (4s timeout)
    try {
      return await this._queryNavigatorGeo({
        enableHighAccuracy: true,
        timeout: 4000,
        maximumAge: 60000
      })
    } catch (e1) {
      // If user explicitly denied permission, immediately fallback to IP
      if (e1 && e1.code === 1) { // PERMISSION_DENIED
        return await this._getIpLocation()
      }

      // 2. Try fast network/coarse location (5s timeout)
      try {
        return await this._queryNavigatorGeo({
          enableHighAccuracy: false,
          timeout: 5000,
          maximumAge: 300000
        })
      } catch (e2) {
        // 3. Fallback to IP geolocation
        return await this._getIpLocation()
      }
    }
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
        },
        signal: AbortSignal.timeout(6000)
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

      // Street level address or landmark
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
        neighborhood: neighborhood || (city ? `Brgy. ${city}` : 'My Neighborhood'),
        address: streetAddress || '',
        city,
        displayName: data.display_name || ''
      }
    } catch {
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
      neighborhood: geoDetails.neighborhood || (coords.city ? `Brgy. ${coords.city}` : 'My Neighborhood'),
      address: geoDetails.address,
      city: geoDetails.city || coords.city || ''
    }
  },

  /**
   * Get coordinates for a post/neighborhood
   */
  getCoordinatesForPost(post, index = 0, userPos = null) {
    if (post.latitude && post.longitude) {
      return [Number(post.latitude), Number(post.longitude)]
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
      if (userPos && userPos[0] && userPos[1]) {
        base = [userPos[0], userPos[1]]
      } else {
        base = [14.5995, 120.9842] // Default to Manila/PH centroid
      }
    }

    // Add tiny deterministic jitter so markers with same neighborhood don't perfectly stack
    const id = post.id || index || 1
    const jitterLat = ((id * 17) % 100 - 50) * 0.00015
    const jitterLng = ((id * 23) % 100 - 50) * 0.00015

    return [base[0] + jitterLat, base[1] + jitterLng]
  }
}
