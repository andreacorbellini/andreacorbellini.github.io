document.querySelector('button.main-navbar-expand').addEventListener('click', (event) => {
  const expandedClass = 'expanded';
  let navbarItems = document.querySelector('.main-navbar-links');
  let navbarClassList = navbarItems.classList;
  if (navbarClassList.contains(expandedClass)) {
    navbarClassList.remove(expandedClass);
  } else {
    navbarClassList.add(expandedClass);
  }
});
