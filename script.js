// ─── État global ─────────────────────────────────────────────────────────────
let ELEVES = [];
let SPORTS = [];
let sportSelectionne = null;
let inscritsActuels = [];
let champsActuels = [];
let idsSelectionnes = new Set();
let triColonne = 'nom';
let triAsc = true;
let allElevesCache = [];

// ─── Onglets ─────────────────────────────────────────────────────────────────
function showTab(tab) {
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  event.currentTarget.classList.add('active');

  document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
  document.getElementById('panel-' + tab).classList.add('active');

  document.getElementById('sidebar-eleves').style.display = tab === 'eleves' ? '' : 'none';
  document.getElementById('sidebar-sports').style.display = tab === 'sports' ? '' : 'none';
  document.getElementById('sidebar-import').style.display = tab === 'import' ? '' : 'none';

  closeSidebar();
  if (tab === 'eleves') rechercherEleves();
  if (tab === 'sports') chargerSports();
}

// ─── Sidebar mobile ───────────────────────────────────────────────────────────
function toggleSidebar() {
  const sidebar = [...document.querySelectorAll('.sidebar')].find(s => s.style.display !== 'none');
  if (!sidebar) return;
  const overlay = document.getElementById('sidebar-overlay');
  const isOpen = sidebar.classList.contains('open');
  sidebar.classList.toggle('open', !isOpen);
  overlay.classList.toggle('open', !isOpen);
}

function closeSidebar() {
  document.querySelectorAll('.sidebar').forEach(s => s.classList.remove('open'));
  document.getElementById('sidebar-overlay').classList.remove('open');
}

// ─── Toast ───────────────────────────────────────────────────────────────────
function toast(msg, type = 'success') {
  const el = document.getElementById('toast');
  el.textContent = msg;
  el.className = 'show ' + type;
  clearTimeout(el._t);
  el._t = setTimeout(() => { el.className = ''; }, 2800);
}

// ─── Modals ──────────────────────────────────────────────────────────────────
function ouvrirModal(id) { document.getElementById(id).classList.add('open'); }
function fermerModal(id) { document.getElementById(id).classList.remove('open'); }

document.querySelectorAll('.modal-backdrop').forEach(m => {
  m.addEventListener('click', e => { if (e.target === m) m.classList.remove('open'); });
});

// ─── API helpers ─────────────────────────────────────────────────────────────
async function api(url, method = 'GET', body = null) {
  const opts = { method, headers: { 'Content-Type': 'application/json' } };
  if (body) opts.body = JSON.stringify(body);
  const r = await fetch(url, opts);
  if (!r.ok) {
    const err = await r.json().catch(() => ({}));
    throw new Error(err.erreur || `HTTP ${r.status}`);
  }
  return r.json();
}

// ─── Classes ─────────────────────────────────────────────────────────────────
async function chargerClasses() {
  try {
    const classes = await api('/api/classes');
    const sel = document.getElementById('filter-classe');
    sel.innerHTML = '<option value="">Toutes classes</option>';
    classes.forEach(c => {
      const o = document.createElement('option');
      o.value = c; o.textContent = c;
      sel.appendChild(o);
    });
    // Pour le modal inscrire
    const sel2 = document.getElementById('inscrire-classe');
    sel2.innerHTML = '<option value="">Toutes classes</option>';
    classes.forEach(c => {
      const o = document.createElement('option');
      o.value = c; o.textContent = c;
      sel2.appendChild(o);
    });
  } catch {}
}

// ─── Sports sidebar ───────────────────────────────────────────────────────────
async function chargerSports() {
  try {
    SPORTS = await api('/api/sports');
    const liste = document.getElementById('sports-sidebar-list');
    const sel = document.getElementById('filter-sport-eleve');
    sel.innerHTML = '<option value="">Tous sports</option>';

    liste.innerHTML = '';
    SPORTS.forEach(s => {
      const card = document.createElement('div');
      card.className = 'sport-card' + (sportSelectionne === s.nom ? ' selected' : '');
      card.innerHTML = `<span class="sport-name">${s.nom}</span><span class="sport-count">${s.nb_inscrits} inscrits</span>`;
      card.onclick = () => selectionnerSport(s.nom);
      liste.appendChild(card);

      const o = document.createElement('option');
      o.value = s.nom; o.textContent = s.nom;
      sel.appendChild(o);
    });
  } catch (e) { toast('Erreur chargement sports', 'error'); }
}

async function ajouterSport() {
  const nom = document.getElementById('nouveau-sport-nom').value.trim();
  if (!nom) { toast('Entrez un nom de sport', 'error'); return; }
  try {
    await api('/api/sports', 'POST', { nom });
    document.getElementById('nouveau-sport-nom').value = '';
    await chargerSports();
    toast(`Sport "${nom}" créé ✓`);
  } catch (e) { toast(e.message, 'error'); }
}

async function supprimerSport() {
  if (!sportSelectionne) return;
  if (!confirm(`Supprimer le sport "${sportSelectionne}" et toutes ses inscriptions ?`)) return;
  try {
    await api(`/api/sports/${encodeURIComponent(sportSelectionne)}`, 'DELETE');
    sportSelectionne = null;
    document.getElementById('table-sport-wrap').style.display = 'none';
    document.getElementById('sport-empty').style.display = '';
    document.getElementById('sport-recherche').style.display = 'none';
    document.getElementById('count-sport-inscrits').style.display = 'none';
    document.getElementById('sport-titre').textContent = 'Choisissez un sport';
    ['btn-renommer-champs','btn-inscrire-eleves','btn-supprimer-sport'].forEach(id => {
      document.getElementById(id).style.display = 'none';
    });
    await chargerSports();
    toast('Sport supprimé');
  } catch (e) { toast(e.message, 'error'); }
}

async function selectionnerSport(nom) {
  sportSelectionne = nom;
  document.getElementById('sport-titre').textContent = nom;
  document.getElementById('sport-empty').style.display = 'none';
  document.getElementById('sport-recherche').style.display = '';
  document.getElementById('count-sport-inscrits').style.display = '';
  ['btn-renommer-champs','btn-inscrire-eleves','btn-supprimer-sport'].forEach(id => {
    document.getElementById(id).style.display = '';
  });
  await chargerSports();
  await chargerInscrits();
}

async function chargerInscrits() {
  if (!sportSelectionne) return;
  const q = document.getElementById('search-inscrit').value;
  try {
    const data = await api(`/api/sports/${encodeURIComponent(sportSelectionne)}/inscrits?q=${encodeURIComponent(q)}`);
    inscritsActuels = data.inscrits;
    champsActuels = data.champs;
    afficherTableauSport();
  } catch (e) { toast(e.message, 'error'); }
}

function rechercherInscrits() { chargerInscrits(); }

function afficherTableauSport() {
  const wrap = document.getElementById('table-sport-wrap');
  wrap.style.display = '';

  // Header
  const tr = document.getElementById('thead-sport-row');
  tr.innerHTML = `<th>Nom</th><th>Prénom</th><th>Classe</th>`;
  champsActuels.forEach(c => { tr.innerHTML += `<th>${c}</th>`; });
  tr.innerHTML += `<th></th>`;

  // Body
  const tbody = document.getElementById('tbody-sport');
  tbody.innerHTML = '';
  document.getElementById('count-sport-inscrits').textContent = `${inscritsActuels.length} inscrits`;

  inscritsActuels.forEach(e => {
    const tr2 = document.createElement('tr');
    tr2.innerHTML = `<td>${e.nom}</td><td>${e.prenom}</td><td><span class="classe-tag">${e.classe}</span></td>`;
    champsActuels.forEach(c => {
      const val = e.champs[c] || false;
      const cell = document.createElement('td');
      const box = document.createElement('div');
      box.className = 'check-cell' + (val ? ' checked' : '');
      box.textContent = val ? '✓' : '';
      box.title = `Cliquer pour ${val ? 'décocher' : 'cocher'}`;
      box.onclick = async () => {
        try {
          await api(`/api/sports/${encodeURIComponent(sportSelectionne)}/inscrits/${e.id}`, 'PATCH', { [c]: !val });
          await chargerInscrits();
        } catch (err) { toast(err.message, 'error'); }
      };
      cell.appendChild(box);
      tr2.appendChild(cell);
    });
    const tdAction = document.createElement('td');
    tdAction.innerHTML = `<button class="btn btn-danger btn-sm" onclick="desinscrire('${e.id}')">✕</button>`;
    tr2.appendChild(tdAction);
    tbody.appendChild(tr2);
  });
}

async function desinscrire(eleveId) {
  try {
    await api(`/api/sports/${encodeURIComponent(sportSelectionne)}/desinscrire/${eleveId}`, 'DELETE');
    await chargerInscrits();
    await chargerSports();
    toast('Élève désinscrit');
  } catch (e) { toast(e.message, 'error'); }
}

// ─── Modal inscrire élèves ────────────────────────────────────────────────────
async function ouvrirModalInscrire() {
  try {
    allElevesCache = await api('/api/eleves');
    afficherListeInscription();
    ouvrirModal('modal-inscrire');
  } catch (e) { toast(e.message, 'error'); }
}

function filtrerInscription() { afficherListeInscription(); }

function afficherListeInscription() {
  const q = document.getElementById('inscrire-search').value.toLowerCase();
  const classe = document.getElementById('inscrire-classe').value;
  const deja = new Set(inscritsActuels.map(e => e.id));

  const liste = document.getElementById('inscrire-liste');
  liste.innerHTML = '';

  allElevesCache
    .filter(e => !deja.has(e.id))
    .filter(e => !q || e.nom.toLowerCase().startsWith(q))
    .filter(e => !classe || e.classe === classe)
    .forEach(e => {
      const row = document.createElement('div');
      row.style.cssText = 'display:flex;align-items:center;gap:10px;padding:9px 14px;border-bottom:1px solid var(--border)';
      row.innerHTML = `
        <input type="checkbox" value="${e.id}" style="width:auto;cursor:pointer"/>
        <span style="flex:1">${e.nom} ${e.prenom}</span>
        <span class="classe-tag">${e.classe}</span>`;
      liste.appendChild(row);
    });

  if (!liste.children.length) {
    liste.innerHTML = '<div style="padding:20px;text-align:center;color:var(--muted)">Aucun élève disponible</div>';
  }
}

async function validerInscription() {
  const ids = [...document.getElementById('inscrire-liste').querySelectorAll('input[type=checkbox]:checked')]
    .map(c => c.value);
  if (!ids.length) { toast('Sélectionnez au moins un élève', 'error'); return; }
  try {
    const r = await api(`/api/sports/${encodeURIComponent(sportSelectionne)}/inscrire`, 'POST', { ids });
    fermerModal('modal-inscrire');
    await chargerInscrits();
    await chargerSports();
    toast(`${r.inscrits} élève(s) inscrit(s) ✓`);
  } catch (e) { toast(e.message, 'error'); }
}

// ─── Modal renommer champs ────────────────────────────────────────────────────
function ouvrirModalRenommerChamps() {
  const container = document.getElementById('champs-inputs');
  container.innerHTML = '';
  champsActuels.forEach((c, i) => {
    const row = document.createElement('div');
    row.style.marginBottom = '10px';
    row.innerHTML = `<label class="form-label">Colonne ${i + 1}</label>
      <input type="text" class="champ-rename" value="${c}" placeholder="Nom colonne ${i+1}"/>`;
    container.appendChild(row);
  });
  // Bouton pour ajouter colonne si < 7
  if (champsActuels.length < 7) {
    const btn = document.createElement('button');
    btn.className = 'btn btn-ghost btn-sm';
    btn.textContent = '+ Ajouter colonne';
    btn.onclick = () => {
      if (container.querySelectorAll('.champ-rename').length >= 7) return;
      const row2 = document.createElement('div');
      row2.style.marginBottom = '10px';
      row2.innerHTML = `<label class="form-label">Colonne ${container.querySelectorAll('.champ-rename').length + 1}</label>
        <input type="text" class="champ-rename" placeholder="Nouvelle colonne"/>`;
      container.insertBefore(row2, btn);
    };
    container.appendChild(btn);
  }
  ouvrirModal('modal-champs');
}

async function validerRenommerChamps() {
  const vals = [...document.querySelectorAll('.champ-rename')].map(i => i.value.trim()).filter(Boolean);
  if (!vals.length) { toast('Au moins un champ requis', 'error'); return; }
  try {
    await api(`/api/sports/${encodeURIComponent(sportSelectionne)}/champs`, 'PUT', { champs: vals });
    fermerModal('modal-champs');
    await chargerInscrits();
    toast('Champs mis à jour ✓');
  } catch (e) { toast(e.message, 'error'); }
}

// ─── Élèves ──────────────────────────────────────────────────────────────────
async function rechercherEleves() {
  const q = document.getElementById('search-nom').value;
  const niveau = document.getElementById('filter-niveau').value;
  const classe = document.getElementById('filter-classe').value;
  const carte = document.getElementById('filter-carte').value;
  const photo = document.getElementById('filter-photo').value;
  const sport = document.getElementById('filter-sport-eleve').value;
  const params = new URLSearchParams({ q, niveau, classe, carte, photo, sport });
  try {
    ELEVES = await api('/api/eleves?' + params);
    afficherTableauEleves();
    mettreAJourStats();
  } catch (e) { toast('Erreur chargement élèves', 'error'); }
}

let sortKey = 'nom', sortDir = 1;

function trierColonne(col) {
  if (sortKey === col) sortDir *= -1;
  else { sortKey = col; sortDir = 1; }
  document.querySelectorAll('#table-eleves th').forEach(th => {
    th.classList.remove('sorted-asc', 'sorted-desc');
  });
  const idx = ['', 'nom', 'prenom', 'sexe', 'classe', 'date_naissance', 'carte_jeunest', 'autorisation_photo', 'cotisation'].indexOf(col);
  if (idx > 0) {
    const th = document.querySelectorAll('#table-eleves th')[idx];
    th.classList.add(sortDir === 1 ? 'sorted-asc' : 'sorted-desc');
  }
  ELEVES.sort((a, b) => {
    let va = a[col], vb = b[col];
    if (typeof va === 'boolean') { va = va ? 1 : 0; vb = vb ? 1 : 0; }
    if (typeof va === 'string') return va.localeCompare(vb) * sortDir;
    return (va - vb) * sortDir;
  });
  afficherTableauEleves();
}

function afficherTableauEleves() {
  const tbody = document.getElementById('tbody-eleves');
  tbody.innerHTML = '';
  document.getElementById('count-eleves').textContent = ELEVES.length;

  ELEVES.forEach(e => {
    const tr = document.createElement('tr');
    const sel = idsSelectionnes.has(e.id);
    tr.innerHTML = `
      <td><input type="checkbox" ${sel ? 'checked' : ''} onchange="toggleSelection('${e.id}', this.checked)" style="cursor:pointer;width:auto"/></td>
      <td><strong>${e.nom}</strong></td>
      <td>${e.prenom}</td>
      <td><span class="badge ${e.sexe === 'F' ? 'badge-ok' : 'badge-warn'}">${e.sexe}</span></td>
      <td><span class="classe-tag">${e.classe}</span></td>
      <td>${e.date_naissance}</td>
      <td>${e.carte_jeunest
        ? `<span class="editable" onclick="editerCarte('${e.id}', this)">${e.carte_jeunest}</span>`
        : `<span class="editable" style="color:var(--muted)" onclick="editerCarte('${e.id}', this)">—</span>`}</td>
      <td><span class="badge ${e.autorisation_photo ? 'badge-ok' : 'badge-no'}" style="cursor:pointer" onclick="togglePhoto('${e.id}', ${e.autorisation_photo})">${e.autorisation_photo ? 'Oui' : 'Non'}</span></td>
      <td>${e.cotisation} €</td>
      <td>${(e.sports || []).map(s => `<span class="sport-tag">${s}</span>`).join('')}</td>
      <td style="display:flex;gap:4px">
        <button class="btn btn-ghost btn-sm" onclick="ouvrirModifEleve('${e.id}')">✏️</button>
        <button class="btn btn-danger btn-sm" onclick="supprimerEleve('${e.id}')">🗑</button>
      </td>`;
    tbody.appendChild(tr);
  });
}

function mettreAJourStats() {
  const total = ELEVES.length;
  const avecCarte = ELEVES.filter(e => e.carte_jeunest).length;
  const avecPhoto = ELEVES.filter(e => e.autorisation_photo).length;
  const cotisTotal = ELEVES.reduce((s, e) => s + (e.cotisation || 0), 0);
  document.getElementById('stats-eleves').innerHTML = `
    <div class="stat-card"><div class="stat-val">${total}</div><div class="stat-lbl">Élèves affichés</div></div>
    <div class="stat-card"><div class="stat-val">${avecCarte}</div><div class="stat-lbl">Avec carte</div></div>
    <div class="stat-card"><div class="stat-val">${avecPhoto}</div><div class="stat-lbl">Photos ok</div></div>
    <div class="stat-card"><div class="stat-val">${cotisTotal.toFixed(0)} €</div><div class="stat-lbl">Cotisations</div></div>`;
}

// ─── Édition inline carte ─────────────────────────────────────────────────────
function editerCarte(eleveId, el) {
  const old = el.textContent === '—' ? '' : el.textContent;
  const input = document.createElement('input');
  input.className = 'editable-input';
  input.value = old;
  el.replaceWith(input);
  input.focus();
  const sauvegarder = async () => {
    const val = input.value.trim();
    try {
      await api(`/api/eleves/${eleveId}`, 'PATCH', { carte_jeunest: val });
      await rechercherEleves();
    } catch (e) { toast(e.message, 'error'); }
  };
  input.addEventListener('blur', sauvegarder);
  input.addEventListener('keydown', e => { if (e.key === 'Enter') input.blur(); });
}

async function togglePhoto(eleveId, actuel) {
  try {
    await api(`/api/eleves/${eleveId}`, 'PATCH', { autorisation_photo: !actuel });
    await rechercherEleves();
  } catch (e) { toast(e.message, 'error'); }
}

// ─── Modal ajout élève ────────────────────────────────────────────────────────
function ouvrirModalAjoutEleve() { ouvrirModal('modal-ajout-eleve'); }

async function validerAjoutEleve() {
  const payload = {
    nom: document.getElementById('ajout-nom').value,
    prenom: document.getElementById('ajout-prenom').value,
    sexe: document.getElementById('ajout-sexe').value,
    classe: document.getElementById('ajout-classe').value,
    date_naissance: document.getElementById('ajout-date').value,
  };
  try {
    await api('/api/eleves', 'POST', payload);
    fermerModal('modal-ajout-eleve');
    ['ajout-nom','ajout-prenom','ajout-classe','ajout-date'].forEach(id => document.getElementById(id).value = '');
    await rechercherEleves();
    await chargerClasses();
    toast('Élève ajouté ✓');
  } catch (e) { toast(e.message, 'error'); }
}

// ─── Modal modif élève ────────────────────────────────────────────────────────
function ouvrirModifEleve(eleveId) {
  const e = ELEVES.find(el => el.id === eleveId);
  if (!e) return;
  document.getElementById('edit-eleve-id').value = eleveId;
  document.getElementById('edit-nom').value = e.nom;
  document.getElementById('edit-prenom').value = e.prenom;
  document.getElementById('edit-sexe').value = e.sexe;
  document.getElementById('edit-classe').value = e.classe;
  document.getElementById('edit-date').value = e.date_naissance;
  document.getElementById('edit-carte').value = e.carte_jeunest || '';
  document.getElementById('edit-cotisation').value = e.cotisation;
  document.getElementById('edit-photo').checked = e.autorisation_photo;
  ouvrirModal('modal-edit-eleve');
}

async function validerModifEleve() {
  const id = document.getElementById('edit-eleve-id').value;
  const payload = {
    nom: document.getElementById('edit-nom').value,
    prenom: document.getElementById('edit-prenom').value,
    sexe: document.getElementById('edit-sexe').value,
    classe: document.getElementById('edit-classe').value,
    date_naissance: document.getElementById('edit-date').value,
    carte_jeunest: document.getElementById('edit-carte').value,
    cotisation: parseFloat(document.getElementById('edit-cotisation').value) || 10,
    autorisation_photo: document.getElementById('edit-photo').checked,
  };
  try {
    await api(`/api/eleves/${id}`, 'PATCH', payload);
    fermerModal('modal-edit-eleve');
    await rechercherEleves();
    toast('Élève modifié ✓');
  } catch (e) { toast(e.message, 'error'); }
}

async function supprimerSelection() {
  const ids = [...idsSelectionnes];
  if (!ids.length) return;
  if (!confirm(`Supprimer ${ids.length} élève(s) ? Cette action est irréversible.`)) return;
  try {
    await Promise.all(ids.map(id => api(`/api/eleves/${id}`, 'DELETE')));
    idsSelectionnes.clear();
    await rechercherEleves();
    toast(`${ids.length} élève(s) supprimé(s)`);
  } catch (e) { toast(e.message, 'error'); }
}

async function supprimerEleve(eleveId) {
  if (!confirm('Supprimer cet élève ?')) return;
  try {
    await api(`/api/eleves/${eleveId}`, 'DELETE');
    await rechercherEleves();
    toast('Élève supprimé');
  } catch (e) { toast(e.message, 'error'); }
}

// ─── Sélection multiple ───────────────────────────────────────────────────────
function toggleSelection(id, checked) {
  if (checked) idsSelectionnes.add(id);
  else idsSelectionnes.delete(id);
  mettrAJourBarSelection();
}

function toggleTout(checked) {
  ELEVES.forEach(e => { if (checked) idsSelectionnes.add(e.id); else idsSelectionnes.delete(e.id); });
  afficherTableauEleves();
  mettrAJourBarSelection();
}

function deselectionnerTout() {
  idsSelectionnes.clear();
  document.getElementById('check-all').checked = false;
  afficherTableauEleves();
  mettrAJourBarSelection();
}

function mettrAJourBarSelection() {
  const bar = document.getElementById('select-bar');
  const n = idsSelectionnes.size;
  if (n > 0) {
    bar.classList.add('visible');
    document.getElementById('select-count').textContent = `${n} sélectionné(s)`;
  } else {
    bar.classList.remove('visible');
  }
}

function ouvrirModalBatch() { ouvrirModal('modal-batch'); }

async function validerBatch() {
  const modifications = {};
  const carte = document.getElementById('batch-carte').value.trim();
  const cotis = document.getElementById('batch-cotisation').value;
  const photo = document.querySelector('input[name="batch-photo"]:checked')?.value;

  if (carte !== '') modifications.carte_jeunest = carte;
  if (cotis !== '') modifications.cotisation = parseFloat(cotis);
  if (photo === 'oui') modifications.autorisation_photo = true;
  if (photo === 'non') modifications.autorisation_photo = false;

  if (!Object.keys(modifications).length) { toast('Aucune modification', 'error'); return; }
  try {
    const r = await api('/api/eleves/batch', 'PATCH', { ids: [...idsSelectionnes], modifications });
    fermerModal('modal-batch');
    deselectionnerTout();
    await rechercherEleves();
    toast(`${r.modifies} élève(s) modifié(s) ✓`);
  } catch (e) { toast(e.message, 'error'); }
}

// ─── Import CSV ───────────────────────────────────────────────────────────────
function dragOver(e) { e.preventDefault(); document.getElementById('drop-zone').classList.add('dragover'); }
function dragLeave()  { document.getElementById('drop-zone').classList.remove('dragover'); }

function dropFichier(e) {
  e.preventDefault();
  dragLeave();
  const file = e.dataTransfer.files[0];
  if (file) importerFichier(file);
}

function importerCSV(input) { if (input.files[0]) importerFichier(input.files[0]); }

async function importerFichier(file) {
  const formData = new FormData();
  formData.append('fichier', file);
  const result = document.getElementById('import-result');
  result.innerHTML = '<div style="color:var(--muted)">⏳ Import en cours…</div>';
  try {
    const r = await fetch('/api/import', { method: 'POST', body: formData });
    const data = await r.json();
    let html = `<div style="color:var(--accent);font-size:14px;margin-bottom:10px">✓ ${data.importes} élève(s) importé(s)</div>`;
    if (data.erreurs?.length) {
      html += `<div style="color:var(--accent2);margin-bottom:6px">⚠️ ${data.erreurs.length} ligne(s) ignorée(s) :</div>`;
      html += `<ul style="padding-left:18px;font-size:11px;color:var(--muted)">`;
      data.erreurs.forEach(err => { html += `<li>${err}</li>`; });
      html += '</ul>';
    }
    result.innerHTML = html;
    await chargerClasses();
    toast(`Import terminé : ${data.importes} élèves`);
  } catch (e) { result.innerHTML = `<div style="color:var(--accent2)">Erreur : ${e.message}</div>`; }
}

async function genererEleves() {
  const result = document.getElementById('import-result');
  result.innerHTML = '<div style="color:var(--muted)">⏳ Génération en cours…</div>';
  try {
    const r = await fetch('/api/generer_eleves', { method: 'POST' });
    const data = await r.json();
    if (data.erreur) { result.innerHTML = `<div style="color:var(--accent2)">Erreur : ${data.erreur}</div>`; return; }
    let html = `<div style="color:var(--accent);font-size:14px;margin-bottom:10px">✓ ${data.importes} élève(s) généré(s) et importé(s)</div>`;
    if (data.erreurs?.length) {
      html += `<div style="color:var(--accent2);margin-bottom:6px">⚠️ ${data.erreurs.length} ligne(s) ignorée(s)</div>`;
    }
    result.innerHTML = html;
    await chargerClasses();
    toast(`Génération terminée : ${data.importes} élèves`);
  } catch (e) { result.innerHTML = `<div style="color:var(--accent2)">Erreur : ${e.message}</div>`; }
}

// ─── Impression ───────────────────────────────────────────────────────────────
function imprimerTableau() { window.print(); }

// ─── Init ─────────────────────────────────────────────────────────────────────
(async function init() {
  await chargerClasses();
  await chargerSports();
  await rechercherEleves();
})();
