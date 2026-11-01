import { STRINGS, CATEGORIES, TIME_LIMITS } from './i18n.js';

const $ = (id) => document.getElementById(id);
const store = {
  get(key, fallback) {
    try { const v = localStorage.getItem(key); return v === null ? fallback : JSON.parse(v); }
    catch { return fallback; }
  },
  set(key, value) {
    try { localStorage.setItem(key, JSON.stringify(value)); } catch { /* private mode */ }
  },
};

const state = {
  lang: store.get('lang', 'he'),
  favs: new Set(store.get('favs', [])),
  tab: 'all',
  category: null,
  maxTime: 0,
  shabbatOnly: false,
  query: '',
  recipes: [],
  updated: '',
  scrollY: 0,
};

const t = () => STRINGS[state.lang];
const today = () => new Date().toLocaleDateString('en-CA'); // YYYY-MM-DD in local time

function esc(s) {
  return String(s ?? '').replace(/[&<>"']/g, (c) =>
    ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]);
}

function safeUrl(u) {
  try { const url = new URL(u); return url.protocol === 'https:' || url.protocol === 'http:' ? url.href : ''; }
  catch { return ''; }
}

// The text block for the current language, falling back to the other one.
function text(r) {
  return r[state.lang] || r[state.lang === 'he' ? 'en' : 'he'] || {};
}

async function load() {
  try {
    const res = await fetch('data/recipes.json', { cache: 'no-cache' });
    if (!res.ok) throw new Error(res.status);
    const data = await res.json();
    state.recipes = (data.recipes || []).slice().sort((a, b) =>
      (b.added || '').localeCompare(a.added || ''));
    state.updated = data.updated || '';
  } catch {
    $('list').innerHTML = `<p class="error">${esc(t().loadError)}</p>`;
    return;
  }
  render();
}

function applyLang() {
  const s = t();
  document.documentElement.lang = state.lang;
  document.documentElement.dir = state.lang === 'he' ? 'rtl' : 'ltr';
  document.title = s.appTitle;
  $('title').textContent = s.appTitle;
  $('lang').textContent = state.lang === 'he' ? 'EN' : 'עב';
  $('back').setAttribute('aria-label', s.back);
  $('back').textContent = state.lang === 'he' ? '›' : '‹';
  $('tabAll').textContent = s.all;
  $('tabFav').textContent = s.fav;
  $('search').placeholder = s.search;
  $('shabbatLabel').textContent = s.shabbat;
  $('time').innerHTML = [`<option value="0">${esc(s.anyTime)}</option>`]
    .concat(TIME_LIMITS.map((m) => `<option value="${m}">${esc(s.upTo(m))}</option>`)).join('');
  $('time').value = String(state.maxTime);
  renderChips();
}

function renderChips() {
  const present = new Set(state.recipes.map((r) => r.category));
  $('chips').innerHTML = Object.entries(CATEGORIES)
    .filter(([key]) => present.has(key))
    .map(([key, c]) =>
      `<button class="chip${state.category === key ? ' active' : ''}" data-cat="${key}">${c.icon} ${esc(c[state.lang])}</button>`)
    .join('');
}

function matches(r) {
  if (state.tab === 'fav' && !state.favs.has(r.id)) return false;
  if (state.category && r.category !== state.category) return false;
  if (state.maxTime && (!r.totalMinutes || r.totalMinutes > state.maxTime)) return false;
  if (state.shabbatOnly && !r.shabbat) return false;
  if (state.query) {
    const q = state.query.toLowerCase();
    const hay = ['he', 'en'].map((l) => {
      const x = r[l] || {};
      return [x.title, x.description, ...(x.ingredients || [])].join(' ');
    }).join(' ').toLowerCase();
    if (!hay.includes(q)) return false;
  }
  return true;
}

function card(r) {
  const s = t();
  const x = text(r);
  const cat = CATEGORIES[r.category];
  const img = safeUrl(r.image);
  const isNew = r.added === today();
  const fav = state.favs.has(r.id);
  return `
    <article class="rcard" data-id="${esc(r.id)}">
      <div class="thumb">
        ${img ? `<img src="${esc(img)}" alt="" loading="lazy" referrerpolicy="no-referrer" onerror="this.remove()">` : ''}
        <span class="ph">${cat ? cat.icon : '🍽️'}</span>
        ${isNew ? `<span class="badge">${esc(s.newToday)}</span>` : ''}
        <button class="heart${fav ? ' on' : ''}" data-fav="${esc(r.id)}" aria-label="${esc(fav ? s.removeFav : s.addFav)}">${fav ? '♥' : '♡'}</button>
      </div>
      <div class="body">
        <h2>${esc(x.title)}</h2>
        <p class="meta">
          ${cat ? `<span>${cat.icon} ${esc(cat[state.lang])}</span>` : ''}
          ${r.totalMinutes ? `<span>⏱ ${esc(s.minutes(r.totalMinutes))}</span>` : ''}
          ${r.shabbat ? `<span>🕯️</span>` : ''}
        </p>
        <p class="source">${esc(r.source)}</p>
      </div>
    </article>`;
}

function renderList() {
  const s = t();
  const items = state.recipes.filter(matches);
  $('count').textContent = s.count(items.length);
  $('list').innerHTML = items.length
    ? items.map(card).join('')
    : `<p class="muted center">${esc(state.tab === 'fav' && !state.favs.size ? s.noFav : s.none)}</p>`;
  $('updated').textContent = state.updated ? s.updated(state.updated) : '';
  document.querySelectorAll('.tab').forEach((b) =>
    b.classList.toggle('active', b.dataset.tab === state.tab));
}

function renderRecipe(id) {
  const s = t();
  const r = state.recipes.find((x) => x.id === id);
  const view = $('recipeView');
  if (!r) { view.innerHTML = `<p class="muted center">${esc(s.notFound)}</p>`; return; }
  const x = text(r);
  const cat = CATEGORIES[r.category];
  const img = safeUrl(r.image);
  const url = safeUrl(r.url);
  const fav = state.favs.has(r.id);
  const checked = new Set(store.get(`checked:${r.id}`, []));
  const translated = r.sourceLang && r.sourceLang !== state.lang;
  const n = r.nutrition || {};
  const times = [
    r.prepMinutes && `${s.prep}: ${s.minutes(r.prepMinutes)}`,
    r.cookMinutes && `${s.cook}: ${s.minutes(r.cookMinutes)}`,
    r.waitMinutes && `${s.wait}: ${s.minutes(r.waitMinutes)}`,
    r.totalMinutes && `${s.total}: ${s.minutes(r.totalMinutes)}`,
  ].filter(Boolean);

  view.innerHTML = `
    <div class="hero">
      ${img ? `<img src="${esc(img)}" alt="${esc(x.title)}" referrerpolicy="no-referrer" onerror="this.remove()">` : ''}
      <span class="ph">${cat ? cat.icon : '🍽️'}</span>
    </div>
    <div class="detail">
      <div class="title-row">
        <h2>${esc(x.title)}</h2>
        <button class="heart big${fav ? ' on' : ''}" data-fav="${esc(r.id)}" aria-label="${esc(fav ? s.removeFav : s.addFav)}">${fav ? '♥' : '♡'}</button>
      </div>
      ${x.description ? `<p>${esc(x.description)}</p>` : ''}
      <p class="meta">
        ${cat ? `<span>${cat.icon} ${esc(cat[state.lang])}</span>` : ''}
        ${r.servings ? `<span>🍽 ${esc(s.servings(r.servings))}</span>` : ''}
        ${r.shabbat ? `<span>🕯️ ${esc(s.shabbat)}</span>` : ''}
      </p>
      ${times.length ? `<p class="meta">${times.map((x) => `<span>⏱ ${esc(x)}</span>`).join('')}</p>` : ''}
      ${n.calories || n.protein ? `
        <div class="nutri">
          ${n.calories ? `<div><b>${esc(n.calories)}</b><small>${esc(s.kcal)}</small></div>` : ''}
          ${n.protein ? `<div><b>${esc(n.protein)}</b><small>${esc(s.protein)}</small></div>` : ''}
          <p class="muted">${esc(s.perServing)}</p>
        </div>` : ''}

      <h3>${esc(s.ingredients)}</h3>
      <ul class="ingredients">
        ${(x.ingredients || []).map((ing, i) => `
          <li><label><input type="checkbox" data-ing="${i}"${checked.has(i) ? ' checked' : ''}> <span>${esc(ing)}</span></label></li>`).join('')}
      </ul>

      <h3>${esc(s.steps)}</h3>
      <ol class="steps">${(x.steps || []).map((st) => `<li>${esc(st)}</li>`).join('')}</ol>

      ${x.whyFits ? `<div class="why"><b>✅ ${esc(s.whyFits)}</b><p>${esc(x.whyFits)}</p></div>` : ''}

      <p class="source">
        ${esc(s.from)} ${esc(r.source)}${translated ? ` · ${esc(s.translated)}` : ''}
      </p>
      ${url ? `<a class="primary" href="${esc(url)}" target="_blank" rel="noopener">${esc(s.original)}</a>` : ''}
    </div>`;

  view.querySelectorAll('[data-ing]').forEach((box) => box.addEventListener('change', () => {
    const on = [...view.querySelectorAll('[data-ing]')].filter((b) => b.checked).map((b) => Number(b.dataset.ing));
    store.set(`checked:${r.id}`, on);
  }));
}

function route() {
  const m = location.hash.match(/^#\/r\/(.+)$/);
  const inRecipe = Boolean(m);
  $('feedView').hidden = inRecipe;
  $('recipeView').hidden = !inRecipe;
  $('back').hidden = !inRecipe;
  if (inRecipe) {
    renderRecipe(decodeURIComponent(m[1]));
    window.scrollTo(0, 0);
  } else {
    renderList();
    window.scrollTo(0, state.scrollY);
  }
}

function render() {
  applyLang();
  route();
}

function toggleFav(id) {
  if (state.favs.has(id)) state.favs.delete(id); else state.favs.add(id);
  store.set('favs', [...state.favs]);
  const y = window.scrollY;
  const m = location.hash.match(/^#\/r\/(.+)$/);
  if (m) renderRecipe(decodeURIComponent(m[1])); else renderList();
  window.scrollTo(0, y);
}

// Events
$('lang').addEventListener('click', () => {
  state.lang = state.lang === 'he' ? 'en' : 'he';
  store.set('lang', state.lang);
  render();
});
$('back').addEventListener('click', () => {
  if (history.length > 1) history.back(); else location.hash = '';
});
document.querySelectorAll('.tab').forEach((b) => b.addEventListener('click', () => {
  state.tab = b.dataset.tab;
  renderList();
}));
$('search').addEventListener('input', (e) => { state.query = e.target.value.trim(); renderList(); });
$('time').addEventListener('change', (e) => { state.maxTime = Number(e.target.value); renderList(); });
$('shabbatOnly').addEventListener('change', (e) => { state.shabbatOnly = e.target.checked; renderList(); });
$('chips').addEventListener('click', (e) => {
  const chip = e.target.closest('[data-cat]');
  if (!chip) return;
  state.category = state.category === chip.dataset.cat ? null : chip.dataset.cat;
  renderChips();
  renderList();
});
document.addEventListener('click', (e) => {
  const heart = e.target.closest('[data-fav]');
  if (heart) { e.stopPropagation(); toggleFav(heart.dataset.fav); return; }
  const c = e.target.closest('.rcard');
  if (c) {
    state.scrollY = window.scrollY;
    location.hash = `#/r/${encodeURIComponent(c.dataset.id)}`;
  }
});
window.addEventListener('hashchange', route);

if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('sw.js').catch(() => {});
}

applyLang();
load();
