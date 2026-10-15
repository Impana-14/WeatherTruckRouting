import { useState } from 'react'
import 'leaflet/dist/leaflet.css'
import './App.css'
import RouteMap from './RouteMap'

function App() {
  const [form, setForm] = useState({
    origin: '',
    destination: '',
    departure: '',
    loadWeight: '',
    intervalMiles: 25,
  })

  const [routes, setRoutes] = useState([])
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [forecastHour, setForecastHour] = useState(0)

  function handleChange(event) {
    setForm({
      ...form,
      [event.target.name]: event.target.value,
    })
  }


  async function handleSubmit(event) {
    event.preventDefault()
    setError('')
    setRoutes([])
    setLoading(true)

    try {
      const response = await fetch("https://weather-truck-routing-api-7z9o.onrender.com/api/plan/", {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(form),
      })

      const data = await response.json()

      if (!response.ok) {
        setError(data.error || 'Failed to plan the route.')
        return
      }

      setRoutes(data.routes || [])

      console.log('Route recommendations:', data.routes.map(route => ({
        route_number: route.route_number,
        recommended: route.recommended,
        summary: route.summary
      })))

    } catch (error) {
      setError('Could not connect to the backend. Check that Django is running.')
    } finally {
      setLoading(false)
    }
  }



  return (
    <div style={{ maxWidth: '650px', margin: '40px auto', fontFamily: 'Arial, sans-serif' }}>
      <h1>Weather-Aware Truck Routing</h1>
      <p>Plan safer truck routes using weather conditions.</p>

      <form onSubmit={handleSubmit}>
        <label>Origin</label>
        <input
          name="origin"
          value={form.origin}
          onChange={handleChange}
          placeholder="e.g. Bengaluru, India"
          required
        />

        <br /><br />

        <label>Destination</label>
        <input
          name="destination"
          value={form.destination}
          onChange={handleChange}
          placeholder="e.g. Mysuru, India"
          required
        />

        <br /><br />

        <label>Departure date and time</label>
        <input
          type="datetime-local"
          onBlur={(event) => event.target.blur()}
          name="departure"
          value={form.departure}
          onChange={handleChange}
          required
        />

        <br /><br />

        <label>Truck load weight (kg)</label>
        <input
          type="number"
          name="loadWeight"
          value={form.loadWeight}
          onChange={handleChange}
          min="0"
          step="0.1"
          placeholder="e.g. 12000"
          required
        />

        <label htmlFor="intervalMiles">
          Weather checkpoint interval (miles)
        </label>

        <select
          id="intervalMiles"
          name="intervalMiles"
          value={form.intervalMiles}
          onChange={handleChange}
          className="form-select"
        >
          <option value={10}>10 miles</option>
          <option value={25}>25 miles</option>
          <option value={50}>50 miles</option>
        </select>

        <button
          type="submit"
          disabled={loading}
          style={{ display: 'block', marginTop: '8px' }}
        >
          {loading ? 'Planning Route...' : 'Plan Route'}
        </button>

      </form>

      {loading && <p>Finding driving routes...</p>}

      {error && (
        <p style={{ color: 'red' }}>
          {error}
        </p>
      )}

      {routes.length > 0 && (
        <section style={{ marginTop: '30px' }}>
          <h2>Available Driving Routes</h2>

          {routes.map((route) => (
            <div
              key={route.route_number}
              style={{
                background: 'white',
                padding: '20px',
                marginBottom: '15px',
                borderRadius: '10px',
                border: '1px solid #d8e0eb',
              }}
            >
              <h3>
                Route {route.route_number}
                {route.recommended && ' — Recommended'}
              </h3>

              {route.summary && (
                <div
                  style={{
                    padding: '12px',
                    marginBottom: '15px',
                    borderRadius: '8px',
                    background: '#eaf7ee',
                  }}
                >
                  <h4>Route Risk Summary</h4>
                  <p>
                    <strong>Weather data coverage:</strong>{' '}
                    {route.checkpoints?.filter(
                      (checkpoint) => checkpoint.risk_score != null
                    ).length ?? 0}{' '}
                    / {route.checkpoints?.length ?? 0} checkpoints
                  </p>
                  {route.checkpoints?.some(
                    (checkpoint) => checkpoint.risk_score == null
                  ) && (
                      <p style={{ color: '#b45309', fontWeight: 'bold' }}>
                        Weather data is incomplete. Risk totals may not reflect the full route.
                        This route cannot be safely assessed until weather data is available.
                      </p>
                    )}
                  <p>
                    <strong>Severe-risk miles:</strong>{' '}
                    {route.summary.severe_miles} miles
                  </p>
                  <p>
                    <strong>High-risk miles:</strong>{' '}
                    {route.summary.high_miles} miles
                  </p>
                  <p>
                    <strong>Average risk score:</strong>{' '}
                    {route.summary.average_risk_score ?? 'Unavailable'}
                  </p>
                </div>
              )}

              <p>
                <strong>Distance:</strong>{' '}
                {(route.distance_km / 1.60934).toFixed(2)} miles
              </p>
              <p>
                <strong>Estimated driving time:</strong>{' '}
                {Math.floor(route.duration_minutes / 60)} hours{' '}
                {Math.round(route.duration_minutes % 60)} minutes
              </p>

              <h4>Weather Checkpoints</h4>

              {route.checkpoints?.map((checkpoint, index) => (
                <div
                  key={index}
                  style={{
                    padding: '12px',
                    marginTop: '10px',
                    borderTop: '1px solid #e2e8f0',
                  }}
                >
                  <strong>
                    Checkpoint {index + 1} — {checkpoint.distance_miles} miles
                  </strong>

                  <p>
                    Arrival: {new Date(checkpoint.arrival_time).toLocaleString()}
                  </p>

                  <p>
                    Risk: {(checkpoint.risk_level || 'unknown')
                      .replace('_', ' ')
                      .toUpperCase()}
                    {checkpoint.risk_score !== null &&
                      checkpoint.risk_score !== undefined
                      ? ` (Score: ${checkpoint.risk_score})`
                      : ''}
                  </p>

                  {checkpoint.weather ? (
                    <p>
                      Temperature: {checkpoint.weather.temperature_c ?? 'N/A'}°C
                      {' | '}Wind: {checkpoint.weather.wind_speed_mph != null
                        ? checkpoint.weather.wind_speed_mph.toFixed(1)
                        : 'N/A'} mph
                      {' | '}Rain: {checkpoint.weather.rain_mm ?? 'N/A'} mm
                      {' | '}Snow: {checkpoint.weather.snowfall_cm ?? 'N/A'} cm
                    </p>
                  ) : (
                    <p>Weather forecast unavailable.</p>
                  )}

                  <p>
                    {checkpoint.reasons?.join(', ')}
                  </p>
                </div>
              ))}

            </div>
          ))}
        </section>
      )}


      {routes.length > 0 && (
        <>
          <div style={{ marginTop: '24px', padding: '16px', border: '1px solid #d8e0eb', borderRadius: '10px' }}>
            <h3>Weather Forecast Timeline</h3>
            <label>
              Forecast: {forecastHour} hours from departure
            </label>
            <input
              type="range"
              min="0"
              max="48"
              step="1"
              value={forecastHour}
              onChange={(event) => setForecastHour(Number(event.target.value))}
              style={{ width: '100%' }}
            />
            <p>Use the slider to select a forecast hour from 0 to 48.</p>
          </div>

          <RouteMap routes={routes} forecastHour={forecastHour} />
        </>
      )}

    </div>
  )
}

export default App
