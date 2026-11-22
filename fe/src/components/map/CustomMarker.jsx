import { useEffect } from 'react';
import { getUrgencyLevel, urgencyStyles } from '../../utils/urgency';

export default function CustomMarker({ incident, context, onClick, isSelected }) {
  useEffect(() => {
    const { color, size, label } = urgencyStyles[getUrgencyLevel(incident.urgency_score)];
    const element = document.createElement('button');
    element.type = 'button';
    element.setAttribute('aria-label', `${incident.title}: ${label}`);
    Object.assign(element.style, { width: `${size}px`, height: `${size}px`, background: color, border: '2px solid white',
      borderRadius: '50%', cursor: 'pointer', padding: 0, boxShadow: isSelected ? '0 0 0 5px #2563EB88' : '0 2px 6px #0006' });
    const icon = context.library.divIcon({ html: element, className: '', iconSize: [size, size], iconAnchor: [size / 2, size / 2] });
    const marker = context.library.marker([incident.latitude, incident.longitude], {
      icon, keyboard: false, title: `${incident.title} · ${label}`, zIndexOffset: isSelected ? 1000 : size,
    }).addTo(context.map);
    element.onclick = (event) => { event.stopPropagation(); onClick(incident); };
    return () => { element.onclick = null; marker.remove(); };
  }, [incident, context, onClick, isSelected]);
  return null;
}
