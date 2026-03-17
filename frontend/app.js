const buttons = document.querySelectorAll(".tab-button");
const panels = document.querySelectorAll(".panel");

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

checkHealth();
