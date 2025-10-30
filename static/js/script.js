document.addEventListener("DOMContentLoaded", () => {
  const data = document.getElementById("data");
  const novedades = JSON.parse(data.dataset.novedades);
  const masVendidos = JSON.parse(data.dataset.masvendidos);
  const shampoo = JSON.parse(data.dataset.shampoo);
  
  function renderProductos(lista, containerId) {
    const container = document.getElementById(containerId);
    const productoDiv = container.querySelector(".producto");
    const sumar = container.querySelector(".sumar");
    const restar = container.querySelector(".restar");

    let contador = 0;
    const visible = 3; // cuántos productos mostrar a la vez

    function mostrarProductos(index) {
      productoDiv.innerHTML = ""; // limpiamos el contenedor

      for (let i = 0; i < visible; i++) {
        // calcular el índice real, envolviendo al final del array
        const realIndex = (index + i) % lista.length;
        const producto = lista[realIndex];

        const card = document.createElement("div");
        card.classList.add("card-container");
        card.innerHTML = `
          <p class="card-title">${producto.nombre}</p>
          <img class="card-img" src="${producto.imagen}" width="150">
          <p class="card-price">$${producto.precio}</p>
        `;
        productoDiv.classList.add("grid-container")
        productoDiv.appendChild(card);
      }
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
  }

  renderProductos(novedades, "carrusel-novedades");
  renderProductos(masVendidos, "carrusel-mas-vendidos");
  renderProductos(shampoo, "carrusel-shampoo");
});
