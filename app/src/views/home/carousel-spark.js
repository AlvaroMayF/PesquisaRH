// app/src/views/home/carousel-spark.js

document.addEventListener('DOMContentLoaded', () => {
  const track      = document.querySelector('.carousel-track');
  const slides     = Array.from(document.querySelectorAll('.carousel-slide'));
  const prevButton = document.querySelector('.carousel-button.prev');
  const nextButton = document.querySelector('.carousel-button.next');
  const indicators = Array.from(document.querySelectorAll('.indicator'));
  let currentIndex = 0;

  // Função para mover para o slide i
  function goToSlide(i) {
    currentIndex = i;
    track.style.transform = `translateX(-${100 * i}%)`;
    indicators.forEach((dot, idx) => {
      dot.classList.toggle('active', idx === i);
    });
  }

  // Eventos dos botões
  prevButton.addEventListener('click', () => {
    goToSlide((currentIndex - 1 + slides.length) % slides.length);
  });

  nextButton.addEventListener('click', () => {
    goToSlide((currentIndex + 1) % slides.length);
  });

  // Eventos dos indicadores (bolinhas)
  indicators.forEach(dot => {
    dot.addEventListener('click', () => {
      const idx = parseInt(dot.dataset.index, 10);
      goToSlide(idx);
    });
  });

  // Inicia no slide 0
  goToSlide(0);
});
