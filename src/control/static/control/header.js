function toggleMenu() {
    const menu = document.querySelector('.burger-menu');
    if (menu.style.display === 'flex') {
        menu.style.display = 'none';
    } else {
        menu.style.display = 'flex';
    }
}

// Fermer le menu si on clique en dehors
document.addEventListener('click', function(event) {
    const burgerMenu = document.querySelector('.burger-menu');
    const menuToggle = document.querySelector('.menu-toggle');
    if (!burgerMenu.contains(event.target) && !menuToggle.contains(event.target)) {
        burgerMenu.style.display = 'none';
    }
});