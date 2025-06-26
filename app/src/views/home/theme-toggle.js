document.addEventListener("DOMContentLoaded", () => {
  const toggle = document.getElementById("theme-toggle");
  const html   = document.documentElement;

  // Carrega tema salvo ou usa preferência do sistema
  let theme = localStorage.getItem("theme");
  if (!theme) {
    theme = window.matchMedia("(prefers-color-scheme: dark)").matches
      ? "dark"
      : "light";
  }
  if (theme === "dark") html.classList.add("dark");
  toggle.checked = theme === "dark";

  // Altera ao clicar
  toggle.addEventListener("change", () => {
    if (toggle.checked) {
      html.classList.add("dark");
      localStorage.setItem("theme", "dark");
    } else {
      html.classList.remove("dark");
      localStorage.setItem("theme", "light");
    }
  });
});
