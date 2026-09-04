import { readdirSync, statSync, writeFileSync, mkdirSync } from "node:fs";
import { join, relative } from "node:path";

const ROOT = "./ds-bundle";
const AUTHOR_SCOPE = new Set(process.argv[2] ? process.argv[2].split(",") : []);

function walk(dir, acc = []) {
  for (const e of readdirSync(dir)) {
    if (e.startsWith(".") || e === "_screenshots") continue;
    const p = join(dir, e);
    if (statSync(p).isDirectory()) walk(p, acc);
    else acc.push(relative(ROOT, p));
  }
  return acc;
}

const all = walk(ROOT);
const base = all.filter((p) => !p.startsWith("components/") && !p.startsWith("_preview/"));
const compOf = (p) => (p.startsWith("components/") ? p.split("/")[2] : null);
const batch = all.filter((p) => {
  const c = compOf(p);
  if (c) return !AUTHOR_SCOPE.has(c);
  return false;
});

mkdirSync(".design-sync/.cache", { recursive: true });
const chunks = [];
const files = [...base.filter((p) => p !== "_ds_sync.json"), ...batch];
for (let i = 0; i < files.length; i += 200) chunks.push(files.slice(i, i + 200));
writeFileSync(".design-sync/.cache/upload-batch1.json", JSON.stringify({ total: files.length, chunks }, null, 0));
console.log(`base=${base.length} batch=${batch.length} total=${files.length} chunks=${chunks.length}`);
