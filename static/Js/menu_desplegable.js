const logo = document.getElementById("profile-logo")
const menu = document.getElementById("menu-desplegable")

logo.addEventListener("click", () => {
    menu.classList.toggle("desescondido");
});