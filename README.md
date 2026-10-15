# Weather-Aware Truck Routing

A full-stack application that helps truck drivers compare driving routes using weather forecasts, truck load weight, estimated travel time, and weather-related risk levels.

## Features

- Geocodes origin and destination locations.
- Retrieves alternative heavy-vehicle driving routes.
- Samples weather conditions along each route at configurable intervals.
- Estimates checkpoint arrival times based on departure time and route progress.
- Evaluates wind, rain, and snowfall risks, including load-weight restrictions.
- Recommends a route based on severe-risk miles, high-risk miles, average risk, and travel time.
- Displays route options, weather checkpoints, and risk information on an interactive map.
- Includes a 0–48-hour forecast slider and weather heatmap.

## Technology Stack

**Frontend**
- React
- Vite
- React Leaflet
- Leaflet and Leaflet.heat

**Backend**
- Python
- Django
- Django REST Framework
- Open-Meteo weather forecast API
- OpenRouteService heavy-vehicle routing API
- OpenStreetMap Nominatim geocoding

## Prerequisites

Install the following before running the application:

- Python 3
- Node.js and npm
- An OpenRouteService API key

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/Impana-14/WeatherTruckRouting.git
cd WeatherTruckRouting
```

### 2. Configure the backend

Open a terminal in the project root.

Create and activate a virtual environment:

**Windows PowerShell**
```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install backend dependencies:

```powershell
python -m pip install -r requirements.txt
```

Create a `.env` file inside the `backend` directory using `.env.example` as a template:

```dotenv
DJANGO_SECRET_KEY=your-own-django-secret
OPENROUTESERVICE_API_KEY=your-own-openrouteservice-api-key
```

Replace the placeholder values with your own values. Never commit the real `.env` file or expose API keys.

Start the backend:

```powershell
python manage.py runserver
```

The backend runs at `http://127.0.0.1:8000/`.

### 3. Configure the frontend

Open a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open the local URL printed by Vite, normally `http://localhost:5173/`.

## API Configuration

- **OpenRouteService:** Provides heavy-vehicle driving routes and route geometry.
- **Open-Meteo:** Provides hourly weather forecast data.
- **OpenStreetMap Nominatim:** Resolves place names into coordinates.

API access, forecast availability, geocoding limits, and network connectivity can affect results.

## Risk Assessment

The application evaluates wind speed, rainfall intensity, snowfall intensity, and truck load weight. Risk levels are classified as Low, Moderate, High, Severe, or No Travel according to the assessment rules.

Routes with incomplete weather data should not be treated as confirmed safe routes. The recommendation logic considers weather coverage and No Travel conditions alongside route risk and travel time.

## Project Structure

```text
WeatherTruckRouting/
├── backend/
│   ├── config/
│   ├── routing/
│   ├── .env.example
│   └── manage.py
├── frontend/
│   ├── src/
│   ├── package.json
│   └── vite.config.js
├── .gitignore
└── README.md
```

## Limitations

- Weather values are forecast estimates and may differ from actual road conditions.
- Forecast availability depends on the selected travel time and weather provider.
- Route alternatives depend on the routing provider's coverage and response.
- This application is a decision-support tool and does not replace official road closures, weather warnings, or professional driver judgment.

## License

No license has been specified for this repository.