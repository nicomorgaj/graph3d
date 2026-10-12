// Prueba del visor sin navegador: ejecuta el script del HTML generado con un DOM simulado.
// Uso: node tests/js/viewer.test.js <archivo.html>
const fs = require('fs');
const vm = require('vm');
const assert = require('assert');

const html = fs.readFileSync(process.argv[2], 'utf8');
const script = html.split('<script>')[1].split('</script>')[0];
const data = JSON.parse(script.match(/const DATA = (\{[\s\S]*?\});\nconst T = DATA/)[1]);

let alpha = 1;
const drawn = { fills: 0, labels: 0 };
const ctx = new Proxy({}, {
  get(_t, p) {
    if (p === 'fill') return () => { drawn.fills++; };
    if (p === 'fillText') return () => { drawn.labels++; };
    if (p === 'measureText') return (t) => ({ width: String(t).length * 6.5 });
    if (p === 'globalAlpha') return alpha;
    return () => {};
  },
  set(_t, p, v) { if (p === 'globalAlpha') alpha = v; return true; },
});

const listeners = {};
const canvas = {
  getContext: () => ctx,
  addEventListener: (type, fn) => { listeners[type] = fn; },
  setPointerCapture() {},
  classList: { add() {}, remove() {} },
};
const created = [];
const makeElement = () => ({
  style: {}, dataset: {}, children: [{ style: {} }, {}, {}], checked: false, value: '', textContent: '',
  appendChild() {}, addEventListener() {}, classList: { add() {}, remove() {} },
  set innerHTML(_v) {}, get innerHTML() { return ''; },
});
const elements = {};
global.document = {
  documentElement: {},
  title: '',
  getElementById: (id) => (id === 'c' ? canvas : (elements[id] ||= makeElement())),
  createElement: () => { const el = makeElement(); created.push(el); return el; },
  querySelectorAll: () => [],
};
global.window = { innerWidth: 1600, innerHeight: 900, devicePixelRatio: 1, addEventListener() {} };
let frame = null;
global.requestAnimationFrame = (fn) => { frame = fn; };

vm.runInThisContext(script);
const run = (code) => vm.runInThisContext(code);
const renderFrame = () => { run('dirty = true'); drawn.fills = 0; drawn.labels = 0; frame(); };
const lit = () => run('nodes.filter((_, i) => isLit(i)).length');
const chip = (index) => created.filter((e) => String(e.className || '').startsWith('chip')).slice(-data.areas.length)[index].onclick();

let passed = 0;
const test = (name, fn) => { fn(); passed++; console.log('  ok  ' + name); };

test('arranca y dibuja todos los nodos', () => {
  renderFrame();
  assert.strictEqual(drawn.fills, data.nodes.length);
  assert.ok(elements.stats.textContent.includes(String(data.nodes.length)));
});

test('muestra las etiquetas principales sin pasarse del límite', () => {
  assert.ok(drawn.labels <= 45, `demasiadas etiquetas: ${drawn.labels}`);
});

test('traduce el título y el idioma de la interfaz', () => {
  assert.strictEqual(global.document.title, data.title);
  assert.strictEqual(global.document.documentElement.lang, data.lang);
});

test('sin filtros todos los nodos están iluminados', () => {
  assert.strictEqual(lit(), data.nodes.length);
});

test('los filtros de área se pueden combinar', () => {
  const counts = data.areas.map((_, a) => data.nodes.filter((n) => n.a === a).length);
  const count = data.areas.length;
  assert.ok(count >= 2, 'el grafo de prueba necesita al menos 2 áreas');
  chip(0);
  assert.strictEqual(lit(), counts[0]);
  chip(1);
  assert.strictEqual(lit(), counts[0] + counts[1]);
  chip(0);
  assert.strictEqual(lit(), counts[1]);
  chip(1);
  assert.strictEqual(lit(), data.nodes.length);
});

test('seleccionar un nodo ilumina solo sus vecinos', () => {
  const target = data.nodes.findIndex((n) => n.d > 0);
  run(`selectNode(${target})`);
  const neighbours = new Set([target]);
  data.edges.forEach(([s, t]) => { if (s === target) neighbours.add(t); if (t === target) neighbours.add(s); });
  assert.strictEqual(lit(), neighbours.size);
  run('clearSelection()');
  assert.strictEqual(lit(), data.nodes.length);
});

test('la velocidad de rotación escala y se puede invertir', () => {
  const step = (speed, reverse) => {
    elements.speed.oninput({ target: { value: String(speed) } });
    elements.reverse.onchange({ target: { checked: reverse } });
    const before = run('view.yaw');
    run('loop()');
    return run('view.yaw') - before;
  };
  const base = step(1, false);
  assert.ok(Math.abs(step(4, false) / base - 4) < 1e-9);
  assert.ok(Math.abs(step(0.1, false) / base - 0.1) < 1e-9);
  assert.ok(Math.abs(step(1, true) + base) < 1e-12);
  assert.strictEqual(run('autoSpin'), true);
});

test('rotar con el ratón y hacer zoom no rompe el dibujo', () => {
  listeners.pointerdown({ pointerId: 1, clientX: 600, clientY: 400, shiftKey: false, button: 0 });
  listeners.pointermove({ clientX: 660, clientY: 430 });
  listeners.pointerup({ clientX: 660, clientY: 430 });
  listeners.wheel({ preventDefault() {}, deltaY: 300 });
  renderFrame();
  assert.strictEqual(drawn.fills, data.nodes.length);
});

console.log(`${passed} pruebas del visor OK`);
