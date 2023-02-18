document.querySelectorAll('details').forEach((elem) => {
  // Give each details element an ID derived from the text of the summary
  if (!elem.id) {
    const base = elem.querySelector('summary').innerText
                                              .toLowerCase()
                                              .replaceAll(/[^a-zA-Z0-9\s-]/g, '')
                                              .replaceAll(/\s+/g, '-');
    let id = base;
    let counter = 0;
    while (document.getElementById(id) !== null) {
      counter += 1;
      id = `${base}_${counter}`;
    }
    elem.id = id;
  }

  // Remember if details were expanded or not across sessions
  elem.addEventListener('toggle', (event) => {
    const elem = event.target;
    if (elem.open) {
      localStorage.setItem(elem.id, 'open');
    } else {
      localStorage.removeItem(elem.id);
    }
  });

  // Expand the details if the current URL points to it, or if it was opened in
  // a previous session
  if (location.hash === `#${elem.id}` || localStorage.getItem(elem.id) === 'open') {
    elem.open = true;
  }
});
