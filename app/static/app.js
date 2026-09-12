const saleForm = document.querySelector("#sale-form");
if (saleForm) {
  let firstFocus = null;
  saleForm.addEventListener("focusin", (event) => {
    if (firstFocus === null && event.target.matches("input, select, textarea")) {
      firstFocus = performance.now();
    }
  });
  saleForm.addEventListener("submit", () => {
    if (saleForm.dataset.editing !== "true" && firstFocus !== null) {
      saleForm.elements.fill_seconds.value = Math.floor((performance.now() - firstFocus) / 1000);
    }
    saleForm.querySelector('button[type="submit"]').textContent = "Evaluando…";
  });
  document.querySelector("#load-example")?.addEventListener("click", () => {
    const example = JSON.parse(document.querySelector("#sale-example").textContent);
    for (const [field, value] of Object.entries(example)) {
      saleForm.elements[field].value = value;
    }
    saleForm.elements.promise_text.focus();
    document.querySelector("#example-status").textContent = "Ejemplo sintético cargado. Puedes cambiar cualquier campo. El tiempo de llenado se mide realmente: un envío rápido puede generar una señal.";
  });
}

document.querySelectorAll("[data-copy]").forEach((button) => {
  button.addEventListener("click", async () => {
    const input = document.getElementById(button.dataset.copy);
    const status = document.querySelector("#copy-status");
    try {
      await navigator.clipboard.writeText(input.value);
      status.textContent = "Enlace copiado.";
    } catch {
      input.focus();
      input.select();
      status.textContent = "Seleccionamos el enlace. Usa la opción Copiar de tu dispositivo.";
    }
  });
});
