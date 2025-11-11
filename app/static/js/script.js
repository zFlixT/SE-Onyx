// =============================================
// SEAC — Sistema Experto Asistente de Compras
// Unificado con login, registro, feedback, favoritos
// y efecto visual de guardado ✨
// =============================================

// ---------- SESIÓN ----------
function setSession(data) {
  localStorage.setItem("user_id", data.user_id);
  localStorage.setItem("user_email", data.email);
  localStorage.setItem(
    "user_name",
    `${(data.first_name || "").trim()} ${(data.last_name || "").trim()}`.trim()
  );
}

function clearSession() {
  localStorage.removeItem("user_id");
  localStorage.removeItem("user_email");
  localStorage.removeItem("user_name");
}

function getSession() {
  return {
    userId: localStorage.getItem("user_id"),
    userEmail: localStorage.getItem("user_email"),
    userName: localStorage.getItem("user_name"),
  };
}

// ---------- LOGIN ----------
async function handleLogin(email, password, msgEl) {
  try {
    const res = await fetch(
      `/users/login?email=${encodeURIComponent(email)}&password=${encodeURIComponent(password)}`,
      { method: "POST" }
    );
    const data = await res.json();
    if (res.ok && data.ok) {
      setSession({
        user_id: data.user_id,
        email: email,
        first_name: data.first_name || "",
        last_name: data.last_name || ""
      });
      msgEl.textContent = "Inicio de sesión exitoso ✅";
      msgEl.style.color = "green";
      setTimeout(() => (window.location.href = "/index"), 800);
    } else {
      msgEl.textContent = data.detail || "Error al iniciar sesión.";
      msgEl.style.color = "red";
    }
  } catch {
    msgEl.textContent = "Error de conexión con el servidor.";
    msgEl.style.color = "red";
  }
}

// ---------- REGISTRO ----------
async function handleRegister(first_name, last_name, email, password, msgEl) {
  try {
    const res = await fetch(
      `/users/register?email=${encodeURIComponent(email)}&password=${encodeURIComponent(password)}&first_name=${encodeURIComponent(first_name)}&last_name=${encodeURIComponent(last_name)}`,
      { method: "POST" }
    );
    const data = await res.json();
    if (res.ok && data.ok) {
      setSession(data);
      msgEl.textContent = "Cuenta creada correctamente ✅";
      msgEl.style.color = "green";
      setTimeout(() => (window.location.href = "/index"), 800);
    } else {
      msgEl.textContent = data.detail || "Error al registrar usuario.";
      msgEl.style.color = "red";
    }
  } catch {
    msgEl.textContent = "Error de conexión con el servidor.";
    msgEl.style.color = "red";
  }
}

// ---------- SALUDO EN INDEX ----------
function loadWelcome() {
  const { userId, userName, userEmail } = getSession();
  if (!userId) {
    window.location.href = "/bienvenida";
  } else {
    const el = document.getElementById("userWelcome");
    if (el)
      el.textContent = `👋 Bienvenido, ${
        userName && userName.trim() ? userName : userEmail || "usuario"
      }`;
  }
}

// ---------- LOGOUT ----------
function initLogout() {
  const btn = document.getElementById("logoutBtn");
  if (!btn) return;
  btn.addEventListener("click", () => {
    clearSession();
    alert("Sesión cerrada correctamente 👋");
    window.location.href = "/";
  });
}

// ---------- FAVORITOS ----------
async function loadFavorites() {
  const { userId } = getSession();
  const section = document.getElementById("favoritesSection");
  const container = document.getElementById("favoritesContainer");
  if (!section || !container) return;

  section.style.display = "block";
  container.innerHTML = "<p class='text-muted'>Cargando favoritos...</p>";

  try {
    const res = await fetch(`/users/${userId}/favorites`);
    const data = await res.json();

    if (data.ok && data.favorites.length > 0) {
      container.innerHTML = "";
      data.favorites.forEach((prod) => {
        container.innerHTML += `
          <div class="col-md-4">
            <div class="card fav-card p-3">
              <h5 class="text-primary fw-bold mb-2">${prod.brand || "Marca N/D"} ${prod.name || ""}</h5>
              <p class="mb-1"><strong>Procesador:</strong> ${prod.cpu || "N/D"}</p>
              <p class="mb-1"><strong>Tarjeta gráfica:</strong> ${prod.gpu || "N/D"}</p>
              <p class="mb-1"><strong>RAM:</strong> ${prod.ram || "N/D"} &nbsp; | &nbsp; <strong>Almacenamiento:</strong> ${prod.storage || "N/D"}</p>
              <p class="mb-1"><strong>SO:</strong> ${prod.os || "N/D"}</p>
              <p class="fw-bold text-primary mt-2">$${parseFloat(prod.price || prod.precio || 0).toFixed(2)}</p>
              <div class="d-flex justify-content-end">
                <button class="btn btn-outline-danger btn-sm" onclick="removeFavorite('${prod.id}')">🗑️ Eliminar</button>
              </div>
            </div>
          </div>
        `;
      });
    } else {
      container.innerHTML =
        "<p class='text-muted'>No tienes productos favoritos aún.</p>";
    }
  } catch {
    container.innerHTML = "<p class='text-danger'>Error al cargar los favoritos.</p>";
  }
}

async function removeFavorite(productId) {
  const { userId } = getSession();
  if (!confirm("¿Eliminar este producto de tus favoritos?")) return;
  const res = await fetch(`/users/${userId}/favorites/${productId}`, { method: "DELETE" });
  if (res.ok) {
    mostrarToast("Producto eliminado de favoritos", "danger");
    loadFavorites();
  }
}

// ---------- EFECTO VISUAL (TOAST + GUARDADO) ----------
function mostrarToast(mensaje, tipo = "success") {
  const toast = document.createElement("div");
  toast.className = `toast align-items-center text-white bg-${tipo} border-0 position-fixed bottom-0 end-0 m-3 p-3 fade show`;
  toast.style.zIndex = 2000;
  toast.innerHTML = `
    <div class="d-flex">
      <div class="toast-body">${mensaje}</div>
      <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
    </div>
  `;
  document.body.appendChild(toast);
  setTimeout(() => toast.remove(), 3000);
}

// ---------- INFERENCIA ----------
const form = document.getElementById("consultaForm");
const resultsDiv = document.getElementById("results");

let currentSessionId = null;
let currentUso = null;

if (form) {
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    resultsDiv.innerHTML = "<p>🔍 Buscando recomendaciones...</p>";

    const uso = document.getElementById("uso").value.trim();
    const gama = document.getElementById("gama").value.trim();
    const presupuesto =
      parseFloat(document.getElementById("presupuesto").value) || 0;
    const marca = document.getElementById("marca").value.trim();

    currentUso = uso;

// === VALIDACIÓN COMBINADA DE PRESUPUESTO, USO Y GAMA ===
const usoNormalizado = uso.toLowerCase();
let tipoUso = "";

if (usoNormalizado.includes("juego") || usoNormalizado.includes("gaming")) tipoUso = "gaming";
else if (usoNormalizado.includes("oficina") || usoNormalizado.includes("trabajo") || usoNormalizado.includes("estudio") || usoNormalizado.includes("universidad"))
  tipoUso = "oficina";
else if (usoNormalizado.includes("edicion") || usoNormalizado.includes("video") || usoNormalizado.includes("diseno"))
  tipoUso = "edicion";
else if (usoNormalizado.includes("program") || usoNormalizado.includes("dev") || usoNormalizado.includes("codigo"))
  tipoUso = "programacion";
else tipoUso = "basico";

const rangosGama = {
  baja:  { min: 150, max: 450 },
  media: { min: 451, max: 900 },
  alta:  { min: 901, max: 2000 }
};

const gamaSel = (gama || "").toLowerCase();
let mensajes = [];

// ---- Validación por uso ----
if (tipoUso === "gaming" && presupuesto < 500)
  mensajes.push("⚠️ El presupuesto indicado parece insuficiente para un equipo de gaming.");
else if (tipoUso === "edicion" && presupuesto < 400)
  mensajes.push("⚠️ El presupuesto indicado es bajo para tareas de edición o diseño.");
else if (tipoUso === "programacion" && presupuesto < 350)
  mensajes.push("⚠️ El presupuesto puede ser limitado para programación o desarrollo.");
else if (tipoUso === "oficina" && presupuesto < 250)
  mensajes.push("⚠️ Puede que el presupuesto sea demasiado bajo para un equipo de oficina.");
else if (tipoUso === "basico" && presupuesto < 180)
  mensajes.push("⚠️ Presupuesto muy bajo incluso para tareas básicas.");

// ---- Validación por gama ----
if (gamaSel && rangosGama[gamaSel]) {
  const { min, max } = rangosGama[gamaSel];
  if (presupuesto < min || presupuesto > max) {
    mensajes.push(
      `⚠️ El presupuesto $${presupuesto} no coincide con la gama “${gamaSel}”.\n\n` +
      `• Gama baja:  $${rangosGama.baja.min} – $${rangosGama.baja.max}\n` +
      `• Gama media: $${rangosGama.media.min} – $${rangosGama.media.max}\n` +
      `• Gama alta:  $${rangosGama.alta.min} – $${rangosGama.alta.max}`
    );
  }
} else if (gamaSel && !rangosGama[gamaSel]) {
  mensajes.push("⚠️ Debes seleccionar una gama válida (baja, media o alta).");
}

// ---- Mostrar una sola alerta si hay algo que advertir ----
if (mensajes.length) {
  alert(mensajes.join("\n\n") + "\n\nEl sistema ajustará automáticamente los parámetros para ofrecerte opciones viables.");
}

    const query = {
      uso,
      gama,
      presupuesto,
      preferencias: { marca },
      top_k: 3,
    };

    try {
      const res = await fetch("/infer", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(query),
      });
      const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Error desconocido");

        // ⬇️ INSERTA ESTE BLOQUE AQUÍ (antes de llamar a renderResults)
        const { userId } = getSession();
        let favSet = new Set();
        try {
          const fr = await fetch(`/users/${userId}/favorites`);
          const fj = await fr.json();
          if (fj.ok && Array.isArray(fj.favorites)) {
            favSet = new Set(fj.favorites.map(x => x.id));
          }
        } catch (e) {
        }
        renderResults(data, favSet);
    } catch (err) {
      resultsDiv.innerHTML = `<div class="alert alert-warning">⚠️ ${err.message}</div>`;
    }
  });
}

// ⚠️ Reemplaza tu renderResults completo por este:
async function renderResults(data) {
  resultsDiv.innerHTML = '';
  if (!Array.isArray(data) || data.length === 0) {
    resultsDiv.innerHTML = '<p>No se encontraron recomendaciones para esos parámetros.</p>';
    return;
  }

  currentSessionId = data[0]?.session_id || null;

  // --- Filtrar tarjeta de "Ajuste Automático del Sistema"
  const esAjuste = (item) => {
    const n = (item?.product?.name || '').toLowerCase();
    const b = (item?.product?.brand || '').toLowerCase();
    return b === 'seac' || n.includes('ajuste automático del sistema');
  };
  const ajusteItem = data.find(esAjuste);
  if (ajusteItem) {
    const nota = (Array.isArray(ajusteItem.reasons) && ajusteItem.reasons[0]) ? ajusteItem.reasons[0] : '';
    const alert = document.createElement('div');
    alert.className = 'alert alert-info d-flex align-items-center gap-2';
    alert.innerHTML = `<span>${nota}</span>`;
    resultsDiv.appendChild(alert);
  }
  const itemsVisibles = data.filter(item => !esAjuste(item));
  if (itemsVisibles.length === 0) return;

  // 🔎 Cargar favoritos del usuario UNA SOLA VEZ
  const { userId } = getSession();
  let favSet = new Set();
  try {
    const resFav = await fetch(`/users/${userId}/favorites`);
    const dataFav = await resFav.json();
    if (dataFav.ok && Array.isArray(dataFav.favorites)) {
      dataFav.favorites.forEach(f => { if (f.id) favSet.add(String(f.id)); });
    }
  } catch {
    console.warn("⚠️ No se pudieron cargar favoritos previos.");
  }

  itemsVisibles.forEach(item => {
    const p = item.product;
    const descripcion = Array.isArray(item.reasons) && item.reasons.length
      ? item.reasons[0]
      : 'Sin descripción disponible.';

    const yaFavorito = favSet.has(String(p.id || ""));

    const card = document.createElement('div');
    card.className = 'card mb-3 shadow-sm p-3';
    card.dataset.productId = p.id || "";

    // 👇 Todo el HTML del card en UNA SOLA asignación (sin +=)
    card.innerHTML = `
      <h5 class="text-primary fw-bold mb-2">${p.name || "Producto sin nombre"}</h5>
      <p class="mb-1">
        <strong>Marca:</strong> ${p.brand || "N/D"} &nbsp; | &nbsp;
        <strong>Precio:</strong> $${p.price || p.precio || 0}
      </p>
      <p class="mb-1">
        <strong>Procesador:</strong> ${p.cpu || "N/D"} &nbsp; | &nbsp;
        <strong>Tarjeta gráfica:</strong> ${p.gpu || "N/D"}
      </p>
      <p class="mb-1">
        <strong>RAM:</strong> ${p.ram || "N/D"} &nbsp; | &nbsp;
        <strong>Almacenamiento:</strong> ${p.storage || "N/D"} &nbsp; | &nbsp;
        <strong>SO:</strong> ${p.os || "N/D"}
      </p>
      <p class="text-muted mb-2">${descripcion}</p>
      <div class="d-flex gap-2 mt-2">
        <button class="btn ${yaFavorito ? "btn-warning" : "btn-outline-warning"} btn-sm btn-feedback fade-color"
          data-rate="1" ${yaFavorito ? "disabled" : ""}>
          ${yaFavorito ? "✔️ Ya en favoritos" : "⭐ Agregar a favoritos"}
        </button>
      </div>
    `;

    const btn = card.querySelector('.btn-feedback');
    if (!yaFavorito) {
      btn.addEventListener('click', async () => {
        const rating = 1;
        // ⚠️ Si tu enviarFeedback espera 'id', pásale p.id; si espera el objeto, pásale p.
        await enviarFeedback(currentSessionId, p, rating, btn);
        btn.textContent = "✔️ Ya en favoritos";
        btn.classList.remove("btn-outline-warning");
        btn.classList.add("btn-warning");
        btn.disabled = true;
      });
    }

    resultsDiv.appendChild(card);
  });
}

// ---------- FEEDBACK ----------
async function enviarFeedback(session_id, product, rating, buttonEl) {
  const { userId } = getSession();

  // 🟢 Estructura simple alineada con el nuevo modelo de FastAPI
  const body = {
    session_id: session_id || "web-session",
    product_name: product.name || product.modelo || "Desconocido",
    brand: product.brand || product.marca || "(desconocida)",
    rating,
    notes: "Me gusta",
    user_id: userId || null,
    cpu: product.cpu || product.procesador || "",
    gpu: product.gpu || product.tarjeta_grafica || "",
    ram: product.ram || product.memoria_ram || "",
    storage: product.storage || product.almacenamiento || "",
    os: product.os || product.sistema_operativo || "",
    price: Number(product.price ?? product.precio ?? 0)
  };

  const original = buttonEl.className;
  const toSuccess = () => {
    buttonEl.textContent = "✔️ Ya en favoritos";
    buttonEl.classList.remove("btn-outline-warning");
    buttonEl.classList.add("btn-warning");
    buttonEl.disabled = true;
    mostrarToast("Producto guardado en favoritos ⭐", "success");
  };
  const revert = () => {
    buttonEl.className = original;
    buttonEl.disabled = false;
  };

  try {
    toSuccess();
    const r = await fetch("/feedback", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!r.ok) {
      const j = await r.json().catch(() => ({ detail: "Error" }));
      throw new Error(j.detail || "Error en feedback");
    }
  } catch (err) {
    buttonEl.classList.remove("btn-outline-warning", "btn-warning");
    buttonEl.classList.add("btn-danger");
    mostrarToast("❌ Error enviando feedback", "danger");
    setTimeout(revert, 1200);
  }
}

// ---------- EVENTOS GLOBALES ----------
document.addEventListener("DOMContentLoaded", () => {
  const favBtn = document.getElementById("verFavoritos");
  if (favBtn) favBtn.addEventListener("click", loadFavorites);
  loadWelcome();
  initLogout();
});