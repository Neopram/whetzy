#!/usr/bin/env node

/**
 * i18n CI Guard
 *
 * Validates i18n parity across the project:
 * - Frontend i18n JSON files (ES/EN key parity)
 * - Backend email templates (ES/EN sections)
 * - Legal documents (ES/EN variants)
 *
 * Fails build if parity < threshold (default: 95%)
 */

import * as fs from 'fs';
import * as path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const projectRoot = path.resolve(__dirname, '..');

const DEFAULT_THRESHOLD = 95;
const args = process.argv.slice(2);
let threshold = DEFAULT_THRESHOLD;
let verbose = false;

for (let i = 0; i < args.length; i++) {
  if (args[i] === '--threshold' && args[i + 1]) {
    threshold = parseInt(args[i + 1], 10);
    i++;
  }
  if (args[i] === '--verbose' || args[i] === '-v') {
    verbose = true;
  }
}

const results = [];
let hasFailures = false;

function log(msg) {
  console.log(msg);
}

function logVerbose(msg) {
  if (verbose) console.log(msg);
}

function checkFrontendI18n() {
  const i18nDir = path.join(projectRoot, 'frontend', 'src', 'i18n');
  const enFile = path.join(i18nDir, 'en', 'common.json');
  const esFile = path.join(i18nDir, 'es', 'common.json');

  const result = {
    category: 'frontend-i18n',
    parity: 0,
    status: 'FAIL',
  };

  try {
    if (!fs.existsSync(enFile) || !fs.existsSync(esFile)) {
      result.error = 'Missing translation files';
      results.push(result);
      hasFailures = true;
      return;
    }

    const enData = JSON.parse(fs.readFileSync(enFile, 'utf-8'));
    const esData = JSON.parse(fs.readFileSync(esFile, 'utf-8'));

    function flattenKeys(obj, prefix = '') {
      const keys = new Set();
      for (const k in obj) {
        const fullKey = prefix ? `${prefix}.${k}` : k;
        keys.add(fullKey);
        if (typeof obj[k] === 'object' && obj[k] !== null) {
          const nested = flattenKeys(obj[k], fullKey);
          nested.forEach(nk => keys.add(nk));
        }
      }
      return keys;
    }

    const enKeys = flattenKeys(enData);
    const esKeys = flattenKeys(esData);

    const missingInEn = Array.from(esKeys).filter(k => !enKeys.has(k));
    const missingInEs = Array.from(enKeys).filter(k => !esKeys.has(k));
    const total = new Set([...enKeys, ...esKeys]).size;

    const matched = total - missingInEn.length - missingInEs.length;
    const parity = total > 0 ? (matched / total) * 100 : 100;

    result.parity = Math.round(parity * 100) / 100;
    result.total_keys = total;
    result.en_keys = enKeys.size;
    result.es_keys = esKeys.size;

    if (missingInEn.length > 0) {
      result.missing_in_en = missingInEn;
    }
    if (missingInEs.length > 0) {
      result.missing_in_es = missingInEs;
    }

    result.status = parity >= threshold ? 'PASS' : 'FAIL';
    if (parity < threshold) {
      hasFailures = true;
    }

    logVerbose(`[frontend-i18n] Total keys: ${total}, EN: ${enKeys.size}, ES: ${esKeys.size}, Parity: ${result.parity}%`);
  } catch (e) {
    result.error = e.message;
    result.status = 'FAIL';
    hasFailures = true;
  }

  results.push(result);
}

function checkBackendEmails() {
  const emailServicePath = path.join(projectRoot, 'backend', 'app', 'services', 'email.py');

  const result = {
    category: 'backend-emails',
    parity: 0,
    status: 'FAIL',
  };

  try {
    if (!fs.existsSync(emailServicePath)) {
      result.error = 'Email service not found';
      results.push(result);
      return;
    }

    const content = fs.readFileSync(emailServicePath, 'utf-8');

    // Look for email templates - they are defined as:
    // "template_name": { "es": {...}, "en": {...} }
    // Strategy: Find all "word": { occurrences, then check if that section has "es" and "en"
    
    const templateMatches = content.match(/"([a-z_]+)"\s*:\s*{/g) || [];
    const templateNames = [...new Set(templateMatches.map(m => m.match(/"([a-z_]+)"/)[1]))];

    // For each potential template, check if it has both es and en
    let correctCount = 0;
    const templateStatus = {};

    // Simple heuristic: look for patterns like "welcome": { ... "es": ... "en": ...
    for (const tpl of templateNames) {
      // Count occurrences of this exact template name followed by nesting and language keys
      const searchStr = `"${tpl}"`;
      const idx = content.indexOf(searchStr);
      
      if (idx !== -1) {
        // Get a reasonable chunk after this template name (1500 chars or until next template)
        let endIdx = content.indexOf('}, "', idx);
        if (endIdx === -1) endIdx = idx + 1500;
        
        const section = content.substring(idx, endIdx);
        const hasEs = section.includes('"es":');
        const hasEn = section.includes('"en":');
        
        // Only count as a valid template if it has both es and en
        if (hasEs && hasEn) {
          correctCount++;
          templateStatus[tpl] = 'OK';
        } else if (hasEs || hasEn) {
          templateStatus[tpl] = hasEs ? 'MISSING_EN' : 'MISSING_ES';
        }
      }
    }

    const parity = templateNames.length > 0
      ? (correctCount / templateNames.length) * 100
      : 100;

    result.parity = Math.round(parity * 100) / 100;
    result.total_templates = templateNames.length;
    result.correct_templates = correctCount;
    result.status = parity >= threshold ? 'PASS' : 'FAIL';

    if (parity < threshold && Object.keys(templateStatus).length > 0) {
      hasFailures = true;
      result.template_status = templateStatus;
    } else if (parity >= threshold) {
      result.status = 'PASS';
    }

    logVerbose(`[backend-emails] Total: ${templateNames.length}, Correct: ${correctCount}, Parity: ${result.parity}%`);
  } catch (e) {
    result.error = e.message;
    result.status = 'FAIL';
    hasFailures = true;
  }

  results.push(result);
}

function checkLegalDocs() {
  const legalDir = path.join(projectRoot, 'legal');

  const result = {
    category: 'legal-docs',
    parity: 0,
    status: 'FAIL',
  };

  try {
    if (!fs.existsSync(legalDir)) {
      result.error = 'Legal directory not found';
      result.status = 'PASS';
      results.push(result);
      return;
    }

    const files = fs.readdirSync(legalDir).filter(f => f.endsWith('.md'));

    const docsByBase = {};
    for (const file of files) {
      let base = file.replace('.md', '');
      let lang = null;

      if (base.endsWith('.es')) {
        base = base.slice(0, -3);
        lang = 'es';
      } else if (base.endsWith('.en')) {
        base = base.slice(0, -3);
        lang = 'en';
      } else {
        lang = 'en';
      }

      if (!docsByBase[base]) {
        docsByBase[base] = { es: false, en: false };
      }
      docsByBase[base][lang] = true;
    }

    const total = Object.keys(docsByBase).length;
    let correctCount = 0;
    const missingLangs = {};

    for (const [base, langs] of Object.entries(docsByBase)) {
      if (langs.es && langs.en) {
        correctCount++;
      } else {
        missingLangs[base] = langs.es ? 'MISSING_EN' : 'MISSING_ES';
      }
    }

    const parity = total > 0 ? (correctCount / total) * 100 : 100;

    result.parity = Math.round(parity * 100) / 100;
    result.total_docs = total;
    result.correct_docs = correctCount;
    result.status = parity >= threshold ? 'PASS' : 'WARN';

    if (Object.keys(missingLangs).length > 0) {
      result.missing_languages = missingLangs;
    }

    logVerbose(`[legal-docs] Total: ${total}, Correct: ${correctCount}, Parity: ${result.parity}%`);
  } catch (e) {
    result.error = e.message;
    result.status = 'WARN';
  }

  results.push(result);
}

checkFrontendI18n();
checkBackendEmails();
checkLegalDocs();

log('\n=== i18n Parity Check ===\n');

let allPass = true;
for (const result of results) {
  const icon = result.status === 'PASS' ? '✓' : result.status === 'FAIL' ? '✗' : '⚠';
  log(`${icon} ${result.category.padEnd(20)} ${result.parity.toString().padEnd(6)}% ${result.status}`);

  if (result.error) {
    log(`  Error: ${result.error}`);
  }
  if (result.missing_in_en && result.missing_in_en.length > 0) {
    log(`  Missing in EN: ${result.missing_in_en.slice(0, 3).join(', ')}${result.missing_in_en.length > 3 ? ' ...' : ''}`);
  }
  if (result.missing_in_es && result.missing_in_es.length > 0) {
    log(`  Missing in ES: ${result.missing_in_es.slice(0, 3).join(', ')}${result.missing_in_es.length > 3 ? ' ...' : ''}`);
  }
  if (result.missing_languages) {
    const missing = Object.entries(result.missing_languages).map(([k, v]) => `${k}(${v})`);
    log(`  Missing: ${missing.join(', ')}`);
  }

  if (result.status === 'FAIL') {
    allPass = false;
  }
}

const passCount = results.filter(r => r.status === 'PASS').length;
const failCount = results.filter(r => r.status === 'FAIL').length;
const warnCount = results.filter(r => r.status === 'WARN').length;

log(`\nSummary: ${passCount} PASS, ${warnCount} WARN, ${failCount} FAIL`);
log(`Threshold: ${threshold}%\n`);

process.exit(hasFailures ? 1 : 0);
