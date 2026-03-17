const state = {
  places: [],
  savedPlaces: [],
  trips: [],
  expenses: [],
  visits: [],
  imports: [],
};

// --- Map setup ---
const TYPE_COLORS = {
  park: "#2d7a2d",
  restaurant: "#c86f31",
  cafe: "#8b5e3c",
  cultural: "#5b4a8a",
  attraction: "#0f5c52",
  hiking: "#1a6e4a",
  viewpoint: "#1a5c8a",
};

function typeColor(type) {
  return TYPE_COLORS[type] || "#5f6d69";
}

function makeMarkerIcon(type) {
  const color = typeColor(type);
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="34" viewBox="0 0 24 34">
    <path d="M12 0C5.4 0 0 5.4 0 12c0 9 12 22 12 22s12-13 12-22C24 5.4 18.6 0 12 0z" fill="${color}" stroke="white" stroke-width="1.5"/>
    <circle cx="12" cy="12" r="5" fill="white"/>
  </svg>`;
  return L.divIcon({
    html: svg,
    className: "",
    iconSize: [24, 34],
    iconAnchor: [12, 34],
    popupAnchor: [0, -34],
  });
}

let map = null;
const placeMarkers = new Map();

function initMap() {
  if (map) return;
  map = L.map("map-view", { zoomControl: true }).setView([20, 10], 2);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
    maxZoom: 19,
  }).addTo(map);
}

function syncMapMarkers(places) {
  if (!map) return;

  // Remove markers for places no longer in list
  const currentIds = new Set(places.map((p) => p.id));
  for (const [id, marker] of placeMarkers) {
    if (!currentIds.has(id)) {
      marker.remove();
      placeMarkers.delete(id);
    }
  }

  // Add new markers
  for (const place of places) {
    if (placeMarkers.has(place.id)) continue;
    const marker = L.marker([place.lat, place.lon], {
      icon: makeMarkerIcon(place.place_type),
      title: place.name,
    }).addTo(map);
    marker.bindPopup(
      `<strong>${escapeHtml(place.name)}</strong><br>
       <span style="color:#5f6d69;font-size:0.9em">${escapeHtml(place.place_type)}${place.region ? ` · ${escapeHtml(place.region)}` : ""}</span>
       ${place.description ? `<br><span style="font-size:0.88em">${escapeHtml(place.description)}</span>` : ""}`,
      { maxWidth: 220 }
    );
    marker.on("click", () => {
      const card = document.querySelector(`[data-place-id="${place.id}"]`);
      if (card) {
        card.closest("article")?.scrollIntoView({ behavior: "smooth", block: "nearest" });
        card.closest("article")?.classList.add("map-highlight");
        setTimeout(() => card.closest("article")?.classList.remove("map-highlight"), 1800);
      }
    });
    placeMarkers.set(place.id, marker);
  }

  // Fit map to markers if there are any
  if (places.length > 0) {
    const group = L.featureGroup([...placeMarkers.values()]);
    map.fitBounds(group.getBounds().pad(0.2));
  }
}

const buttons = document.querySelectorAll(".tab-button");
const panels = document.querySelectorAll(".panel");
const placesGrid = document.getElementById("places-grid");
const savedGrid = document.getElementById("saved-grid");
const placesForm = document.getElementById("places-form");
const tripsGrid = document.getElementById("trips-grid");
const tripForm = document.getElementById("trip-form");
const expenseForm = document.getElementById("expense-form");
const visitForm = document.getElementById("visit-form");
const preferencesForm = document.getElementById("preferences-form");
const preferencesFeedback = document.getElementById("preferences-feedback");
const expenseFeedback = document.getElementById("expense-feedback");
const visitFeedback = document.getElementById("visit-feedback");
const systemStatusCopy = document.getElementById("system-status-copy");
const systemMetrics = document.getElementById("system-metrics");
const expenseSummary = document.getElementById("expense-summary");
const expenseSummaryCopy = document.getElementById("expense-summary-copy");
const expensesGrid = document.getElementById("expenses-grid");
const visitsGrid = document.getElementById("visits-grid");
const importsList = document.getElementById("imports-list");
const importForm = document.getElementById("import-form");
const importFeedback = document.getElementById("import-feedback");

for (const button of buttons) {
  button.addEventListener("click", () => {
    const { tab } = button.dataset;

    for (const candidate of buttons) {
      candidate.classList.toggle("active", candidate === button);
    }

    for (const panel of panels) {
      panel.classList.toggle("active", panel.id === `panel-${tab}`);
    }

    if (tab === "map") {
      // Leaflet needs a moment after the panel becomes visible
      setTimeout(() => {
        initMap();
        map?.invalidateSize();
        if (state.places.length > 0) syncMapMarkers(state.places);
      }, 50);
    }
  });
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function formatDate(value) {
  if (!value) {
    return "not set";
  }

  if (typeof value === "string" && !value.includes("T")) {
    return value;
  }

  return new Date(value).toLocaleDateString("en-GB");
}

function formatDateTime(value) {
  if (!value) {
    return "not set";
  }

  return new Date(value).toLocaleString("en-GB", {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

function uniquePlaces() {
  const places = new Map();

  for (const saved of state.savedPlaces) {
    if (saved.place) {
      places.set(saved.place.id, saved.place);
    }
  }

  for (const place of state.places) {
    places.set(place.id, place);
  }

  return [...places.values()].sort((a, b) => a.name.localeCompare(b.name));
}

function syncSelectOptions() {
  const placeOptions = uniquePlaces();
  const tripOptions = [...state.trips].sort((a, b) => a.name.localeCompare(b.name));

  const optionSets = [
    {
      select: expenseForm?.elements.place_id,
      items: placeOptions,
      placeholder: "No linked place",
    },
    {
      select: visitForm?.elements.place_id,
      items: placeOptions,
      placeholder: "Choose a place",
    },
    {
      select: expenseForm?.elements.trip_id,
      items: tripOptions,
      placeholder: "No linked trip",
    },
    {
      select: visitForm?.elements.trip_id,
      items: tripOptions,
      placeholder: "No linked trip",
    },
  ];

  for (const { select, items, placeholder } of optionSets) {
    if (!select) {
      continue;
    }

    const previousValue = select.value;
    const options = [
      `<option value="">${escapeHtml(placeholder)}</option>`,
      ...items.map((item) => {
        const suffix = item.region ? ` (${item.region})` : "";
        return `<option value="${escapeHtml(item.id)}">${escapeHtml(item.name)}${escapeHtml(suffix)}</option>`;
      }),
    ];

    select.innerHTML = options.join("");
    if (previousValue && items.some((item) => item.id === previousValue)) {
      select.value = previousValue;
    }
  }
}

function renderPlaces(data) {
  if (!data.length) {
    placesGrid.innerHTML =
      '<p class="empty-state">No places matched the current filters.</p>';
    return;
  }

  placesGrid.innerHTML = data
    .map((place) => {
      const tags = Object.keys(place.tags || {});
      return `
        <article class="place-card">
          <div>
            <p class="card-eyebrow">${escapeHtml(place.region || "alpha-region")}</p>
            <h4>${escapeHtml(place.name)}</h4>
            <p class="muted">${escapeHtml(place.place_type)} · ${place.lat.toFixed(3)}, ${place.lon.toFixed(3)}</p>
          </div>
          <p>${escapeHtml(place.description || "No description yet.")}</p>
          <div class="chip-row">
            <span class="chip">${escapeHtml(place.place_type)}</span>
            ${tags.map((tag) => `<span class="chip">${escapeHtml(tag)}</span>`).join("")}
          </div>
          <form class="save-form" data-place-id="${escapeHtml(place.id)}">
            <select name="status" aria-label="Save status">
              <option value="want_to_visit">Want to visit</option>
              <option value="visited">Visited</option>
              <option value="favorite">Favorite</option>
            </select>
            <textarea name="notes" placeholder="Quick note for future you"></textarea>
            <button class="action-button" type="submit">Save place</button>
            <p class="feedback" data-feedback-for="${escapeHtml(place.id)}"></p>
          </form>
        </article>
      `;
    })
    .join("");
}

function renderSaved(data) {
  if (!data.length) {
    savedGrid.innerHTML = '<p class="empty-state">No saved places yet.</p>';
    return;
  }

  savedGrid.innerHTML = data
    .map(
      (saved) => `
        <article class="saved-card">
          <div>
            <p class="card-eyebrow">${escapeHtml(saved.status.replaceAll("_", " "))}</p>
            <h4>${escapeHtml(saved.place.name)}</h4>
            <p class="muted">${escapeHtml(saved.place.region || "alpha-region")} · ${escapeHtml(saved.place.place_type)}</p>
          </div>
          <p>${escapeHtml(saved.notes || saved.place.description || "No notes yet.")}</p>
          <div class="chip-row">
            <span class="chip">${escapeHtml(saved.place.place_type)}</span>
            <span class="chip">${escapeHtml(saved.place.source)}</span>
          </div>
          <button class="unsave-button" data-unsave-id="${escapeHtml(saved.id)}">Remove</button>
        </article>
      `
    )
    .join("");
}

function renderTrips(data) {
  if (!data.length) {
    tripsGrid.innerHTML = '<p class="empty-state">No trips yet.</p>';
    return;
  }

  tripsGrid.innerHTML = data
    .map((trip) => {
      const cities = trip.cities || [];
      return `
        <article class="trip-card">
          <div>
            <p class="card-eyebrow">${escapeHtml(trip.start_date || "no start")} to ${escapeHtml(trip.end_date || "open end")}</p>
            <h4>${escapeHtml(trip.name)}</h4>
            <p class="muted">${escapeHtml(trip.notes || "No notes yet.")}</p>
          </div>
          <div class="chip-row">
            <span class="chip">${cities.length} cities</span>
          </div>
          <ul class="cities-list">
            ${
              cities.length
                ? cities
                    .map(
                      (city) =>
                        `<li>${escapeHtml(city.name)}${city.country ? `, ${escapeHtml(city.country)}` : ""}</li>`
                    )
                    .join("")
                : "<li>No cities added yet.</li>"
            }
          </ul>
          <form class="city-form" data-trip-id="${escapeHtml(trip.id)}">
            <div class="city-form-row">
              <input name="name" type="text" placeholder="Add city" required>
              <input name="country" type="text" placeholder="Country">
            </div>
            <button class="action-button" type="submit">Add city</button>
            <p class="feedback" data-trip-feedback="${escapeHtml(trip.id)}"></p>
          </form>
        </article>
      `;
    })
    .join("");
}

function renderExpenses(data) {
  if (!data.length) {
    expensesGrid.innerHTML = '<p class="empty-state">No expenses yet.</p>';
    return;
  }

  expensesGrid.innerHTML = data
    .map(
      (expense) => `
        <article class="tracking-card">
          <div>
            <p class="card-eyebrow">${escapeHtml(expense.category)}</p>
            <h4>${escapeHtml(expense.amount.toFixed(2))} EUR</h4>
            <p class="muted">${escapeHtml(formatDate(expense.date))}${expense.trip_name ? ` · ${escapeHtml(expense.trip_name)}` : ""}</p>
          </div>
          <p>${escapeHtml(expense.description || "No description yet.")}</p>
          <div class="chip-row">
            ${expense.place_name ? `<span class="chip">${escapeHtml(expense.place_name)}</span>` : ""}
            ${expense.city ? `<span class="chip">${escapeHtml(expense.city)}</span>` : ""}
          </div>
        </article>
      `
    )
    .join("");
}

function renderVisits(data) {
  if (!data.length) {
    visitsGrid.innerHTML = '<p class="empty-state">No visits yet.</p>';
    return;
  }

  visitsGrid.innerHTML = data
    .map(
      (visit) => `
        <article class="tracking-card">
          <div>
            <p class="card-eyebrow">${escapeHtml(visit.city || "visit")}</p>
            <h4>${escapeHtml(visit.place_name)}</h4>
            <p class="muted">${escapeHtml(formatDateTime(visit.visited_at))}</p>
          </div>
          <p>${escapeHtml(visit.notes || "No notes yet.")}</p>
          <div class="chip-row">
            ${visit.trip_name ? `<span class="chip">${escapeHtml(visit.trip_name)}</span>` : ""}
          </div>
        </article>
      `
    )
    .join("");
}

function renderExpenseSummary(payload) {
  const items = payload.data || [];

  if (!items.length) {
    expenseSummaryCopy.textContent = "No tracked expenses yet.";
    expenseSummary.innerHTML = '<p class="empty-state">No category totals yet.</p>';
    return;
  }

  expenseSummaryCopy.textContent = `Tracked total: ${payload.total_amount.toFixed(2)} ${escapeHtml(payload.currency)} across ${items.length} categories.`;
  expenseSummary.innerHTML = items
    .map(
      (item) => `
        <div class="summary-item">
          <strong>${escapeHtml(item.category)}</strong>
          <span class="muted">${escapeHtml(item.total.toFixed(2))} EUR</span>
        </div>
      `
    )
    .join("");
}

function renderSystemStatus(payload) {
  systemStatusCopy.textContent =
    `System status: ${payload.status}. Database reachable: ${payload.database ? "yes" : "no"}. ` +
    `Alpha seed: ${payload.alpha_seed_enabled ? "on" : "off"}.`;
  const metrics = payload.metrics || {};
  systemMetrics.innerHTML = Object.entries(metrics)
    .map(
      ([label, value]) =>
        `<span class="chip">${escapeHtml(label)}: ${escapeHtml(value)}</span>`
    )
    .join("");
}

function renderImports(data) {
  if (!data.length) {
    importsList.innerHTML = '<p class="empty-state">No import regions recorded yet.</p>';
    return;
  }

  importsList.innerHTML = data
    .map(
      (item) => `
        <div class="import-item">
          <div>
            <strong>${escapeHtml(item.region)}</strong>
            <p class="muted">${escapeHtml(item.place_count)} places</p>
          </div>
          <div class="chip-row">
            ${(item.sources || []).map((source) => `<span class="chip">${escapeHtml(source)}</span>`).join("")}
          </div>
        </div>
      `
    )
    .join("");
}

async function loadPlaces() {
  const formData = new FormData(placesForm);
  const params = new URLSearchParams();

  for (const [key, value] of formData.entries()) {
    if (value) {
      params.set(key, value);
    }
  }

  const suffix = params.toString() ? `?${params.toString()}` : "";
  const response = await fetch(`/api/map/places${suffix}`);

  if (!response.ok) {
    throw new Error("Could not load places");
  }

  const payload = await response.json();
  state.places = payload.data || [];
  renderPlaces(state.places);
  syncSelectOptions();
  initMap();
  syncMapMarkers(state.places);
}

async function loadSavedPlaces() {
  const response = await fetch("/api/saves/");

  if (!response.ok) {
    throw new Error("Could not load saved places");
  }

  const payload = await response.json();
  state.savedPlaces = payload.data || [];
  renderSaved(state.savedPlaces);
  syncSelectOptions();
}

async function loadTrips() {
  const response = await fetch("/api/trips/");

  if (!response.ok) {
    throw new Error("Could not load trips");
  }

  const payload = await response.json();
  state.trips = payload.data || [];
  renderTrips(state.trips);
  syncSelectOptions();
}

async function loadExpenses() {
  const response = await fetch("/api/tracking/expenses");

  if (!response.ok) {
    throw new Error("Could not load expenses");
  }

  const payload = await response.json();
  state.expenses = payload.data || [];
  renderExpenses(state.expenses);
}

async function loadVisits() {
  const response = await fetch("/api/tracking/visits");

  if (!response.ok) {
    throw new Error("Could not load visits");
  }

  const payload = await response.json();
  state.visits = payload.data || [];
  renderVisits(state.visits);
}

async function loadExpenseSummary() {
  const response = await fetch("/api/tracking/expenses/summary");

  if (!response.ok) {
    throw new Error("Could not load expense summary");
  }

  const payload = await response.json();
  renderExpenseSummary(payload);
}

async function loadPreferences() {
  const response = await fetch("/api/admin/preferences");

  if (!response.ok) {
    throw new Error("Could not load preferences");
  }

  const payload = await response.json();
  const data = payload.data || {};
  preferencesForm.elements.interests.value = (data.interests || []).join(", ");
  preferencesForm.elements.dietary_filters.value = (data.dietary_filters || []).join(", ");
  preferencesForm.elements.budget_level.value = data.budget_level || "balanced";
}

async function loadSystemStatus() {
  const response = await fetch("/api/admin/status");

  if (!response.ok) {
    throw new Error("Could not load system status");
  }

  const payload = await response.json();
  renderSystemStatus(payload);
}

async function loadImports() {
  const response = await fetch("/api/admin/imports");

  if (!response.ok) {
    throw new Error("Could not load imports");
  }

  const payload = await response.json();
  state.imports = payload.data || [];
  renderImports(state.imports);
}

async function savePlace(form) {
  const placeId = form.dataset.placeId;
  const formData = new FormData(form);
  const feedback = document.querySelector(`[data-feedback-for="${placeId}"]`);

  feedback.textContent = "Saving...";

  const response = await fetch("/api/saves/", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      place_id: placeId,
      status: formData.get("status"),
      notes: formData.get("notes") || null,
    }),
  });

  if (!response.ok) {
    feedback.textContent = "Save failed";
    return;
  }

  feedback.textContent = "Saved";
  await loadSavedPlaces();
}

async function createTrip() {
  const formData = new FormData(tripForm);
  const response = await fetch("/api/trips/", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      name: formData.get("name"),
      start_date: formData.get("start_date") || null,
      end_date: formData.get("end_date") || null,
      notes: formData.get("notes") || null,
    }),
  });

  if (!response.ok) {
    return;
  }

  tripForm.reset();
  await loadTrips();
}

async function addCity(form) {
  const tripId = form.dataset.tripId;
  const formData = new FormData(form);
  const feedback = document.querySelector(`[data-trip-feedback="${tripId}"]`);
  feedback.textContent = "Adding...";

  const response = await fetch(`/api/trips/${tripId}/cities`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      name: formData.get("name"),
      country: formData.get("country") || null,
    }),
  });

  if (!response.ok) {
    feedback.textContent = "Add failed";
    return;
  }

  feedback.textContent = "Added";
  await loadTrips();
}

async function recordExpense() {
  const formData = new FormData(expenseForm);
  expenseFeedback.textContent = "Saving...";

  const response = await fetch("/api/tracking/expenses", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      amount: Number(formData.get("amount")),
      category: formData.get("category"),
      date: formData.get("date") || null,
      trip_id: formData.get("trip_id") || null,
      place_id: formData.get("place_id") || null,
      description: formData.get("description") || null,
    }),
  });

  if (!response.ok) {
    expenseFeedback.textContent = "Save failed";
    return;
  }

  expenseForm.reset();
  syncSelectOptions();
  expenseFeedback.textContent = "Recorded";
  await Promise.all([loadExpenses(), loadExpenseSummary(), loadSystemStatus()]);
}

async function logVisit() {
  const formData = new FormData(visitForm);
  visitFeedback.textContent = "Saving...";

  const visitedAt = formData.get("visited_at");
  const response = await fetch("/api/tracking/visits", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      place_id: formData.get("place_id"),
      trip_id: formData.get("trip_id") || null,
      visited_at: visitedAt ? new Date(visitedAt).toISOString() : null,
      notes: formData.get("notes") || null,
    }),
  });

  if (!response.ok) {
    visitFeedback.textContent = "Save failed";
    return;
  }

  visitForm.reset();
  syncSelectOptions();
  visitFeedback.textContent = "Logged";
  await Promise.all([loadVisits(), loadSystemStatus()]);
}

async function savePreferences() {
  preferencesFeedback.textContent = "Saving...";
  const interests = preferencesForm.elements.interests.value
    .split(",")
    .map((value) => value.trim())
    .filter(Boolean);
  const dietaryFilters = preferencesForm.elements.dietary_filters.value
    .split(",")
    .map((value) => value.trim())
    .filter(Boolean);

  const response = await fetch("/api/admin/preferences", {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      interests,
      dietary_filters: dietaryFilters,
      budget_level: preferencesForm.elements.budget_level.value,
    }),
  });

  preferencesFeedback.textContent = response.ok ? "Saved" : "Save failed";
}

async function checkHealth() {
  const statusPill = document.getElementById("status-pill");
  const healthTitle = document.getElementById("health-title");
  const healthCopy = document.getElementById("health-copy");

  try {
    const response = await fetch("/api/health", {
      headers: { Accept: "application/json" },
    });

    const payload = await response.json();

    if (response.ok && payload.database) {
      statusPill.textContent = "API reachable";
      statusPill.style.background = "#d7ebe7";
      statusPill.style.color = "#0f5c52";
      healthTitle.textContent = "Backend is responding.";
      healthCopy.textContent =
        "FastAPI answered through the frontend proxy and reported database connectivity.";
      await loadPlaces();
      await Promise.all([
        loadSavedPlaces(),
        loadTrips(),
        loadExpenses(),
        loadVisits(),
        loadExpenseSummary(),
        loadPreferences(),
        loadSystemStatus(),
        loadImports(),
      ]);
      return;
    }

    statusPill.textContent = "API degraded";
    statusPill.style.background = "#f7ddcf";
    statusPill.style.color = "#8f3f10";
    healthTitle.textContent = "Backend responded with a warning.";
    healthCopy.textContent =
      "The endpoint answered, but the database check did not come back healthy yet.";
  } catch (error) {
    statusPill.textContent = "API offline";
    statusPill.style.background = "#f7ddcf";
    statusPill.style.color = "#8f3f10";
    healthTitle.textContent = "Health check not reachable yet.";
    healthCopy.textContent =
      "This usually means the API container is not up yet or the reverse proxy cannot reach it.";
  }
}

placesForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  await loadPlaces();
});

document.getElementById("near-me-btn").addEventListener("click", async () => {
  const btn = document.getElementById("near-me-btn");
  if (!navigator.geolocation) {
    btn.textContent = "Not supported";
    return;
  }

  btn.textContent = "Locating...";
  btn.disabled = true;

  navigator.geolocation.getCurrentPosition(
    async (pos) => {
      const { latitude, longitude } = pos.coords;

      try {
        initMap();
        map.setView([latitude, longitude], 14);

        // User location marker
        L.circleMarker([latitude, longitude], {
          radius: 8,
          fillColor: "#0f5c52",
          color: "#fff",
          weight: 2,
          fillOpacity: 0.9,
        })
          .addTo(map)
          .bindPopup("You are here")
          .openPopup();

        const response = await fetch(
          `/api/map/places/nearby?lat=${latitude}&lon=${longitude}&radius_m=2500&limit=20`
        );
        if (!response.ok) throw new Error("Nearby request failed");

        const payload = await response.json();
        const nearby = payload.data || [];
        state.places = nearby;
        renderPlaces(nearby);
        syncSelectOptions();
        syncMapMarkers(nearby);

        btn.textContent = `${nearby.length} nearby`;
      } catch {
        btn.textContent = "Failed";
      } finally {
        btn.disabled = false;
      }
    },
    () => {
      btn.textContent = "Denied";
      btn.disabled = false;
    },
    { timeout: 8000 }
  );
});

placesGrid.addEventListener("submit", async (event) => {
  const form = event.target.closest(".save-form");
  if (!form) {
    return;
  }

  event.preventDefault();
  await savePlace(form);
});

tripForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  await createTrip();
});

tripsGrid.addEventListener("submit", async (event) => {
  const form = event.target.closest(".city-form");
  if (!form) {
    return;
  }

  event.preventDefault();
  await addCity(form);
});

expenseForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  await recordExpense();
});

visitForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  await logVisit();
});

preferencesForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  await savePreferences();
});

importForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const formData = new FormData(importForm);
  const city = formData.get("city");
  const country = formData.get("country") || null;

  importFeedback.textContent = `Importing ${city}... (this can take 30–60 seconds)`;
  const submitBtn = importForm.querySelector("button[type=submit]");
  submitBtn.disabled = true;

  try {
    const response = await fetch("/api/admin/imports", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ city, country }),
    });

    const payload = await response.json();

    if (!response.ok) {
      importFeedback.textContent = `Error: ${payload.detail || "Import failed"}`;
      return;
    }

    importFeedback.textContent = `Done — imported ${payload.imported} places for ${payload.region}.`;
    importForm.reset();
    await Promise.all([loadImports(), loadPlaces(), loadSystemStatus()]);
  } catch {
    importFeedback.textContent = "Import request failed.";
  } finally {
    submitBtn.disabled = false;
  }
});

savedGrid.addEventListener("click", async (event) => {
  const btn = event.target.closest("[data-unsave-id]");
  if (!btn) return;

  const savedId = btn.dataset.unsaveId;
  btn.textContent = "Removing...";
  btn.disabled = true;

  const response = await fetch(`/api/saves/${savedId}`, { method: "DELETE" });
  if (response.ok) {
    await loadSavedPlaces();
  } else {
    btn.textContent = "Failed";
    btn.disabled = false;
  }
});

checkHealth();
