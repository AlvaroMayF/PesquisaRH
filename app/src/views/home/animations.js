document.addEventListener('DOMContentLoaded', () => {

  // Animação de Fade-in ao Rolar a Página
  // Esta função observa os elementos e adiciona uma classe quando eles se tornam visíveis
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      // Se o elemento estiver na tela (intersecting)
      if (entry.isIntersecting) {
        // Adiciona a classe que ativa a animação CSS
        entry.target.classList.add('is-visible');
      }
    });
  }, {
    threshold: 0.1 // A animação começa quando 10% do elemento está visível
  });

  // Seleciona todas as seções que você quer animar
  const sectionsToAnimate = document.querySelectorAll('.carousel-card, .quick-access-section, .indicators-section, .birthday-table');

  // Para cada seção, aplica a classe de estado inicial e começa a observar
  sectionsToAnimate.forEach(section => {
    section.classList.add('fade-in-section');
    observer.observe(section);
  });

});