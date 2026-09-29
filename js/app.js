/* ------------------------------------------------------------------
   TECTURA — app
   Renders the index, the floating portrait, and row expansion.
------------------------------------------------------------------ */

(function () {
  const list = document.getElementById("index-list");
  const float = document.getElementById("portrait-float");
  const floatImg = document.getElementById("portrait-img");
  const floatCaption = document.getElementById("portrait-caption");

  /* Placeholder images (dummy phase) — plain SVG data URIs so the
     site works offline with no assets. Replaced by real images in
     the research phase. */
  function placeholder(label, w, h) {
    const svg =
      `<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}">` +
      `<rect width="100%" height="100%" fill="#e8e8e8"/>` +
      `<rect x="0.5" y="0.5" width="${w - 1}" height="${h - 1}" fill="none" stroke="#999" stroke-width="1"/>` +
      `<line x1="0" y1="0" x2="${w}" y2="${h}" stroke="#c8c8c8" stroke-width="1"/>` +
      `<line x1="${w}" y1="0" x2="0" y2="${h}" stroke="#c8c8c8" stroke-width="1"/>` +
      `<text x="50%" y="50%" fill="#666" font-family="Helvetica, Arial, sans-serif" font-size="10" ` +
      `letter-spacing="2" text-anchor="middle" dominant-baseline="middle">${label}</text>` +
      `</svg>`;
    return "data:image/svg+xml," + encodeURIComponent(svg);
  }

  const pad3 = (n) => String(n).padStart(3, "0");
  const years = (a) => a.yearsLabel ?? `${a.born}–${a.died ?? ""}`;

  function render() {
    ARCHITECTS.forEach((a, i) => {
      const li = document.createElement("li");
      li.className = "index-row";
      li.dataset.id = a.id;

      const head = document.createElement("div");
      head.className = "index-row-head";
      head.innerHTML = `
        <span class="row-no">${pad3(i + 1)}</span>
        <span class="row-name">${a.name}</span>
        <span class="row-years">${years(a)}</span>
        <span class="row-country">${a.country}</span>
        <span class="row-link">${
          a.link
            ? `<a href="${a.link}" target="_blank" rel="noopener">${a.linkLabel}<span class="arrow">&#8594;</span></a>`
            : `<span class="no-link">&mdash;</span>`
        }</span>`;

      const body = document.createElement("div");
      body.className = "index-row-body";

      li.appendChild(head);
      li.appendChild(body);
      list.appendChild(li);

      /* --- expansion (lazy render) --- */
      function open() {
        if (!body.dataset.rendered) {
          renderBody(body, a);
          body.dataset.rendered = "1";
        }
        li.classList.add("open");
        hideFloat();
      }
      li.openRow = open;

      head.addEventListener("click", (e) => {
        if (e.target.closest("a")) return; // let the office link work
        const isOpen = li.classList.contains("open");
        document.querySelectorAll(".index-row.open").forEach((row) => row.classList.remove("open"));
        history.replaceState(null, "", isOpen ? location.pathname : "#" + a.id);
        if (!isOpen) open();
      });

      /* --- floating portrait --- */
      head.addEventListener("mouseenter", () => {
        if (li.classList.contains("open")) return;
        floatImg.src = a.portrait || placeholder("PORTRAIT", 300, 400);
        floatCaption.textContent = a.name;
        float.classList.add("visible");
      });
      head.addEventListener("mouseleave", hideFloat);
    });
  }

  function renderBody(body, a) {
    if (!a.projects.length) {
      body.innerHTML = `
        <div class="row-body-intro">
          <span class="row-body-label">Entry</span>
          <p class="row-body-bio pending">Full entry pending research &mdash; bio, portrait and ten selected works to come.</p>
        </div>`;
      return;
    }
    const stylesLine = a.styles.join(" / ");
    const projects = a.projects
      .map(
        (p) => `
        <div class="project">
          <img class="project-image" loading="lazy"
               src="${p.image || placeholder("IMAGE", 400, 300)}" alt="${p.title}">
          <div class="project-title">${p.title}</div>
          <div class="project-year">${p.year} &mdash; ${p.location}</div>
          <div class="project-blurb">${p.blurb}</div>
        </div>`
      )
      .join("");

    body.innerHTML = `
      <div class="row-body-intro">
        <span class="row-body-label">Selected<br>Works</span>
        <p class="row-body-bio">${a.bio}</p>
        <dl class="row-body-meta">
          <div><dt>Firm</dt> <dd>${a.firm}</dd></div>
          <div><dt>Styles</dt> <dd>${stylesLine}</dd></div>
        </dl>
      </div>
      <div class="project-grid">${projects}</div>`;
  }

  function hideFloat() {
    float.classList.remove("visible");
  }

  render();

  /* deep link: #architect-id opens that row */
  if (location.hash) {
    const target = document.querySelector(`.index-row[data-id="${CSS.escape(location.hash.slice(1))}"]`);
    if (target) {
      target.openRow();
      target.scrollIntoView();
    }
  }
})();
