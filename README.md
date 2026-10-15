Weather-Aware Truck Routing
A full-stack application that helps truck drivers compare driving routes
using weather forecasts, truck load weight, estimated travel time, and
weather-related risk levels.
Live Application
- Frontend:
  https://weather-truck-routing-frontend-i9l6.onrender.com/
- Backend API:
  https://weather-truck-routing-api-7z9o.onrender.com/
- GitHub Repository:
  https://github.com/Impana-14/WeatherTruckRouting
The backend root URL may return a Django 404 because the application
exposes its API under /api/ and the admin interface under /admin/.
This does not, by itself, mean the API is unavailable.
Features
- Geocodes origin and destination locations.
- Retrieves up to three alternative driving routes using a routing
  API.
- Samples weather conditions along each route at configurable
  intervals of 10, 25, or 50 miles.
- Estimates checkpoint arrival times from the departure time and route
  progress.
- Retrieves forecast weather data for route checkpoints.
- Evaluates wind, rainfall, snowfall, and truck load-weight
  restrictions.
- Classifies checkpoint risk as Low, Moderate, High, Severe, or No
  Travel.
- Recommends a route using route risk summaries and estimated travel
  time.
- Displays route options, distances, estimated driving times,
  checkpoint ETAs, weather conditions, and risk summaries.
- Shows routes and weather checkpoints on an interactive map.
- Includes a 0--48-hour forecast timeline slider and a weather heatmap
  for the selected checkpoint arrival-time window.
Technology Stack
Frontend
- React
- Vite
- JavaScript
- React Leaflet
- Leaflet
- Leaflet.heat
- OpenStreetMap map tiles
Backend
- Python
- Django
- Django REST Framework
- WeatherAPI for weather forecasts
- OpenRouteService for driving routes
- OpenStreetMap Nominatim for geocoding
Deployment
- GitHub for source control
- Render for hosting the frontend and backend
Prerequisites
- Python 3
- Node.js and npm
- An OpenRouteService API key
- A WeatherAPI API key
API keys may have usage limits or require an active subscription. Check
the providers' current plans and terms.
Getting Started
1. Clone the repository
git clone https://github.com/Impana-14/WeatherTruckRouting.git
cd WeatherTruckRouting
2. Configure the backend
From the project root, create a virtual environment:
Windows PowerShell
cd backend
python -m venv .venv
Activate the environment:
.\\.venv\\Scripts\\Activate.ps1
Install dependencies:
python -m pip install -r requirements.txt
Create a .env file inside backend, using .env.example as a
template. The configuration uses these environment variables:
DJANGO_SECRET_KEY=your-own-django-secret
OPENROUTESERVICE_API_KEY=your-own-openrouteservice-api-key
WEATHERAPI_API_KEY=your-own-weatherapi-api-key
Replace the placeholders with your own credentials. Use the exact
variable names expected by the backend settings and weather/routing
clients.
Security: Never commit your real .env file or expose API keys in
source code, screenshots, logs, or public documentation.
Start the Django development server:
python manage.py runserver
The backend is normally available at http://127.0.0.1:8000/.
3. Configure the frontend
Open a second terminal from the project root:
cd frontend
npm install
npm run dev
Open the local URL printed by Vite, normally http://localhost:5173/.
Ensure the frontend API configuration points to the correct backend URL.
For local development this is normally http://127.0.0.1:8000; the
deployed frontend should use the deployed backend URL.
On Windows PowerShell, use npm.cmd instead of npm if the shell
blocks the npm PowerShell script.
API Configuration
OpenRouteService
Provides driving routes and route geometry used to generate route
alternatives.
WeatherAPI
Provides forecast weather data used to evaluate conditions at route
checkpoints and estimated arrival times.
OpenStreetMap Nominatim
Resolves origin and destination place names into geographic coordinates.
OpenStreetMap
Provides map tiles displayed by the interactive route map.
API availability, provider quotas, forecast coverage, network
connectivity, and routing responses can affect results.
How It Works
1. The user enters an origin, destination, departure date and time,
   truck load weight, and checkpoint interval.
2. The backend resolves the locations and requests alternative driving
   routes.
3. Each route is sampled at checkpoints according to the selected
   interval.
4. The backend estimates arrival times at the checkpoints.
5. Weather conditions are retrieved for the checkpoints.
6. Weather and load-related risks are evaluated.
7. The application calculates route summaries and identifies a
   recommended route.
8. The frontend displays route alternatives, checkpoint weather, risk
   levels, estimated arrival times, and the interactive map.
The number of checkpoints depends on route length and the selected
checkpoint interval.
Risk Assessment
The application classifies weather conditions according to the following
assessment thresholds.
Wind Risk
  Wind speed           Risk level
  Below 25 mph         Low
  25 to below 35 mph   Moderate
  35 to below 45 mph   High
  45 to below 55 mph   Severe
  55 mph or above      No Travel
Rainfall Risk
  Rainfall intensity         Risk level
  Below 0.10 in/hr           Low
  0.10 to below 0.25 in/hr   Moderate
  0.25 to below 0.50 in/hr   High
  0.50 to 1.00 in/hr         Severe
  Above 1.00 in/hr           No Travel
Snowfall Risk
  Snowfall intensity       Risk level
  Below 0.5 in/hr          Low
  0.5 to below 1.0 in/hr   Moderate
  1.0 to below 2.0 in/hr   High
  2.0 to 3.0 in/hr         Severe
  Above 3.0 in/hr          No Travel
Truck Load Restrictions
- Wind speed of 55 mph or above results in No Travel for every load.
- Wind speed from 45 to below 55 mph combined with a load greater than
  30,000 lb results in No Travel.
- Wind speed from 35 to below 45 mph combined with a load greater than
  40,000 lb results in Severe risk.
The backend evaluates weather and load-related risk at each checkpoint
and uses the results in route risk summaries.
Route Recommendation
The assessment's intended recommendation priority is:
1. Fewest Severe-risk miles.
2. Fewest High-risk miles.
3. Lowest average risk.
4. Shortest estimated travel time.
Review the reported weather-data coverage and any No Travel conditions
when interpreting a recommendation. Routes with incomplete weather data
should not be treated as confirmed safe routes.
Weather Forecast Timeline and Heatmap
The application includes a forecast timeline slider ranging from 0 to 48
hours from departure.
The current implementation uses the selected forecast hour to filter or
highlight checkpoints according to their estimated arrival times. The
map displays route lines, checkpoint markers, weather-risk colors, and a
legend for the five risk categories.
Current limitation: The slider filters checkpoints by their
estimated arrival-time window. Moving it does not itself request a fresh
weather forecast for every slider position. The displayed heatmap and
highlighted markers depend on the available checkpoint data and the
selected time window.
Testing
Backend tests cover risk classification, threshold boundaries, and
representative weather scenarios.
From the project root, run the backend tests:
Windows PowerShell
.\\backend\\.venv\\Scripts\\python.exe backend\\manage.py test routing
Run the Django system check:
.\\backend\\.venv\\Scripts\\python.exe backend\\manage.py check
Build the frontend for production:
cd frontend
npm.cmd run build
Project Structure
WeatherTruckRouting/
├── backend/
│   ├── config/
│   ├── routing/
│   ├── .env.example
│   ├── requirements.txt
│   └── manage.py
├── frontend/
│   ├── src/
│   ├── package.json
│   └── vite.config.js
├── .gitignore
└── README.md
This is a simplified overview; additional files may be present in the
repository.
Limitations
- Weather values are forecasts and may differ from actual road
  conditions.
- Weather availability depends on the provider, departure time, and
  forecast horizon.
- Route alternatives depend on the routing provider's coverage and
  response.
- The forecast slider currently filters checkpoint highlighting by
  estimated arrival time rather than fetching a new forecast on every
  change.
- This application is a decision-support tool and does not replace
  official road closures, weather warnings, or professional driver
  judgment.
- API access limits, network errors, and missing data can affect
  results.
Security
- Keep API keys and Django secret values in environment variables.
- Do not commit real .env files or credentials.
- For production, set Django DEBUG to False and configure
  ALLOWED_HOSTS for the deployed backend hostname.
- Configure CORS so only the intended frontend origins can access the
  API.
License
No license has been specified for this repository.