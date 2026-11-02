const $ = (selector) => document.querySelector(selector);
let token = sessionStorage.getItem("minipay_token");
let currentUser = null;

function showMessage(selector, message, success = false) {
  const el = $(selector);
  el.textContent = message || "";
  el.classList.toggle("success", success);
}

function toast(message) {
  const el = $("#toast");
  el.textContent = message;
  el.classList.remove("hidden");
  setTimeout(() => el.classList.add("hidden"), 3200);
}

async function api(path, options = {}) {
  const headers = { "Content-Type": "application/json", ...(options.headers || {}) };
  if (token) headers.Authorization = `Bearer ${token}`;
  const response = await fetch(path, { ...options, headers });
  let data = {};
  try { data = await response.json(); } catch (_) {}
  if (!response.ok) {
    const detail = typeof data.detail === "string" ? data.detail : "Si è verificato un errore";
    throw new Error(detail);
  }
  return data;
}

function setLoggedIn(loggedIn) {
  $("#auth-view").classList.toggle("hidden", loggedIn);
  $("#app-view").classList.toggle("hidden", !loggedIn);
}

document.querySelectorAll(".tab").forEach(button => {
  button.addEventListener("click", () => {
    document.querySelectorAll(".tab").forEach(tab => tab.classList.toggle("active", tab === button));
    $("#login-form").classList.toggle("hidden", button.dataset.tab !== "login");
    $("#register-form").classList.toggle("hidden", button.dataset.tab !== "register");
    showMessage("#auth-message", "");
  });
});

async function finishAuth(result) {
  token = result.token;
  currentUser = result.user;
  sessionStorage.setItem("minipay_token", token);
  $("#user-name").textContent = currentUser.name.split(" ")[0];
  setLoggedIn(true);
  await refreshDashboard();
}

$("#login-form").addEventListener("submit", async event => {
  event.preventDefault();
  showMessage("#auth-message", "");
  try {
    const result = await api("/api/login", {
      method: "POST",
      body: JSON.stringify({ email: $("#login-email").value, password: $("#login-password").value })
    });
    await finishAuth(result);
  } catch (error) { showMessage("#auth-message", error.message); }
});

$("#register-form").addEventListener("submit", async event => {
  event.preventDefault();
  showMessage("#auth-message", "");
  try {
    const result = await api("/api/register", {
      method: "POST",
      body: JSON.stringify({
        name: $("#register-name").value,
        email: $("#register-email").value,
        password: $("#register-password").value
      })
    });
    await finishAuth(result);
    toast("Account creato: hai 100,00 € virtuali demo.");
  } catch (error) { showMessage("#auth-message", error.message); }
});

$("#logout-button").addEventListener("click", () => {
  token = null;
  currentUser = null;
  sessionStorage.removeItem("minipay_token");
  setLoggedIn(false);
});

$("#payment-form").addEventListener("submit", async event => {
  event.preventDefault();
  showMessage("#payment-message", "");
  const amount = Number($("#amount").value);
  if (!Number.isFinite(amount) || amount <= 0) {
    showMessage("#payment-message", "Inserisci un importo valido.");
    return;
  }
  try {
    const result = await api("/api/payments", {
      method: "POST",
      body: JSON.stringify({
        recipient_email: $("#recipient-email").value,
        amount,
        reference: crypto.randomUUID()
      })
    });
    showMessage("#payment-message", `Pagamento completato · Riferimento ${result.id}`, true);
    $("#payment-form").reset();
    await refreshDashboard();
  } catch (error) {
    showMessage("#payment-message", error.message);
  }
});

function euro(value) {
  return Number(value).toLocaleString("it-IT", { style: "currency", currency: "EUR" });
}
function dateLabel(value) {
  return new Date(value).toLocaleString("it-IT", { dateStyle: "medium", timeStyle: "short" });
}
function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, ch => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
  })[ch]);
}

async function refreshDashboard() {
  try {
    const [me, wallet, transactions, notifications] = await Promise.all([
      api("/api/me"), api("/api/wallet"), api("/api/transactions"), api("/api/notifications")
    ]);
    currentUser = me;
    $("#user-name").textContent = me.name.split(" ")[0];
    $("#balance").textContent = Number(wallet.balance).toLocaleString("it-IT", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    renderTransactions(transactions, me.email);
    renderNotifications(notifications);
  } catch (error) {
    if (error.message.includes("Accedi") || error.message.includes("Sessione")) {
      token = null;
      sessionStorage.removeItem("minipay_token");
      setLoggedIn(false);
    } else {
      toast(error.message);
    }
  }
}

function renderTransactions(items, myEmail) {
  const container = $("#transactions");
  if (!items.length) {
    container.innerHTML = '<p class="empty">Ancora nessuna transazione. Prova a inviare un pagamento a un altro account.</p>';
    return;
  }
  container.innerHTML = items.map(item => {
    const outgoing = item.direction === "out";
    const other = outgoing ? item.recipient_email : item.sender_email;
    return `<div class="transaction">
      <span class="tx-icon ${outgoing ? "" : "in"}">${outgoing ? "↗" : "↙"}</span>
      <div class="tx-main"><b>${outgoing ? "Inviato a" : "Ricevuto da"} ${escapeHtml(other)}</b><small>${escapeHtml(dateLabel(item.created_at))} · ${escapeHtml(item.status)}</small></div>
      <span class="tx-amount ${outgoing ? "out" : "in"}">${outgoing ? "−" : "+"}${euro(item.amount)}</span>
    </div>`;
  }).join("");
}

function renderNotifications(items) {
  const container = $("#notifications");
  if (!items.length) {
    container.innerHTML = '<p class="empty">Non hai ancora notifiche.</p>';
    return;
  }
  container.innerHTML = items.map(item =>
    `<div class="notification">${escapeHtml(item.message)}<small>${escapeHtml(dateLabel(item.created_at))}</small></div>`
  ).join("");
}

async function start() {
  if (!token) { setLoggedIn(false); return; }
  try {
    currentUser = await api("/api/me");
    $("#user-name").textContent = currentUser.name.split(" ")[0];
    setLoggedIn(true);
    await refreshDashboard();
  } catch (_) {
    token = null;
    sessionStorage.removeItem("minipay_token");
    setLoggedIn(false);
  }
}
start();
