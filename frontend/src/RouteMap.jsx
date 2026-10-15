import { MapContainer, TileLayer, Polyline, CircleMarker, Popup, useMap } from 'react-leaflet'
import { useEffect } from 'react'
import 'leaflet/dist/leaflet.css'
import 'leaflet.heat'
import L from 'leaflet'

function WeatherHeatmap({ routes, forecastHour }) {
    const map = useMap()

    useEffect(() => {
        const points = routes.flatMap((route) =>
            (route.checkpoints || [])
                .filter((checkpoint) => {
                    if (
                        checkpoint.risk_score == null ||
                        checkpoint.latitude == null ||
                        checkpoint.longitude == null
                    ) {
                        return false
                    }

                    const departureTime = new Date(
                        route.checkpoints[0].arrival_time
                    ).getTime()

                    const checkpointTime = new Date(
                        checkpoint.arrival_time
                    ).getTime()

                    const hoursFromDeparture =
                        (checkpointTime - departureTime) / (1000 * 60 * 60)

                    return Math.abs(hoursFromDeparture - forecastHour) < 0.5
                })
                .map((checkpoint) => {
                    const intensity = {
                        low: 0.2,
                        moderate: 0.4,
                        high: 0.65,
                        severe: 0.85,
                        no_travel: 1,
                    }

                    return [
                        checkpoint.latitude,
                        checkpoint.longitude,
                        intensity[checkpoint.risk_level] ?? 0.2,
                    ]
                })
        )

        const heatLayer = L.heatLayer(points, {
            radius: 35,
            blur: 25,
            maxZoom: 12,
            max: 1,
            minOpacity: 0.35,
            gradient: {
                0.2: '#16a34a',
                0.4: '#eab308',
                0.65: '#f97316',
                0.85: '#dc2626',
                1.0: '#7f1d1d',
            },
        })

        heatLayer.addTo(map)

        return () => {
            map.removeLayer(heatLayer)
        }
    }, [map, routes, forecastHour])

    return null
}

function RouteMap({ routes, forecastHour }) {
    const validRoutes = routes.filter(
        (route) => route.geometry?.coordinates?.length > 0
    )

    if (validRoutes.length === 0) {
        return <p>No route geometry available to display.</p>
    }

    const firstCoordinate = validRoutes[0].geometry.coordinates[0]
    const center = [firstCoordinate[1], firstCoordinate[0]]

    const routeColors = ['#1769aa', '#16a34a', '#9333ea']

    return (
        <div style={{ marginTop: '24px' }}>
            <h2>Route Map</h2>

            <MapContainer
                center={center}
                zoom={8}
                style={{
                    height: '450px',
                    width: '100%',
                    borderRadius: '12px',
                    border: '1px solid #d8e0eb',
                }}
            >
                <TileLayer
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                />
                <WeatherHeatmap
                    routes={validRoutes}
                    forecastHour={forecastHour}
                />

                {validRoutes.map((route, routeIndex) => {
                    const positions = route.geometry.coordinates.map(
                        ([longitude, latitude]) => [latitude, longitude]
                    )

                    return (
                        <div key={route.route_number}>
                            <Polyline
                                positions={positions}
                                pathOptions={{
                                    color: routeColors[routeIndex % routeColors.length],
                                    weight: routeIndex === 0 ? 6 : 4,
                                    opacity: routeIndex === 0 ? 1 : 0.8,
                                    dashArray: routeIndex === 1 ? "10, 8" : undefined,
                                }}
                            />

                            {route.checkpoints?.map((checkpoint, index) => {
                                const departureTime = new Date(
                                    route.checkpoints[0].arrival_time
                                ).getTime()

                                const checkpointTime = new Date(checkpoint.arrival_time).getTime()

                                const hoursFromDeparture =
                                    (checkpointTime - departureTime) / (1000 * 60 * 60)

                                const isSelectedHour =
                                    Math.abs(hoursFromDeparture - forecastHour) < 0.5
                                const colors = {
                                    low: '#16a34a',
                                    moderate: '#eab308',
                                    high: '#f97316',
                                    severe: '#dc2626',
                                    unknown: '#64748b',
                                }

                                return (
                                    <CircleMarker
                                        key={`${route.route_number}-${index}`}
                                        center={[checkpoint.latitude, checkpoint.longitude]}
                                        radius={isSelectedHour ? 11 : 7}
                                        pathOptions={{
                                            color: isSelectedHour
                                                ? '#2563eb'
                                                : colors[checkpoint.risk_level] || colors.unknown,
                                            weight: isSelectedHour ? 4 : 2,
                                            fillOpacity: 0.9,
                                        }}
                                    >
                                        <Popup>
                                            <strong>Route {route.route_number} — Checkpoint {index + 1}</strong>
                                            <br />
                                            Distance: {checkpoint.distance_miles} miles
                                            <br />
                                            Risk: {checkpoint.risk_level}
                                            <br />
                                            Arrival: {new Date(checkpoint.arrival_time).toLocaleString()}
                                            <br />
                                            Temperature: {checkpoint.weather?.temperature_c ?? 'N/A'}°C
                                            <br />
                                            Wind: {checkpoint.weather?.wind_speed_mph != null
                                                ? `${checkpoint.weather.wind_speed_mph.toFixed(1)} mph`
                                                : 'N/A'}
                                        </Popup>
                                    </CircleMarker>
                                )
                            })}
                        </div>
                    )
                })}
            </MapContainer>
        </div>
    )
}

export default RouteMap
