const api = typeof browser !== "undefined" ? browser : chrome;

async function load() {
  const stored = await api.storage.local.get({ port: 8765, token: "" });
  document.querySelector("#token").value = stored.token;
  document.querySelector("#port").value = stored.port;
}

async function save() {
  await api.storage.local.set({
    token: document.querySelector("#token").value.trim(),
    port: Number(document.querySelector("#port").value) || 8765,
  });
  document.querySelector("#status").textContent = "Saved.";
}

document.querySelector("#save").addEventListener("click", save);
load();
