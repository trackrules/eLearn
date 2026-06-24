const api = path => fetch('/api' + path).then(async response => {
  if (!response.ok) throw new Error((await response.text()) || response.statusText);
  return response.json();
});
const discApi = path => fetch('/disc-api' + path).then(async response => {
  const body = await response.text();
  let data;
  try { data = body ? JSON.parse(body) : {}; } catch { data = { detail: body }; }
  if (!response.ok) throw new Error(data?.error?.message || data?.detail || response.statusText);
  return data;
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
  const active = path.startsWith('/disc') ? 'disc' : path.startsWith('/components') ? 'components' : path.startsWith('/search') ? 'search' : path.startsWith('/manual') ? 'manual' : path.startsWith('/vehicles') || path.startsWith('/elearn') ? 'vehicle' : '';
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

function discNotice() {
  return `<div class="disc-notice" role="status"><strong>Disc Preview / Staged Source / Not Production</strong><span>This area reads the isolated original-disc staging data. Current web-backed workshop pages remain separate.</span></div>`;
}

function discBreadcrumb(items = []) {
  return breadcrumb([{ label: 'Home', href: '/' }, { label: 'Disc Preview', href: '/disc' }, ...items]);
}

function applicabilitySummary(applicability) {
  const labels = { production: 'Production', validity: 'Engine / validity', codep: 'Equipment' };
  const rows = Object.entries(labels).map(([key, label]) => {
    const values = applicability?.[key] || [];
    return `<div class="applicability-row"><strong>${label}</strong><span>${values.length ? values.map(item => esc(item.name || item.code || item.id)).join(', ') : 'All / unrestricted'}</span></div>`;
  });
  return `<div class="applicability-list">${rows.join('')}</div>`;
}

function webMatchPanel(matches) {
  if (!matches?.length) return '<p class="muted">No current web-backed page is linked to this staged record.</p>';
  return `<ul class="disc-link-list">${matches.slice(0, 10).map(match => `<li><a href="${esc(match.web_page_ref)}">Open matched current web page #${esc(match.web_page_id)}</a><small>${esc(match.classification || match.match_method || '')}</small></li>`).join('')}</ul>`;
}

function discSearchResults(results) {
  if (!results.length) return '<div class="empty-state"><h3>No disc records found</h3><p>Try an element title, procedure code, XML ID, or shorter phrase.</p></div>';
  return results.map(result => `<article class="card result-card disc-result">
    <div class="card-top"><div><h3 class="card-title"><a href="/disc/xml/${esc(result.source_xml_id)}">${esc(result.element_name)}</a></h3><div class="muted">${esc(result.section_name)} · XML ${esc(result.source_xml_id)}</div></div><span class="badge">Type ${esc(result.section_type)}</span></div>
    ${result.element_code ? `<p><code>${esc(result.element_code)}</code></p>` : ''}<p class="card-summary">${esc(result.excerpt || '').slice(0, 360)}</p>
    <div class="meta-row"><a href="/disc/elements/${esc(result.source_element_id)}">Element</a><span>·</span><a href="/disc/xml/${esc(result.source_xml_id)}">Content variant</a></div>
  </article>`).join('');
}

async function discLanding() {
  const health = await discApi('/health');
  const initialQuery = new URLSearchParams(location.search).get('q') || '';
  setTitle('Disc Preview');
  app.innerHTML = `${discNotice()}${discBreadcrumb()}
    <section class="hero disc-hero"><p class="eyebrow">Original Fiat Multipla eLearn disc</p><h1>Browse the staged source before production cutover.</h1><p class="lead">This read-only preview preserves the original XML, ordered hierarchy, applicability, cross-links, and native asset identities. The current web-backed pages continue to exist separately.</p>
      <div class="header-actions"><a class="button" href="/disc/manual/fiat-multipla">Open manual tree</a><a class="button secondary" href="#disc-search">Search staged source</a></div></section>
    <section class="stats-grid"><div class="stat"><strong>${number(health.counts.elements)}</strong><span>Disc elements</span></div><div class="stat"><strong>${number(health.counts.xml_records)}</strong><span>XML records</span></div><div class="stat"><strong>${number(health.counts.assets)}</strong><span>Asset records</span></div></section>
    <section><div class="page-header compact"><p class="eyebrow">Validation shortcuts</p><h2>Example disc records</h2></div><div class="grid disc-shortcuts">
      <a class="card" href="/disc/elements/2888504"><h3>Technical Data</h3><p class="muted">Engine and chassis version codes.</p></a>
      <a class="card" href="/disc/elements/2891139"><h3>Procedure</h3><p class="muted">Scheduled service procedure content.</p></a>
      <a class="card" href="/disc/elements/2888756"><h3>Electrical / Wiring</h3><p class="muted">Electrical supply description and references.</p></a>
      <a class="card" href="/disc/elements/2888312"><h3>Fault Diagnosis</h3><p class="muted">Alarm diagnostic workflow.</p></a>
    </div></section>
    <section id="disc-search"><div class="page-header compact"><p class="eyebrow">Staged source search</p><h2>Search disc records</h2><p class="muted">Search by title, element code, XML ID, or normalized source text.</p></div>
      <form class="search-form" id="disc-search-form" role="search"><input class="search-input" id="disc-search-query" value="${esc(initialQuery)}" placeholder="Try 5510CD, current generator, or an XML ID…" aria-label="Search staged disc source"><button class="button" type="submit">Search disc</button></form>
      <div class="results-list" id="disc-search-results">${initialQuery ? '<div class="loading-state"><span class="spinner"></span>Searching staged source…</div>' : '<p class="muted">Enter a query to search the staged disc content.</p>'}</div></section>`;
  const form = document.getElementById('disc-search-form');
  const input = document.getElementById('disc-search-query');
  const run = async () => {
    const query = input.value.trim();
    history.replaceState(null, '', query ? `/disc?q=${encodeURIComponent(query)}#disc-search` : '/disc#disc-search');
    if (!query) { document.getElementById('disc-search-results').innerHTML = '<p class="muted">Enter a query to search the staged disc content.</p>'; return; }
    document.getElementById('disc-search-results').innerHTML = '<div class="loading-state"><span class="spinner"></span>Searching staged source…</div>';
    const data = await discApi('/search?q=' + encodeURIComponent(query) + '&limit=40');
    document.getElementById('disc-search-results').innerHTML = `<p class="muted">${number(data.count)} results shown</p>${discSearchResults(data.results)}`;
  };
  form.addEventListener('submit', event => { event.preventDefault(); run().catch(showError); });
  if (initialQuery) await run();
}

function discTreeNode(node) {
  const label = `${node.code ? `<code>${esc(node.code)}</code> ` : ''}${esc(node.name)}`;
  if (!node.children?.length) return `<a class="disc-tree-leaf" href="/disc/elements/${esc(node.element_id)}">${label}<small>${number(node.xml_count)} content variant${node.xml_count === 1 ? '' : 's'}</small></a>`;
  return `<details class="disc-tree-node"><summary><span class="disc-tree-heading"><a href="/disc/elements/${esc(node.element_id)}">${label}</a><small>${number(node.children.length)} children · ${number(node.xml_count)} variants</small></span></summary><div class="disc-tree-children" data-lazy-element="${esc(node.element_id)}"></div></details>`;
}

function flattenDiscTree(node, section, output) {
  output.push({ ...node, section });
  (node.children || []).forEach(child => flattenDiscTree(child, section, output));
}

function bindDiscTreeLazy(nodeIndex) {
  document.querySelectorAll('.disc-tree-node').forEach(details => {
    details.querySelector(':scope > summary a')?.addEventListener('click', event => event.stopPropagation());
    details.addEventListener('toggle', () => {
      if (!details.open) return;
      const container = details.querySelector(':scope > .disc-tree-children');
      if (!container || container.dataset.loaded) return;
      const node = nodeIndex.get(Number(container.dataset.lazyElement));
      container.innerHTML = (node?.children || []).map(discTreeNode).join('');
      container.dataset.loaded = 'true';
      bindDiscTreeLazy(nodeIndex);
    }, { once: true });
  });
}

async function discManual() {
  const data = await discApi('/manual/fiat-multipla/tree');
  setTitle('Disc Manual Preview');
  const allNodes = [];
  const nodeIndex = new Map();
  data.sections.forEach(section => {
    if (section.root) flattenDiscTree(section.root, section.name, allNodes);
  });
  allNodes.forEach(node => nodeIndex.set(Number(node.element_id), node));
  app.innerHTML = `${discNotice()}${discBreadcrumb([{ label: 'Manual tree' }])}
    <header class="page-header compact"><p class="eyebrow">${number(allNodes.length)} staged navigation elements</p><h1>Fiat Multipla disc manual</h1><p class="lead">Expand the six original sections. Child nodes render only when opened so the full manual remains responsive.</p></header>
    <div class="filter-bar"><input class="filter-input" id="disc-tree-filter" placeholder="Find a title or element code…" aria-label="Filter disc manual tree"></div><div id="disc-tree-filter-results"></div>
    <div class="disc-section-list" id="disc-section-list">${data.sections.map(section => `<details class="disc-section"><summary><span><strong>${esc(section.name)}</strong><small>Section type ${esc(section.section_type)}</small></span></summary><div class="disc-section-body">${section.root ? discTreeNode(section.root) : '<p class="muted">Root element unavailable.</p>'}</div></details>`).join('')}</div>`;
  bindDiscTreeLazy(nodeIndex);
  const filter = document.getElementById('disc-tree-filter');
  filter.addEventListener('input', () => {
    const query = filter.value.trim().toLowerCase();
    const results = query ? allNodes.filter(node => `${node.name} ${node.code || ''} ${node.element_id}`.toLowerCase().includes(query)).slice(0, 100) : [];
    document.getElementById('disc-section-list').hidden = Boolean(query);
    document.getElementById('disc-tree-filter-results').innerHTML = query ? `<p class="muted">${number(results.length)} result${results.length === 100 ? 's (first 100)' : results.length === 1 ? '' : 's'}</p><div class="disc-filter-results">${results.map(node => `<a class="disc-tree-leaf" href="/disc/elements/${esc(node.element_id)}">${node.code ? `<code>${esc(node.code)}</code> ` : ''}${esc(node.name)}<small>${esc(node.section)} · element ${esc(node.element_id)}</small></a>`).join('')}</div>` : '';
  });
}

async function discElement(id) {
  const data = await discApi('/elements/' + encodeURIComponent(id));
  const element = data.element;
  setTitle(`${element.name} · Disc Preview`);
  app.innerHTML = `${discNotice()}${discBreadcrumb([{ label: 'Manual tree', href: '/disc/manual/fiat-multipla' }, { label: element.name }])}
    <header class="page-header compact"><div class="meta-row"><span class="badge">Disc element ${esc(element.source_element_id)}</span><span class="badge">Section type ${esc(element.section_type)}</span></div><h1>${esc(element.name)}</h1>${element.code ? `<p class="lead"><code>${esc(element.code)}</code></p>` : ''}<p class="muted">${esc(element.section_name)} · staged release ${esc(data.release_key)}</p></header>
    <div class="content-layout"><div class="content-main">
      <section class="card disc-panel"><h2>Content variants <span class="count-badge">${number(data.xml_records.length)}</span></h2>${data.xml_records.length ? `<div class="disc-variant-list">${data.xml_records.map((row, index) => `<a href="/disc/xml/${esc(row.source_xml_id)}"><strong>Variant ${index + 1}</strong><span>XML ${esc(row.source_xml_id)}${row.orders != null ? ` · order ${esc(row.orders)}` : ''}</span></a>`).join('')}</div>` : '<p class="muted">This navigation element has no XML content variant.</p>'}</section>
      <section class="card disc-panel"><h2>Applicability</h2>${applicabilitySummary(data.applicability)}</section>
      <section class="card disc-panel"><h2>Matched current web page</h2>${webMatchPanel(data.web_matches)}</section>
    </div><aside class="side-panel card"><h2>Navigation</h2>${data.parent_ref ? `<p><a href="${esc(data.parent_ref)}">← Parent element</a></p>` : '<p class="muted">Section root element</p>'}<h3>Children ${data.children.length ? `<span class="count-badge">${number(data.children.length)}</span>` : ''}</h3>${data.children.length ? `<ul class="subpage-list">${data.children.map(child => `<li><a href="${esc(child.element_ref)}">${child.code ? `<code>${esc(child.code)}</code> ` : ''}${esc(child.name)}</a></li>`).join('')}</ul>` : '<p class="muted">No child elements.</p>'}<hr><p class="source-id-list">Element ID <code>${esc(element.source_element_id)}</code><br>Section ID <code>${esc(element.source_section_id)}</code><br>Parent ID <code>${esc(element.parent_element_id)}</code></p></aside></div>`;
}

function bindDiscRenderedContent(data) {
  const content = document.getElementById('disc-rendered-content');
  if (!content) return;
  const assets = new Map((data.assets || []).map(asset => [String(asset.source_asset_id), asset]));
  content.querySelectorAll('.disc-asset').forEach(image => {
    const id = String(image.dataset.assetId || '');
    const asset = assets.get(id);
    if (!asset?.exists_on_disc) {
      const placeholder = document.createElement('span');
      placeholder.className = 'disc-asset-placeholder';
      placeholder.textContent = `Missing disc asset #${id}`;
      image.replaceWith(placeholder);
    } else if (asset.detected_type === 'JPEG') {
      image.src = `/disc-api/assets/${encodeURIComponent(id)}`;
      image.alt = `Disc asset ${id}`;
      image.loading = 'lazy';
    } else {
      const link = document.createElement('a');
      link.className = 'native-svg-link';
      link.href = `/disc-api/assets/${encodeURIComponent(id)}`;
      link.textContent = `Native SVG asset available (#${id})`;
      link.setAttribute('download', `${id}.image`);
      image.replaceWith(link);
    }
  });
  const links = new Map((data.links || []).filter(link => link.target_ref).map(link => [String(link.target_id), link.target_ref]));
  content.querySelectorAll('.disc-link').forEach(link => {
    const target = links.get(String(link.dataset.targetid || ''));
    if (target) link.href = target;
    else { link.removeAttribute('href'); link.classList.add('unresolved-disc-link'); }
  });
}

async function discXml(id) {
  const data = await discApi('/xml/' + encodeURIComponent(id));
  const record = data.xml;
  setTitle(`${record.element_name} · Disc XML`);
  app.innerHTML = `${discNotice()}${discBreadcrumb([{ label: 'Manual tree', href: '/disc/manual/fiat-multipla' }, { label: record.element_name, href: data.element_ref }, { label: `XML ${record.source_xml_id}` }])}
    <header class="page-header compact"><div class="meta-row"><span class="badge">XML ${esc(record.source_xml_id)}</span><span class="badge">Section type ${esc(record.section_type)}</span></div><h1>${esc(record.element_name)}</h1>${record.element_code ? `<p class="lead"><code>${esc(record.element_code)}</code></p>` : ''}<p class="muted">${esc(record.section_name)} · <a href="${esc(data.element_ref)}">Element ${esc(record.source_element_id)}</a></p></header>
    <div class="content-layout"><div class="content-main">
      <article class="card disc-rendered-card"><div class="disc-rendered-heading"><p class="eyebrow">Safely rendered staged XML</p><span>${number(data.assets.length)} assets · ${number(data.links.length)} internal links</span></div><div id="disc-rendered-content" class="disc-rendered-content">${data.rendered_html}</div></article>
      <section class="card disc-panel"><h2>Assets <span class="count-badge">${number(data.assets.length)}</span></h2>${data.assets.length ? `<div class="disc-asset-list">${data.assets.map(asset => `<div class="disc-asset-row"><div><strong>Asset ${esc(asset.source_asset_id)}</strong><small>${esc(asset.detected_type)} · ${esc(asset.reference_kind)}</small></div>${!asset.exists_on_disc ? '<span class="missing-label">Missing on disc</span>' : asset.detected_type === 'JPEG' ? `<a href="/disc-api/assets/${esc(asset.source_asset_id)}" target="_blank">Open image</a>` : `<a href="/disc-api/assets/${esc(asset.source_asset_id)}" download>Native SVG asset available</a>`}</div>`).join('')}</div>` : '<p class="muted">No assets referenced.</p>'}</section>
      <section class="card disc-panel"><h2>Internal disc links <span class="count-badge">${number(data.links.length)}</span></h2>${data.links.length ? `<ul class="disc-link-list">${data.links.map(link => `<li>${link.target_ref ? `<a href="${esc(link.target_ref)}">${esc(link.target_code || link.target_description || `Element ${link.target_id}`)}</a>` : `<span>${esc(link.target_code || link.target_description || `Target ${link.target_id}`)}</span>`}<small>${esc(link.link_kind)} · target ${esc(link.target_id)}</small></li>`).join('')}</ul>` : '<p class="muted">No internal links.</p>'}</section>
      <details class="card raw-source-panel"><summary>Raw source / debug</summary><div><p class="source-id-list">XML SHA-256 <code>${esc(record.raw_xml_sha256)}</code><br>Normalized text SHA-256 <code>${esc(record.normalized_text_sha256)}</code></p><pre>${esc(record.raw_xml)}</pre></div></details>
    </div><aside class="side-panel card"><h2>Applicability</h2>${applicabilitySummary(data.applicability)}<h2>Matched current web page</h2>${webMatchPanel(data.web_matches)}<hr><p class="source-id-list">XML ID <code>${esc(record.source_xml_id)}</code><br>Element ID <code>${esc(record.source_element_id)}</code></p></aside></div>`;
  bindDiscRenderedContent(data);
}

function showError(error) {
  console.error(error);
  setTitle('Error');
  app.innerHTML = `<div class="error-state"><h1>Unable to load this page</h1><p>${esc(error.message || error)}</p><a class="button secondary" href="${esc(location.pathname + location.search)}">Try again</a></div>`;
}

async function route() {
  setActiveNav();
  const path = location.pathname;
  if (path === '/disc') return discLanding();
  if (path === '/disc/manual/fiat-multipla') return discManual();
  if (path.startsWith('/disc/elements/')) return discElement(path.split('/').filter(Boolean).pop());
  if (path.startsWith('/disc/xml/')) return discXml(path.split('/').filter(Boolean).pop());
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
