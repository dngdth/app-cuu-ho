/** Extract an explicit destination from a full Google Maps URL (never its camera). */
export const extractCoordsFromURL = (url) => {
  if (typeof url !== 'string' || !url) return null;
  try {
    const parsed = new URL(url);
    const hosts = ['maps.google.com', 'maps.google.com.vn', 'google.com', 'www.google.com', 'google.com.vn', 'www.google.com.vn'];
    if (!['http:', 'https:'].includes(parsed.protocol) || !hosts.includes(parsed.hostname) || parsed.username || parsed.password) return null;
    if (!parsed.hostname.startsWith('maps.google.') && !parsed.pathname.startsWith('/maps')) return null;
    const pair = (value) => {
      const match = /^(?:loc:)?\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*$/i.exec(value || '');
      if (!match) return null;
      const lat = Number(match[1]);
      const lng = Number(match[2]);
      return Math.abs(lat) <= 90 && Math.abs(lng) <= 180 ? { lat, lng } : null;
    };
    for (const key of ['destination', 'daddr']) {
      if (parsed.searchParams.has(key)) return pair(parsed.searchParams.get(key));
    }
    const pins = [...decodeURIComponent(url).matchAll(/!3d(-?\d+(?:\.\d+)?)!4d(-?\d+(?:\.\d+)?)/g)];
    if (pins.length) return pair(`${pins.at(-1)[1]},${pins.at(-1)[2]}`);
    if (parsed.searchParams.has('query_place_id') || parsed.searchParams.has('destination_place_id')) return null;
    for (const key of ['q', 'query']) {
      const destination = pair(parsed.searchParams.get(key));
      if (destination) return destination;
    }
    const pathPin = decodeURIComponent(parsed.pathname).match(/\/maps\/(?:place|search)\/(-?\d+(?:\.\d+)?),\s*(-?\d+(?:\.\d+)?)(?:\/|$)/);
    return pathPin ? pair(`${pathPin[1]},${pathPin[2]}`) : null;
  } catch {
    return null;
  }
};
