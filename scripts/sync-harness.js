/**
 * sync-harness.js — copia docs/harness/ para os adaptadores do Claude Code.
 *
 * docs/harness/ é a fonte única. Este script espelha:
 *   docs/harness/rules/*.md     -> .claude/rules/
 *   docs/harness/commands/*.md  -> .claude/commands/
 *   docs/harness/agents/*.md    -> .claude/agents/
 *   docs/harness/skills/<nome>/ -> .claude/skills/<nome>/
 *
 * Arquivos que sobraram no destino e não têm mais fonte são removidos.
 * .claude/settings.json e .claude/settings.local.json NÃO são tocados.
 *
 * Uso:
 *   node scripts/sync-harness.js            # sincroniza
 *   node scripts/sync-harness.js --check    # só verifica; sai 1 se estiver desatualizado
 */

const fs = require('node:fs');
const path = require('node:path');

const ROOT = path.resolve(__dirname, '..');
const HARNESS = path.join(ROOT, 'docs/harness');
const CLAUDE = path.join(ROOT, '.claude');

// Nunca copiados, e nunca considerados órfãos no destino.
const IGNORED = new Set(['__pycache__', '.DS_Store']);

const checkMode = process.argv.includes('--check');
let clean = true;

function log(msg) {
  console.error(`[harness:sync] ${msg}`);
}

function read(p) {
  try {
    return fs.readFileSync(p, 'utf-8');
  } catch {
    return null;
  }
}

function writeIfChanged(dest, content) {
  if (read(dest) === content) return;
  if (checkMode) {
    log(`DESATUALIZADO: ${path.relative(ROOT, dest)}`);
    clean = false;
    return;
  }
  fs.mkdirSync(path.dirname(dest), { recursive: true });
  fs.writeFileSync(dest, content, 'utf-8');
  log(`escreveu ${path.relative(ROOT, dest)}`);
}

/** Remove entradas do destino que não estão em `keep`. */
function prune(destDir, keep, isDir) {
  if (checkMode || !fs.existsSync(destDir)) return;
  for (const entry of fs.readdirSync(destDir, { withFileTypes: true })) {
    if (entry.name.startsWith('.') || IGNORED.has(entry.name)) continue;
    if (entry.isDirectory() !== Boolean(isDir)) continue;
    if (keep.has(entry.name)) continue;
    const p = path.join(destDir, entry.name);
    fs.rmSync(p, { recursive: true, force: true });
    log(`removeu órfão ${path.relative(ROOT, p)}`);
  }
}

/** Pastas planas de .md: rules, commands, agents. */
function syncMdDir(name) {
  const src = path.join(HARNESS, name);
  const dest = path.join(CLAUDE, name);
  const files = fs.existsSync(src)
    ? fs.readdirSync(src).filter((f) => f.endsWith('.md')).sort()
    : [];

  for (const f of files) writeIfChanged(path.join(dest, f), read(path.join(src, f)) ?? '');
  prune(dest, new Set(files), false);
}

function copyTree(src, dest) {
  for (const entry of fs.readdirSync(src, { withFileTypes: true })) {
    if (IGNORED.has(entry.name)) continue;
    const s = path.join(src, entry.name);
    const d = path.join(dest, entry.name);
    if (entry.isDirectory()) copyTree(s, d);
    else writeIfChanged(d, read(s) ?? '');
  }
}

/** Skills são pastas inteiras. */
function syncSkills() {
  const src = path.join(HARNESS, 'skills');
  const dest = path.join(CLAUDE, 'skills');
  const names = fs.existsSync(src)
    ? fs
        .readdirSync(src, { withFileTypes: true })
        .filter((d) => d.isDirectory())
        .map((d) => d.name)
    : [];

  for (const name of names) copyTree(path.join(src, name), path.join(dest, name));
  prune(dest, new Set(names), true);
}

syncMdDir('rules');
syncMdDir('commands');
syncMdDir('agents');
syncSkills();

if (checkMode) {
  if (clean) log('adaptadores em dia.');
  else {
    log('adaptadores desatualizados — rode `node scripts/sync-harness.js`.');
    process.exit(1);
  }
}
