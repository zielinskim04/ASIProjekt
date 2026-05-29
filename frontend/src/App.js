import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import L from 'leaflet';
import markerIcon2x from 'leaflet/dist/images/marker-icon-2x.png';
import markerIcon from 'leaflet/dist/images/marker-icon.png';
import markerShadow from 'leaflet/dist/images/marker-shadow.png';
import 'leaflet/dist/leaflet.css';
import './App.css';

// Fix leaflet default icon paths broken by webpack
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: markerIcon2x,
  iconUrl: markerIcon,
  shadowUrl: markerShadow,
});

const WARSAW_CENTER = [52.2297, 21.0122];

const POI_OPTIONS = [
  { value: 'bus_stop',    label: '🚌 Przystanki autobusowe' },
  { value: 'school',      label: '🏫 Szkoły' },
  { value: 'hospital',    label: '🏥 Szpitale' },
  { value: 'cinema',      label: '🎬 Kina' },
  { value: 'theatre',     label: '🎭 Teatry' },
  { value: 'museum',      label: '🏛️ Muzea' },
  { value: 'pub',         label: '🍺 Puby' },
  { value: 'restaurant',  label: '🍽️ Restauracje' },
  { value: 'cafe',        label: '☕ Kawiarnie' },
  { value: 'bank',        label: '🏦 Banki' },
  { value: 'parking',     label: '🅿️ Parkingi' },
  { value: 'police',      label: '👮 Policja' },
  { value: 'supermarket', label: '🛒 Supermarkety' },
];

const POI_LABELS = Object.fromEntries(POI_OPTIONS.map(o => [o.value, o.label]));

function formatPrice(price) {
  if (!price) return '—';
  return price.toLocaleString('pl-PL') + ' PLN';
}

export default function App() {
  const [properties, setProperties] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [status, setStatus] = useState(null);
  const [selectedProp, setSelectedProp] = useState(null);
  const [poiLoading, setPoiLoading] = useState(false);

  const [filters, setFilters] = useState({
    poi_category: '',
    poi_radius_m: 500,
    price_min: '',
    price_max: '',
    area_min: '',
    area_max: '',
    rooms_min: '',
    rooms_max: '',
    price_per_sqm_max: '',
  });

  // Load ingestion status once
  useEffect(() => {
    fetch('/api/v1/ingestion/status')
      .then(r => r.ok ? r.json() : null)
      .then(data => { if (data) setStatus(data); })
      .catch(() => {});
  }, []);

  // Initial load without filters
  useEffect(() => {
    setLoading(true);
    fetch('/api/v1/properties?limit=300')
      .then(r => r.ok ? r.json() : [])
      .then(data => setProperties(data))
      .catch(() => setError('Nie można połączyć z backendem.'))
      .finally(() => setLoading(false));
  }, []);

  function handleFilterChange(key, value) {
    setFilters(prev => ({ ...prev, [key]: value }));
  }

  async function handleSearch() {
    setLoading(true);
    setError(null);
    const params = new URLSearchParams();
    Object.entries(filters).forEach(([k, v]) => {
      if (v !== '' && v != null) params.append(k, v);
    });

    try {
      const res = await fetch(`/api/v1/properties?${params}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setProperties(await res.json());
    } catch {
      setError('Błąd połączenia z backendem.');
    } finally {
      setLoading(false);
    }
  }

  async function loadPropertyPOIs(propertyId) {
    setPoiLoading(true);
    setSelectedProp(null);
    try {
      const res = await fetch(`/api/v1/properties/${propertyId}`);
      if (res.ok) setSelectedProp(await res.json());
    } finally {
      setPoiLoading(false);
    }
  }

  return (
    <div className="app">
      <header className="header">
        <h1>Nieruchomości Warszawa</h1>
        {status && (
          <div className="status-info">
            <span>{status.total_properties} ofert</span>
            <span>{status.total_pois} punktów POI</span>
            {status.last_scraped_at && (
              <span>
                Ostatni scraping:{' '}
                {new Date(status.last_scraped_at).toLocaleString('pl-PL')}
              </span>
            )}
          </div>
        )}
      </header>

      <div className="layout">
        {/* ── Filter panel ── */}
        <aside className="sidebar">
          <h2>Filtry</h2>

          <div className="field">
            <label>Infrastruktura w pobliżu</label>
            <select
              value={filters.poi_category}
              onChange={e => handleFilterChange('poi_category', e.target.value)}
            >
              <option value="">Bez filtra POI</option>
              {POI_OPTIONS.map(o => (
                <option key={o.value} value={o.value}>{o.label}</option>
              ))}
            </select>
          </div>

          {filters.poi_category && (
            <div className="field">
              <label>Promień: <strong>{filters.poi_radius_m} m</strong></label>
              <input
                type="range" min={100} max={2000} step={100}
                value={filters.poi_radius_m}
                onChange={e => handleFilterChange('poi_radius_m', Number(e.target.value))}
              />
              <div className="range-ends"><span>100 m</span><span>2000 m</span></div>
            </div>
          )}

          <div className="field">
            <label>Cena (PLN)</label>
            <div className="row2">
              <input type="number" placeholder="Min"
                value={filters.price_min}
                onChange={e => handleFilterChange('price_min', e.target.value)} />
              <input type="number" placeholder="Max"
                value={filters.price_max}
                onChange={e => handleFilterChange('price_max', e.target.value)} />
            </div>
          </div>

          <div className="field">
            <label>Maks. cena za m²</label>
            <input type="number" placeholder="np. 15000"
              value={filters.price_per_sqm_max}
              onChange={e => handleFilterChange('price_per_sqm_max', e.target.value)} />
          </div>

          <div className="field">
            <label>Powierzchnia (m²)</label>
            <div className="row2">
              <input type="number" placeholder="Min"
                value={filters.area_min}
                onChange={e => handleFilterChange('area_min', e.target.value)} />
              <input type="number" placeholder="Max"
                value={filters.area_max}
                onChange={e => handleFilterChange('area_max', e.target.value)} />
            </div>
          </div>

          <div className="field">
            <label>Liczba pokoi</label>
            <div className="row2">
              <input type="number" min={1} placeholder="Min"
                value={filters.rooms_min}
                onChange={e => handleFilterChange('rooms_min', e.target.value)} />
              <input type="number" min={1} placeholder="Max"
                value={filters.rooms_max}
                onChange={e => handleFilterChange('rooms_max', e.target.value)} />
            </div>
          </div>

          <button className="search-btn" onClick={handleSearch} disabled={loading}>
            {loading ? 'Szukam…' : 'Szukaj'}
          </button>

          {error && <p className="error">{error}</p>}
          <p className="count">{properties.length} ofert na mapie</p>
        </aside>

        {/* ── Map ── */}
        <div className="map-area">
          <MapContainer center={WARSAW_CENTER} zoom={12} style={{ height: '100%', width: '100%' }}>
            <TileLayer
              attribution='© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />
            {properties
              .filter(p => p.lat && p.lon)
              .map(prop => (
                <Marker key={prop.id} position={[prop.lat, prop.lon]}>
                  <Popup>
                    <div className="popup">
                      <strong>{prop.address_clean}</strong>
                      {prop.price && <div className="popup-price">{formatPrice(prop.price)}</div>}
                      <div className="popup-meta">
                        {prop.area && <span>{prop.area} m²</span>}
                        {prop.rooms && <span>{prop.rooms} pok.</span>}
                        {prop.price_per_sqm && <span>{prop.price_per_sqm} zł/m²</span>}
                      </div>
                      <div className="popup-actions">
                        <a href={prop.link} target="_blank" rel="noopener noreferrer">
                          Oferta →
                        </a>
                        <button onClick={() => loadPropertyPOIs(prop.id)}>
                          Infrastruktura
                        </button>
                      </div>
                    </div>
                  </Popup>
                </Marker>
              ))}
          </MapContainer>
        </div>
      </div>

      {/* ── POI detail panel ── */}
      {(poiLoading || selectedProp) && (
        <div className="overlay" onClick={() => setSelectedProp(null)}>
          <div className="poi-panel" onClick={e => e.stopPropagation()}>
            {poiLoading ? (
              <p>Ładowanie…</p>
            ) : (
              <>
                <div className="poi-header">
                  <h3>{selectedProp.address_clean}</h3>
                  <button onClick={() => setSelectedProp(null)}>✕</button>
                </div>
                {selectedProp.price && (
                  <p className="poi-price">{formatPrice(selectedProp.price)}
                    {selectedProp.price_per_sqm && ` · ${selectedProp.price_per_sqm} zł/m²`}
                  </p>
                )}
                <h4>Najbliższe punkty infrastruktury:</h4>
                {selectedProp.nearest_pois.length === 0 ? (
                  <p>Brak danych POI dla tej lokalizacji.</p>
                ) : (
                  <ul className="poi-list">
                    {selectedProp.nearest_pois.map(poi => (
                      <li key={poi.id}>
                        <span>{POI_LABELS[poi.category] || poi.category}</span>
                        <span className="poi-name">{poi.name || '(bez nazwy)'}</span>
                        <span className="poi-dist">{poi.distance_m} m</span>
                      </li>
                    ))}
                  </ul>
                )}
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
