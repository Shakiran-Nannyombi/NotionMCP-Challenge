# Technical Specification: Weather Dashboard (SHIP)

**Source:** Notion page *SHIP* (child of *MCP Challenge*)  
**Last synced from workspace:** 2026-03-29  

**Notion links**

- SHIP (requirements): [https://www.notion.so/332dd76a630a80bd9658ff74cc1eea05](https://www.notion.so/332dd76a630a80bd9658ff74cc1eea05)
- Spec_DB for SHIP (task database): [https://www.notion.so/95ae67ebd4264da5b16551d7be6d34a4](https://www.notion.so/95ae67ebd4264da5b16551d7be6d34a4)

---

## 1. Project overview

Build a **weather dashboard** web application that lets users see **current conditions** and a **multi-day forecast**, with support for **geolocated “near me” weather** and **manual city search**. Data is sourced from the **OpenWeather API**. The experience must be **responsive** so it works well on **mobile and desktop**, with clear presentation of **temperature**, **humidity**, and **wind speed**, plus **forecast visuals** (icons) for at least a **five-day** horizon.

**Goals**

- Deliver accurate, timely weather information with minimal friction.
- Keep third-party usage transparent (API key handling, rate limits, error messaging).
- Maintain a simple, maintainable architecture that can grow (additional units, i18n, caching).

**Non-goals (initial release)**

- User accounts / saved locations (unless explicitly added later).
- Historical weather analytics or maps beyond what the API provides in-scope endpoints.

---

## 2. Requirements breakdown

### 2.1 Functional

| ID | Requirement | Acceptance criteria |
|----|-------------|---------------------|
| F1 | Current weather for user location | On supported browsers, prompt or use browser geolocation; fetch and display current conditions for resolved coordinates; sensible fallback if permission denied. |
| F2 | Five-day forecast with icons | Show daily (or 3-hour grouped) forecast covering **5 days**; each period shows an icon and key stats. |
| F3 | City search | User can type a city name; app resolves location via OpenWeather geocoding or forecast workflow; results update main dashboard. |
| F4 | Temperature, humidity, wind | All three visible on current weather; forecast shows at least temperature per interval/day. |
| F5 | Responsive layout | Usable on narrow (~320px) and wide viewports; touch-friendly controls on mobile. |
| F6 | OpenWeather API | All weather data fetched from documented OpenWeather endpoints; no scraping. |

### 2.2 Non-functional

| ID | Requirement | Notes |
|----|-------------|--------|
| N1 | Security | API key only on server or build-time env (recommended: small backend or serverless proxy); never commit secrets. |
| N2 | Performance | Debounced search; loading indicators; avoid redundant calls for same city/session. |
| N3 | Reliability | Handle network errors, 404/invalid city, API quota errors with human-readable messages. |
| N4 | Accessibility | Semantic HTML, labels on inputs, sufficient contrast for text over imagery if used. |

---

## 3. Technical approach

### 3.1 Architecture

- **Frontend:** SPA or lightweight framework (e.g. React, Vue, or vanilla TS) consuming a thin **API facade** that hides the OpenWeather key.
- **Backend (recommended):** Minimal HTTP service (Node/Express, Python/FastAPI, or serverless function) exposing endpoints such as `GET /weather/current`, `GET /weather/forecast`, `GET /geocode?q=` forwarding to OpenWeather with the server-held API key.
- **Location flow:** Browser **Geolocation API** → reverse geocode if needed (OpenWeather or bundled geocoding call) → current weather + forecast for coordinates. **Fallback:** default city (configurable) when geolocation is unavailable.

### 3.2 OpenWeather integration

- **Current weather:** e.g. `api.openweathermap.org/data/2.5/weather`.
- **Forecast:** e.g. `.../forecast` or One Call API if licensed—mapped to 5-day UI requirement.
- **Geocoding:** city name → lat/lon via OpenWeather geocoding API where applicable.
- Map OpenWeather **icon codes** to assets (bundled icons or OpenWeather CDN URLs).

### 3.3 UI/UX

- **Layout:** single-column stack on mobile; wider grid on desktop (current hero + forecast section).
- **States:** idle, loading, success, error (per panel or global banner).
- **Search:** input with debounce, clear action, and “use my location” control.

### 3.4 Testing strategy

- **Unit:** parsers for API responses, formatting (temp units, wind), geolocation fallback logic.
- **Integration:** mock OpenWeather responses; verify UI updates.
- **E2E (optional):** smoke test with stub server for CI.

---

## 4. Implementation tasks

The same tasks are tracked in Notion database **Spec_DB for SHIP** (see workspace).

| Order | Task Title | Summary |
|------:|------------|---------|
| 1 | Repository and environment setup | Initialize app repo, lint/format, document env vars (`OPENWEATHER_API_KEY`), CI stub. |
| 2 | OpenWeather API proxy service | Implement secure serverless/backend routes; centralize base URL, timeouts, and error mapping. |
| 3 | Geolocation and default city fallback | Wire Geolocation API; on deny/timeout, use configurable default; normalize lat/lon for API calls. |
| 4 | Current weather data module | Fetch and parse current weather; expose typed model for UI (temp, humidity, wind, icon). |
| 5 | Five-day forecast module | Fetch forecast; aggregate to 5-day presentation; attach icon IDs per interval/day. |
| 6 | City search and geocoding UX | Search input with debounce; handle ambiguous/empty results; update location context. |
| 7 | Responsive dashboard UI | Build layout, cards, forecast list/grid; mobile-first CSS or component library tokens. |
| 8 | Loading, error, and empty states | Global/inline spinners; user-facing errors for network, bad city, quota. |
| 9 | Icon and asset pipeline | Map OpenWeather codes to icons; lazy-load or sprite as needed. |
| 10 | QA pass and release checklist | Cross-browser smoke, lighthouse sanity, README runbook for keys and deploy. |

---

## 5. Open questions

- Temperature unit preference (°C vs °F) and persistence (localStorage).
- Exact OpenWeather product tier (free 5-day/3-hour forecast vs One Call).

This document is the canonical technical summary alongside the Notion *SHIP* page and **Spec_DB for SHIP** task database.
