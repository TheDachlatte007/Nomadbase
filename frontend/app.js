const buttons = document.querySelectorAll(".tab-button");
const panels = document.querySelectorAll(".panel");
const placesGrid = document.getElementById("places-grid");
const savedGrid = document.getElementById("saved-grid");
const placesForm = document.getElementById("places-form");

for (const button of buttons) {
  button.addEventListener("click", () => {
    const { tab } = button.dataset;

    for (const candidate of buttons) {
      candidate.classList.toggle("active", candidate === button);
    }

    for (const panel of panels) {
      panel.classList.toggle("active", panel.id === `panel-${tab}`);
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

function renderPlaces(data) {
  if (!data.length) {
    placesGrid.innerHTML = '<p class="empty-state">No places matched the current filters.</p>';
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
        </article>
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
  renderPlaces(payload.data || []);
}

async function loadSavedPlaces() {
  const response = await fetch("/api/saves/");

  if (!response.ok) {
    throw new Error("Could not load saved places");
  }

  const payload = await response.json();
  renderSaved(payload.data || []);
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
      await loadSavedPlaces();
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

placesGrid.addEventListener("submit", async (event) => {
  const form = event.target.closest(".save-form");
  if (!form) {
    return;
  }

  event.preventDefault();
  await savePlace(form);
});

checkHealth();
