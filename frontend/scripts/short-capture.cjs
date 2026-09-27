// Captura escenas reales de Whetzy (stack local) a 1080x1920 para los shorts.
// Uso (desde frontend/, con backend y `npx vite` en local): OUT=<dir> node scripts/short-capture.cjs
// Responde bien usando la base LOCAL; nunca apuntar a produccion (crea una cuenta).
const { chromium } = require('@playwright/test');
const { execSync } = require('child_process');
const path = require('path');

const BASE = process.env.BASE || 'http://127.0.0.1:5173';
const OUT = process.env.OUT;
const SOLVER = path.join(__dirname, '..', '..', 'scripts', 'video', 'solve_blank.py');
const DB = process.env.WHETZY_DB_URL || 'postgresql://neurium:neurium_dev@localhost:5433/neurium';

function answerFor(id) {
  const sql = `select type, correct_index, coalesce(correct_answer_es,''), options_es::text from questions where id='${id.replace(/'/g, "''")}'`;
  const row = execSync(`psql "${DB}" -At -F '\u0001' -c "${sql}"`).toString().trim();
  const [type, idx, ans, opts] = row.split('\u0001');
  const options = opts ? JSON.parse(opts) : null;
  return { type, idx: idx === '' ? null : Number(idx), ans, options };
}

(async () => {
  const browser = await chromium.launch(process.env.CHROMIUM_PATH ? { executablePath: process.env.CHROMIUM_PATH } : {});
  const ctx = await browser.newContext({ viewport: { width: 432, height: 768 }, deviceScaleFactor: 2.5, locale: 'es-ES' });
  const page = await ctx.newPage();
  const shot = async (name) => { await page.waitForTimeout(1800); await page.screenshot({ path: path.join(OUT, name + '.png') }); console.log('shot', name); };

  let currentId = null;
  page.on('response', async (r) => {
    if (!/\/quiz\/(start|answer|next)/.test(r.url())) return;
    try { const j = await r.json(); const id = j?.question?.id || j?.next_question?.id; if (id) currentId = id; } catch {}
  });

  await page.goto(BASE + '/landing');
  await page.waitForLoadState('networkidle');
  await shot('landing');

  const user = 'demo' + Date.now().toString(36);
  await page.goto(BASE + '/auth');
  await page.getByLabel('Nombre').fill('Ana');
  await page.getByLabel('Usuario').fill(user);
  await page.getByLabel('Correo electrónico').fill(user + '@example.com');
  await page.getByLabel('Contraseña').fill('demo-video-pass-123');
  await page.getByRole('button', { name: 'EMPEZAR A APRENDER' }).click();
  await page.getByTestId('onboarding').waitFor({ timeout: 15000 });
  await shot('onboarding');
  await page.evaluate(() => {
    const raw = localStorage.getItem('learning-engine-store');
    const uid = raw && JSON.parse(raw)?.state?.user?.id;
    if (uid) localStorage.setItem(`whetzy_onboarded_${uid}`, '1');
  });
  await page.reload();
  await page.getByRole('button', { name: 'Inicio' }).waitFor({ timeout: 15000 });
  await shot('inicio_nuevo');

  await page.getByRole('button', { name: 'ESTUDIAR AHORA' }).click();
  await page.locator('[class*="questionCard_"]').waitFor({ timeout: 15000 });

  let mcqShots = 0, execShot = false, lastUsedId = null;
  for (let i = 0; i < 10; i++) {
    for (let w = 0; w < 40 && (!currentId || currentId === lastUsedId); w++) await page.waitForTimeout(200);
    lastUsedId = currentId;
    const a = currentId ? answerFor(currentId) : null;
    const opts = page.locator('[class*="options_"] button');
    if (await opts.count() > 0 && a && a.options && a.idx !== null) {
      const want = String(a.options[a.idx]).trim();
      const norm = (s) => s.replace(/\s+/g,' ').trim().toLowerCase();
      console.log('Q', currentId, a.type, 'want=', want.slice(0,60));
      if (mcqShots < 2) await shot(`pregunta_${mcqShots + 1}`);
      const n = await opts.count();
      let clicked = false;
      for (let k = 0; k < n; k++) {
        const t = (await opts.nth(k).innerText()).trim();
        console.log('  opt', k, JSON.stringify(t.slice(0,60)));
        const body = t.includes('\n') ? t.slice(t.indexOf('\n') + 1) : t;
        if (norm(body) === norm(want)) { await opts.nth(k).click(); clicked = true; break; }
      }
      if (!clicked) await opts.first().click();
      await page.locator('[class*="explanation_"]').waitFor({ timeout: 10000 });
      if (mcqShots < 2) { await shot(`feedback_${mcqShots + 1}`); mcqShots++; }
    } else {
      const blank = page.locator('[class*="blankInput_"]');
      let solFound = false;
      if (await blank.count() > 0 && currentId) {
        const sol = execSync(`python3 ${SOLVER} ${currentId}`).toString().trim();
        console.log('EXEC', currentId, 'sol=', JSON.stringify(sol));
        await blank.first().fill(sol || '42');
        solFound = !!sol;
      }
      const capture = !execShot && solFound;
      if (capture) await shot('codigo');
      const run = page.locator('[class*="btnRun_"]');
      if (await run.count() > 0) {
        for (let t = 0; t < 3; t++) {
          if (await page.locator('[class*="explanation_"]').isVisible().catch(() => false)) break;
          await run.waitFor({ timeout: 60000 });
          await page.waitForFunction((el) => !el.disabled, await run.elementHandle(), { timeout: 90000 }).catch(() => {});
          await run.click();
          await page.waitForTimeout(1500);
        }
      } else {
        const confirm = page.getByRole('button', { name: /Confirmar/ });
        if (await confirm.count() > 0) await confirm.first().click();
      }
      await page.locator('[class*="explanation_"]').waitFor({ timeout: 30000 }).catch(() => {});
      if (capture) { await shot('codigo_resultado'); execShot = true; }
    }
    await page.getByRole('button', { name: /^(SIGUIENTE|VER RESULTADOS)$/ }).click();
  }
  await page.locator('[class*="summaryGrade_"]').waitFor({ timeout: 15000 });
  await shot('resumen');
  await page.locator('[class*="btnStudy_"]').click();
  await page.getByRole('button', { name: 'Inicio' }).waitFor({ timeout: 15000 });
  await shot('inicio');
  const repaso = page.getByText('Lo que olvidarás esta semana');
  if (await repaso.count() > 0) {
    await repaso.first().evaluate((el) => el.scrollIntoView({ block: 'center' }));
    await shot('inicio_repaso');
  }

  await page.goto(BASE + '/evidence');
  await page.waitForLoadState('networkidle');
  await shot('evidence');
  await browser.close();
})().catch((e) => { console.error(e); process.exit(1); });
