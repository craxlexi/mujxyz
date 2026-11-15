const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const ts = require('../frontend/node_modules/typescript');
const source = fs.readFileSync(require.resolve('../frontend/app/app/dashboardRefresh.ts'), 'utf8');
const code = ts.transpileModule(source, {compilerOptions: {module: ts.ModuleKind.CommonJS}}).outputText;

async function main() {
  let hidden = false, listener, calls = 0, pending;
  const timers = new Map();
  let nextId = 0;
  const context = {
    exports: {},
    document: {
      get hidden() { return hidden; },
      addEventListener(name, fn) { assert.equal(name, 'visibilitychange'); listener = fn; },
      removeEventListener(name, fn) { assert.equal(fn, listener); listener = undefined; },
    },
    setTimeout(fn, delay) { timers.set(++nextId, {fn, delay}); return nextId; },
    clearTimeout(id) { timers.delete(id); },
    Math,
  };
  vm.runInNewContext(code, context);
  const start = context.exports.startDashboardRefresh;
  const stop = start(() => { calls++; return new Promise(resolve => { pending = resolve; }); });
  assert.equal(calls, 1);
  assert.equal(timers.size, 0, 'No overlapping refresh while initial request waits');
  hidden = true;
  listener();
  hidden = false;
  listener();
  assert.equal(timers.size, 0, 'Visibility changes during a request must not create extra timers');
  pending();
  await new Promise(setImmediate);
  assert.equal(timers.size, 1);
  const timer = [...timers.values()][0];
  assert(timer.delay >= 60000 && timer.delay <= 75000);
  hidden = true;
  listener();
  assert.equal(timers.size, 0, 'Hidden tab must stop polling');
  await timer.fn();
  assert.equal(calls, 1);
  hidden = false;
  listener();
  const [id, resumed] = [...timers.entries()][0];
  assert(resumed.delay >= 0 && resumed.delay <= 3000);
  timers.delete(id);
  const running = resumed.fn();
  assert.equal(calls, 2);
  stop();
  pending();
  await running;
  assert.equal(timers.size, 0, 'Unmount must not restart polling');
  assert.equal(listener, undefined);
  hidden = true;
  const stopHidden = start(async () => { calls++; });
  assert.equal(calls, 2, 'Initially hidden tab must not fetch');
  stopHidden();
  console.log('Dashboard refresh checks passed: jitter, no overlap, visibility, cleanup.');
}
main().catch(error => { console.error(error); process.exitCode = 1; });
