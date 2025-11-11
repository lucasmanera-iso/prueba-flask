document.addEventListener("DOMContentLoaded", () => {
  const data = document.getElementById("data");
  const novedades = JSON.parse(data.dataset.novedades);
  const masVendidos = JSON.parse(data.dataset.masvendidos);
  const shampoo = JSON.parse(data.dataset.shampoo);

  function getVisibleCount() {
    const w = window.innerWidth;
    if (w <= 480) return 1;   // móviles muy pequeños
    if (w <= 768) return 3;   // pantallas pequeñas / tablets
    return 5;                 // desktop
  }

  function renderProductos(lista, containerId) {
    const container = document.getElementById(containerId);
    const productoDiv = container.querySelector(".producto");
    const sumar = container.querySelector(".sumar");
    const restar = container.querySelector(".restar");

    let contador = 0;
    let visible = getVisibleCount();

    function mostrarProductos(index) {
      productoDiv.innerHTML = ""; // limpiamos el contenedor

      // asegurar visible no supere la longitud
      const realVisible = Math.min(visible, lista.length);

      for (let i = 0; i < realVisible; i++) {
        const realIndex = (index + i) % lista.length;
        const producto = lista[realIndex];

        const card = document.createElement("div");
        card.classList.add("card-container");
        card.innerHTML = `
          <p class="card-title">${producto.nombre}</p>
          <img class="card-img" src="${producto.imagen}" alt="${producto.nombre}">
          <p class="card-price">$${producto.precio}</p>
        `;
        productoDiv.appendChild(card);
      }

      // ajustar scroll horizontal para mantener la primera visible alineada (opcional)
      productoDiv.scrollLeft = 0;
    }

    mostrarProductos(contador);

    sumar.addEventListener("click", () => {
      contador = (contador + 1) % lista.length;
      mostrarProductos(contador);
    });

    restar.addEventListener("click", () => {
      contador = (contador - 1 + lista.length) % lista.length;
      mostrarProductos(contador);
    });

    // Re-render al redimensionar si cambia el número de visibles
    let lastVisible = visible;
    window.addEventListener("resize", () => {
      visible = getVisibleCount();
      if (visible !== lastVisible) {
        // ajustar contador para que no quede fuera de rango
        contador = contador % lista.length;
        mostrarProductos(contador);
        lastVisible = visible;
      }
    });
  }

  renderProductos(novedades, "carrusel-novedades");
  renderProductos(masVendidos, "carrusel-mas-vendidos");
  renderProductos(shampoo, "carrusel-shampoo");
});
