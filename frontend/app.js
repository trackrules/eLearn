const api = path => fetch('/api' + path).then(async response => {
  if (!response.ok) throw new Error((await response.text()) || response.statusText);
  return response.json();
});

const app = document.getElementById('app');
const esc = value => (value ?? '').toString().replace(/[&<>"']/g, char => ({
  '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
})[char]);
const number = value => new Intl.NumberFormat().format(Number(value || 0));
const imageSrc = image => image.local_path ? (image.local_path.startsWith('/') ? image.local_path : '/' + image.local_path) : image.image_url;
const externalLink = (url, label = 'Original source') => `<a class="source-link" href="${esc(url)}" target="_blank" rel="noopener noreferrer">${esc(label)} <span aria-hidden="true">↗</span></a>`;

function setTitle(title) {
  document.title = title ? `${title} · Multipla Workshop Library` : 'Multipla Workshop Library';
}

function setActiveNav() {
  const path = location.pathname;
  const active = path.startsWith('/components') ? 'components' : path.startsWith('/search') ? 'search' : path.startsWith('/manual') ? 'manual' : path.startsWith('/vehicles') || path.startsWith('/elearn') ? 'vehicle' : '';
  document.querySelectorAll('[data-nav]').forEach(link => link.classList.toggle('active', link.dataset.nav === active));
}

function breadcrumb(items) {
  return `<nav class="breadcrumb" aria-label="Breadcrumb">${items.map((item, index) => {
    const body = item.href ? `<a href="${esc(item.href)}">${esc(item.label)}</a>` : `<span class="${index === items.length - 1 ? 'current' : ''}">${esc(item.label)}</span>`;
    return `${index ? '<span class="separator" aria-hidden="true">/</span>' : ''}${body}`;
  }).join('')}</nav>`;
}

function sourceBreadcrumb(value, currentTitle) {
  const parts = (value || '').split(' > ').filter(Boolean);
  const items = [{ label: 'Home', href: '/' }, { label: 'Fiat Multipla', href: '/vehicles/fiat-multipla' }];
  parts.slice(2).forEach(label => items.push({ label }));
  if (items.at(-1)?.label !== currentTitle && currentTitle) items.push({ label: currentTitle });
  return breadcrumb(items);
}

function pageCard(page, options = {}) {
  const summary = (page.content_text || '').replace(/\s+/g, ' ').trim();
  const trail = page.breadcrumb || page.category || '';
  return `<article class="card result-card">
    <div class="card-top">
      <div>
        <h3 class="card-title"><a href="/elearn/${page.id}">${esc(page.title)}</a></h3>
        ${trail ? `<div class="muted">${esc(trail)}</div>` : ''}
      </div>
      ${page.category ? `<span class="badge">${esc(page.category)}</span>` : ''}
    </div>
    ${summary ? `<p class="card-summary">${esc(summary.slice(0, options.summaryLength || 300))}${summary.length > (options.summaryLength || 300) ? '…' : ''}</p>` : ''}
    <div class="meta-row"><a href="/elearn/${page.id}">Open page</a><span>·</span>${externalLink(page.source_url, 'Source')}</div>
    ${options.images?.length ? miniGallery(options.images) : ''}
  </article>`;
}

function miniGallery(images) {
  return `<div class="mini-gallery">${images.filter(image => imageSrc(image)).slice(0, 4).map(image => `<a href="${esc(imageSrc(image))}" target="_blank" rel="noopener"><img loading="lazy" src="${esc(imageSrc(image))}" alt="${esc(image.alt_text || '')}"></a>`).join('')}</div>`;
}

function imageGallery(images) {
  const usable = images.filter(image => imageSrc(image));
  if (!usable.length) return '<p class="muted">No article images are available for this page.</p>';
  return `<div class="gallery">${usable.map((image, index) => {
    const src = imageSrc(image);
    const caption = image.alt_text || `Diagram ${index + 1}`;
    return `<figure class="gallery-item"><a href="${esc(src)}" target="_blank" rel="noopener"><img loading="lazy" src="${esc(src)}" alt="${esc(caption)}"></a><figcaption title="${esc(caption)}">${esc(caption)}</figcaption></figure>`;
  }).join('')}</div>`;
}

function bindImageErrors() {
  document.querySelectorAll('.gallery-item img').forEach(image => image.addEventListener('error', () => image.closest('.gallery-item')?.classList.add('image-error'), { once: true }));
}

function formatContent(text) {
  const lines = (text || '').split(/\n+/).map(line => line.trim()).filter(Boolean);
  if (!lines.length) return '<p class="muted">No extracted article text is available.</p>';
  return lines.map((line, index) => {
    const isHeading = index > 0 && line.length < 90 && line === line.toUpperCase() && /[A-Z]/.test(line);
    const isNumbered = /^\d+\s*[,.)-]/.test(line);
    return `<p class="${isHeading ? 'article-heading' : isNumbered ? 'numbered-line' : ''}">${esc(line)}</p>`;
  }).join('');
}

function renderTables(tables) {
  if (!Array.isArray(tables) || !tables.length) return '';
  return `<h2>Tables</h2>${tables.map(table => `<div class="table-wrap"><table><tbody>${table.map((row, rowIndex) => `<tr>${row.map(cell => rowIndex === 0 ? `<th>${esc(cell)}</th>` : `<td>${esc(cell)}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`).join('')}`;
}

async function home() {
  const [vehicle, components] = await Promise.all([api('/vehicles/fiat-multipla'), api('/components')]);
  setTitle('Home');
  app.innerHTML = `<section class="hero">
    <p class="eyebrow">Phase 2A workshop archive</p>
    <h1>Fiat Multipla technical information, made searchable.</h1>
    <p class="lead">Browse the complete imported eLearn manual, follow its original hierarchy, inspect diagrams, or jump directly to component-related procedures.</p>
    <div class="header-actions"><a class="button" href="/manual/fiat-multipla">Browse the manual</a><a class="button secondary" href="/search">Search the manual</a><a class="button secondary" href="/components">Browse components</a></div>
  </section>
  <section class="stats-grid" aria-label="Library statistics">
    <div class="stat"><strong>${number(vehicle.stats.pages)}</strong><span>eLearn pages</span></div>
    <div class="stat"><strong>${number(vehicle.stats.images)}</strong><span>Image records</span></div>
    <div class="stat"><strong>${number(components.length)}</strong><span>Components</span></div>
  </section>
  <section><div class="page-header compact"><p class="eyebrow">Start exploring</p><h2>Workshop library</h2></div>
    <div class="grid">
      <a class="card" href="/vehicles/fiat-multipla"><h3>Fiat Multipla overview</h3><p class="muted">Vehicle identity, import coverage, and entry points into the manual.</p></a>
      <a class="card" href="/manual/fiat-multipla"><h3>eLearn manual tree</h3><p class="muted">Follow the original engine, section, category, index, and article hierarchy.</p></a>
      <a class="card" href="/search"><h3>Full-text eLearn search</h3><p class="muted">Find procedures, descriptions, diagnostics, technical data, and wiring pages.</p></a>
      <a class="card" href="/components"><h3>Component index</h3><p class="muted">Use familiar component names and aliases to reach matched eLearn pages.</p></a>
    </div>
  </section>`;
}

async function vehicle() {
  const data = await api('/vehicles/fiat-multipla');
  setTitle(`${data.vehicle.make} ${data.vehicle.model}`);
  app.innerHTML = `${breadcrumb([{ label: 'Home', href: '/' }, { label: 'Fiat Multipla' }])}
    <header class="page-header"><p class="eyebrow">Vehicle · eLearn code ${esc(data.vehicle.source_code)}</p><h1>${esc(data.vehicle.make)} ${esc(data.vehicle.model)}</h1><p class="lead">The Phase 2A library contains the completed Multipla eLearn import for petrol and diesel variants.</p></header>
    <section class="stats-grid">
      <div class="stat"><strong>${number(data.stats.pages)}</strong><span>Imported pages</span></div>
      <div class="stat"><strong>${number(data.stats.images)}</strong><span>Image records</span></div>
      <div class="stat"><strong>${number(data.stats.components)}</strong><span>Matched components</span></div>
    </section>
    <section class="card"><p class="eyebrow">Use the library</p><h2>Choose an entry point</h2><div class="grid">
      <a class="card" href="/manual/fiat-multipla"><h3>Browse the original manual tree</h3><p class="muted">Navigate by engine, section, workshop category, index, and article.</p></a>
      <a class="card" href="/search"><h3>Search all eLearn pages</h3><p class="muted">Search titles, breadcrumbs, categories, and extracted article content.</p></a>
      <a class="card" href="/components"><h3>Browse component matches</h3><p class="muted">Start with a component and see its related workshop pages and diagrams.</p></a>
    </div></section>`;
}

function manualPageNode(node) {
  const meta = `${node.relation ? 'Related description · ' : ''}${node.kind === 'index' ? `${number(node.child_count)} subpages` : 'Article'}${node.image_count ? ` · ${number(node.image_count)} image${node.image_count === 1 ? '' : 's'}` : ''}`;
  if (!node.children?.length) return `<a class="manual-leaf" href="/elearn/${node.id}"><span>${esc(node.title)}</span><small>${esc(meta)}</small></a>`;
  return `<details class="manual-page-node"><summary><span class="manual-node-heading"><a class="manual-node-link" href="/elearn/${node.id}">${esc(node.title)}</a><small>${esc(meta)}</small></span></summary><div class="manual-children">${node.children.map(manualPageNode).join('')}</div></details>`;
}

function manualEngine(engine) {
  return `<div class="manual-tree" data-engine-tree="${esc(engine.title)}">${engine.sections.map(section => `<details class="manual-group manual-section"><summary><span><strong>${esc(section.title)}</strong><small>${number(section.page_count)} pages</small></span></summary><div class="manual-group-body">${section.categories.map(category => `<details class="manual-group manual-category"><summary><span><strong>${esc(category.title)}</strong><small>${number(category.page_count)} pages</small></span></summary><div class="manual-pages">${category.pages.map(manualPageNode).join('')}</div></details>`).join('')}</div></details>`).join('')}</div>`;
}

async function manual() {
  setTitle('Manual');
  app.innerHTML = `${breadcrumb([{ label: 'Home', href: '/' }, { label: 'Manual' }])}
    <header class="page-header"><p class="eyebrow">Original workshop navigation</p><h1>eLearn manual browser</h1><p class="lead">Browse the imported workshop manual through its original vehicle and document hierarchy, alongside the modern search and component workflows.</p></header>
    <div class="grid"><a class="card" href="/manual/fiat-multipla"><h2>Fiat Multipla</h2><p class="muted">Choose an engine variant, then browse sections, categories, indexes, and articles.</p></a></div>`;
}

async function manualMultipla() {
  const data = await api('/manual/fiat-multipla/tree');
  setTitle('Fiat Multipla manual');
  app.innerHTML = `${breadcrumb([{ label: 'Home', href: '/' }, { label: 'Manual', href: '/manual' }, { label: 'Fiat Multipla' }])}
    <header class="page-header compact"><p class="eyebrow">${number(data.page_count)} imported manual pages</p><h1>Fiat Multipla eLearn manual</h1><p class="lead">Switch engine variants and expand the original workshop sections. Index pages remain directly accessible while exposing their imported child articles.</p></header>
    <div class="engine-switch" role="tablist" aria-label="Engine variant">${data.engines.map((engine, index) => `<button class="engine-tab${index ? '' : ' active'}" type="button" role="tab" aria-selected="${index ? 'false' : 'true'}" data-engine="${esc(engine.title)}"><strong>${esc(engine.title)}</strong><small>${number(engine.page_count)} pages</small></button>`).join('')}</div>
    <div id="manual-tree-container">${manualEngine(data.engines[0])}</div>`;
  const container = document.getElementById('manual-tree-container');
  document.querySelectorAll('.engine-tab').forEach(button => button.addEventListener('click', () => {
    document.querySelectorAll('.engine-tab').forEach(tab => { tab.classList.toggle('active', tab === button); tab.setAttribute('aria-selected', tab === button ? 'true' : 'false'); });
    const engine = data.engines.find(item => item.title === button.dataset.engine);
    container.innerHTML = manualEngine(engine);
    bindManualLinks();
  }));
  bindManualLinks();
}

function bindManualLinks() {
  document.querySelectorAll('.manual-node-link').forEach(link => link.addEventListener('click', event => event.stopPropagation()));
}

async function search() {
  const initialQuery = new URLSearchParams(location.search).get('q') || '';
  setTitle('Search');
  app.innerHTML = `${breadcrumb([{ label: 'Home', href: '/' }, { label: 'Search' }])}
    <header class="page-header compact"><p class="eyebrow">6,951 imported pages</p><h1>Search Multipla eLearn</h1><p class="lead">Search procedures, fault diagnosis, technical data, component codes, and article text.</p></header>
    <form class="search-form" id="search-form" role="search"><input class="search-input" id="search-query" name="q" value="${esc(initialQuery)}" placeholder="Try radiator fan, 5510CE, alternator…" autocomplete="off" aria-label="Search eLearn pages"><button class="button" type="submit">Search</button></form>
    <div class="results-header"><div><h2 id="results-title">Results</h2><p class="muted" id="results-meta"></p></div></div><div class="results-list" id="search-results"><div class="loading-state"><span class="spinner"></span>Searching…</div></div>`;
  const form = document.getElementById('search-form');
  const input = document.getElementById('search-query');
  const run = async () => {
    const query = input.value.trim();
    history.replaceState(null, '', query ? `/search?q=${encodeURIComponent(query)}` : '/search');
    document.getElementById('search-results').innerHTML = '<div class="loading-state"><span class="spinner"></span>Searching…</div>';
    const data = await api('/search?q=' + encodeURIComponent(query) + '&limit=30');
    const hits = data.hits || [];
    document.getElementById('results-title').textContent = query ? `Results for “${query}”` : 'Recently imported pages';
    document.getElementById('results-meta').textContent = query ? `${number(data.estimatedTotalHits ?? hits.length)} matching pages · showing ${hits.length}` : `Showing ${hits.length} pages`;
    document.getElementById('search-results').innerHTML = hits.length ? hits.map(page => pageCard(page)).join('') : '<div class="empty-state"><h3>No matching pages</h3><p>Try a shorter component name, procedure code, or system name.</p></div>';
  };
  form.addEventListener('submit', event => { event.preventDefault(); run().catch(showError); });
  await run();
}

async function elearn(id) {
  const data = await api('/elearn/' + encodeURIComponent(id));
  const page = data.page;
  const children = data.child_pages || [];
  const sourceChildren = data.source_child_links || [];
  setTitle(page.title);
  const subpages = [...children.map(child => ({ href: `/elearn/${child.id}`, label: child.title })), ...sourceChildren.map(link => ({ href: link.source_url, label: `${link.link_text || link.source_url} (source)`, external: true }))];
  app.innerHTML = `${sourceBreadcrumb(page.breadcrumb, page.title)}
    <header class="page-header compact"><div class="meta-row"><span class="badge">eLearn #${esc(page.source_id || page.id)}</span>${page.category ? `<span class="badge">${esc(page.category)}</span>` : ''}</div><h1>${esc(page.title)}</h1><div class="action-row">${externalLink(page.source_url)}<a class="source-link" href="/search?q=${encodeURIComponent(page.source_id || page.title)}">Find related pages</a></div></header>
    <div class="content-layout"><div class="content-main">
      ${data.images.length ? `<section><h2>Images <span class="count-badge">${number(data.images.length)}</span></h2>${imageGallery(data.images)}</section>` : ''}
      <article class="card article-card"><h2>Content</h2><div class="article-body">${formatContent(page.content_text)}</div>${renderTables(page.tables_json)}</article>
    </div>
    <aside class="side-panel card"><h2>Subpages ${subpages.length ? `<span class="count-badge">${number(subpages.length)}</span>` : ''}</h2>${subpages.length ? `<ul class="subpage-list">${subpages.map(child => `<li><a href="${esc(child.href)}"${child.external ? ' target="_blank" rel="noopener noreferrer"' : ''}>${esc(child.label)}</a></li>`).join('')}</ul>` : '<p class="muted">This is a leaf page with no subpages.</p>'}</aside></div>`;
  bindImageErrors();
}

async function components() {
  const rows = await api('/components');
  setTitle('Components');
  const render = filter => {
    const value = filter.toLowerCase();
    const filtered = rows.filter(component => `${component.name} ${(component.aliases || []).join(' ')}`.toLowerCase().includes(value));
    document.getElementById('component-grid').innerHTML = filtered.length ? filtered.map(component => `<a class="card component-card" href="/components/${esc(component.slug)}"><div class="card-top"><h3>${esc(component.name)}</h3><span class="count-badge">${number(component.related_pages)}</span></div><p class="muted">${number(component.related_pages)} related eLearn pages</p><div>${(component.aliases || []).slice(0, 5).map(alias => `<span class="pill">${esc(alias)}</span>`).join('')}</div></a>`).join('') : '<div class="empty-state">No components match this filter.</div>';
  };
  app.innerHTML = `${breadcrumb([{ label: 'Home', href: '/' }, { label: 'Components' }])}<header class="page-header compact"><p class="eyebrow">Component index</p><h1>Multipla components</h1><p class="lead">Open a component to see aliases and keyword-matched eLearn procedures, descriptions, and diagrams.</p></header><div class="filter-bar"><input class="filter-input" id="component-filter" placeholder="Filter components or aliases…" aria-label="Filter components"></div><div class="grid" id="component-grid"></div>`;
  document.getElementById('component-filter').addEventListener('input', event => render(event.target.value));
  render('');
}

async function component(slug) {
  const data = await api('/components/' + encodeURIComponent(slug));
  const component = data.component;
  setTitle(component.name);
  app.innerHTML = `${breadcrumb([{ label: 'Home', href: '/' }, { label: 'Components', href: '/components' }, { label: component.name }])}
    <header class="page-header compact"><p class="eyebrow">Multipla component</p><h1>${esc(component.name)}</h1><p class="lead">${data.pages.length ? `${number(data.pages.length)} related eLearn pages ranked by keyword relevance.` : 'No related eLearn pages are currently matched.'}</p><div>${data.aliases.map(alias => `<span class="pill">${esc(alias.alias)}</span>`).join('')}</div></header>
    <section><div class="results-header"><div><h2>Related eLearn pages</h2><p class="muted">Matches are ordered by title, breadcrumb, and content relevance.</p></div><span class="count-badge">${number(data.pages.length)}</span></div><div class="results-list">${data.pages.length ? data.pages.map(page => pageCard(page, { images: page.images || [] })).join('') : '<div class="empty-state">No related pages found.</div>'}</div></section>`;
}

function showError(error) {
  console.error(error);
  setTitle('Error');
  app.innerHTML = `<div class="error-state"><h1>Unable to load this page</h1><p>${esc(error.message || error)}</p><a class="button secondary" href="${esc(location.pathname + location.search)}">Try again</a></div>`;
}

async function route() {
  setActiveNav();
  const path = location.pathname;
  if (path === '/') return home();
  if (path === '/vehicles/fiat-multipla') return vehicle();
  if (path === '/manual') return manual();
  if (path === '/manual/fiat-multipla') return manualMultipla();
  if (path === '/search') return search();
  if (path === '/components') return components();
  if (path.startsWith('/components/')) return component(path.split('/').filter(Boolean).pop());
  if (path.startsWith('/elearn/')) return elearn(path.split('/').filter(Boolean).pop());
  setTitle('Not found');
  app.innerHTML = `${breadcrumb([{ label: 'Home', href: '/' }, { label: 'Not found' }])}<div class="empty-state"><h1>Page not found</h1><p>The requested workshop page does not exist.</p><a class="button secondary" href="/">Return home</a></div>`;
}

route().catch(showError);
