const $ = id => document.getElementById(id);
const compact = window.matchMedia('(max-width:650px)');
const fitSettings = () => { $('settings-panel').open = !compact.matches; };
fitSettings(); compact.addEventListener('change', fitSettings);
let models = [], busy = false;
const selected = () => models.find(model => model.id === $('model').value);
async function api(path, options) {
  const response = await fetch(path, options);
  const body = await response.json();
  if (!response.ok) throw new Error(body.error || 'Request failed');
  return body;
}
function option(value, text) { const element = document.createElement('option'); element.value = value; element.textContent = text; return element; }
function message(text, error = false) { $('status').textContent = text; $('status').classList.toggle('error', error); }
function stateControls() {
  const model = selected(), use = $('use-lora').checked && !!model?.adapters.length;
  $('adapter').disabled = busy || !use;
  $('use-lora').disabled = busy || !model?.adapters.length;
  $('model').disabled = busy;
  $('refresh').disabled = busy;
  $('generate').disabled = busy || !model?.available;
  $('compare').disabled = busy || !use || !model?.available;
  for (const input of $('fields').querySelectorAll('input,textarea,select')) input.disabled = busy;
  $('prompt').disabled = busy;
  $('example').disabled = busy;
}
function configure() {
  const model = selected(); if (!model) return;
  $('adapter').replaceChildren(...model.adapters.map(a => option(a.id, a.label)));
  if (!model.adapters.length) $('adapter').append(option('', 'No trained adapter found'));
  $('model-note').textContent = model.available ? 'Local weights ready' : 'Model files are missing. Download this experiment first.';
  $('type-label').textContent = `${model.type.toUpperCase()} WORKSPACE`;
  $('fields').replaceChildren();
  for (const field of model.fields) {
    const wrapper = document.createElement('div'); if (field.type === 'textarea' || field.id === 'size') wrapper.className = 'field-full';
    const label = document.createElement('label'); label.htmlFor = `setting-${field.id}`; label.textContent = field.label;
    const input = document.createElement(field.type === 'select' ? 'select' : field.type === 'textarea' ? 'textarea' : 'input');
    input.id = `setting-${field.id}`;
    if (field.type === 'select') input.append(...field.options.map(v => option(v, v.replace('x', ' × '))));
    if (field.type === 'number') { input.type = 'number'; input.min = field.min; input.max = field.max; input.step = field.step; }
    input.value = field.default; wrapper.append(label, input); $('fields').append(wrapper);
  }
  $('prompt').value = model.default_prompt; stateControls();
}
async function refresh() {
  const old = $('model').value;
  models = (await api('/api/models')).models;
  $('model').replaceChildren(...models.map(model => option(model.id, model.label)));
  if (models.some(m => m.id === old)) $('model').value = old;
  configure();
  if (!models.length) message('No supported experiment profiles found.', true);
}
function renderJob(job) {
  const existing = document.querySelector(`[data-job="${job.id}"]`); if (existing) existing.remove();
  $('welcome')?.remove();
  const article = document.createElement('article'); article.className = 'test'; article.dataset.job = job.id;
  const head = document.createElement('div'); head.className = 'test-head';
  const prompt = document.createElement('p'); prompt.textContent = job.request.prompt;
  const info = document.createElement('small'); info.textContent = `${job.request.model_label} · ${new Date(job.created_utc).toLocaleString()}`;
  head.append(prompt, info); article.append(head);
  const outputs = document.createElement('div'); outputs.className = 'outputs';
  for (const item of job.result?.outputs || []) {
    const card = document.createElement('div'); card.className = 'output';
    const bar = document.createElement('div'); bar.className = 'output-head';
    const label = document.createElement('b'); label.textContent = item.label; bar.append(label);
    const url = item.file ? `/api/jobs/${job.id}/files/${encodeURIComponent(item.file)}` : null;
    if (url) { const link = document.createElement('a'); link.href = url; link.download = item.file; link.textContent = 'Download'; bar.append(link); }
    card.append(bar);
    if (item.kind === 'image') { const image = document.createElement('img'); image.src = url; image.alt = `${item.label}: ${job.request.prompt}`; card.append(image); }
    else if (item.kind === 'audio' || item.kind === 'video') { const media = document.createElement(item.kind); media.src = url; media.controls = true; card.append(media); }
    else { const text = document.createElement('div'); text.className = 'text-output'; text.textContent = item.text || ''; card.append(text); }
    if (item.filtered) { const note = document.createElement('div'); note.className = 'filter-note'; note.textContent = 'The model filter hid this image. Try another prompt.'; card.append(note); }
    outputs.append(card);
  }
  article.append(outputs);
  const footer = document.createElement('div'); footer.className = 'result-footer';
  const settings = job.request.settings || {};
  const parts = [];
  if (settings.seed !== undefined) parts.push(`Seed ${settings.seed}`);
  if (settings.steps !== undefined) parts.push(`${settings.steps} steps`);
  if (settings.size) parts.push(settings.size.replace('x', ' × '));
  if (job.result?.generation_seconds !== undefined) parts.push(`${job.result.generation_seconds}s`);
  const summary = document.createElement('span'); summary.textContent = parts.join(' · ');
  const link = document.createElement('a'); link.href = `/api/jobs/${job.id}/files/result.json`; link.download = 'result.json'; link.className = 'download'; link.textContent = 'Settings JSON';
  footer.append(summary, link); article.append(footer); $('feed').append(article);
}
async function generate(mode) {
  const model = selected(); if (!model || busy) return;
  const settings = {};
  for (const field of model.fields) { const element = $(`setting-${field.id}`); if (!element.reportValidity()) return; settings[field.id] = field.type === 'number' ? Number(element.value) : element.value; }
  if (!$('prompt').value.trim()) return message('Enter an image prompt first.', true);
  busy = true; stateControls(); $('progress').hidden = false; $('progress').value = 0; message('Starting local generation…');
  try {
    let job = await api('/api/jobs', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ model: model.id, adapter: $('use-lora').checked ? $('adapter').value : null, prompt: $('prompt').value, mode, settings }) });
    while (!['done', 'error'].includes(job.status)) {
      message(job.message); $('progress').value = job.progress;
      await new Promise(resolve => setTimeout(resolve, 750));
      job = await api(`/api/jobs/${job.id}`);
    }
    if (job.status === 'error') throw new Error(job.message);
    renderJob(job); message('Saved locally. Change the prompt or seed to try another result.'); $('progress').value = 100;
  } catch (error) { message(error.message, true); }
  finally { busy = false; stateControls(); $('progress').hidden = true; }
}
$('model').addEventListener('change', configure);
$('use-lora').addEventListener('change', stateControls);
$('refresh').addEventListener('click', () => refresh().catch(error => message(error.message, true)));
$('example').addEventListener('click', () => { $('prompt').value = selected().default_prompt; });
$('generate').addEventListener('click', () => generate('generate'));
$('compare').addEventListener('click', () => generate('compare'));
$('clear').addEventListener('click', () => $('feed').replaceChildren());
$('history-button').addEventListener('click', async () => {
  try {
    const jobs = (await api('/api/jobs')).jobs; $('history-list').replaceChildren();
    if (!jobs.length) $('history-list').textContent = 'No saved tests yet.';
    for (const job of jobs) {
      const button = document.createElement('button'); button.className = 'history-item';
      const title = document.createElement('b'); title.textContent = job.request.prompt;
      const detail = document.createElement('span'); detail.textContent = `${job.request.model_label} · ${job.status} · ${new Date(job.created_utc).toLocaleString()}`;
      button.append(title, detail); button.addEventListener('click', () => { if (job.status === 'done') renderJob(job); else message(job.message, job.status === 'error'); $('history').close(); }); $('history-list').append(button);
    }
    $('history').showModal();
  } catch (error) { message(error.message, true); }
});
$('close-history').addEventListener('click', () => $('history').close());
refresh().catch(error => message(error.message, true));
