import { readdirSync, readFileSync, writeFileSync, mkdirSync, rmSync } from "node:fs";
import { fileURLToPath } from "node:url";

/** Grouping stubs for design-sync: the DS pane takes a component's group from
 *  its doc frontmatter, and without these all 210 exports land in one list. */
const CATEGORY = {
  "Navigation & Layout": ["sidebar", "breadcrumb", "tabs", "separator", "scroll-area"],
  "Overlays & Menus": ["dialog", "alert-dialog", "sheet", "popover", "tooltip", "dropdown-menu", "command"],
  "Forms & Actions": ["button", "button-group", "input", "input-group", "textarea", "label", "select", "checkbox", "switch", "radio-group", "calendar", "field"],
  "Data Display": ["card", "table", "badge", "avatar", "progress", "item", "skeleton", "empty"],
  "Feedback": ["alert", "sonner", "spinner"],
  "Disclosure": ["accordion", "collapsible"],
  "Companion": ["bubble", "message", "message-scroller"],
};

const groupOf = new Map();
for (const [group, files] of Object.entries(CATEGORY)) {
  for (const f of files) groupOf.set(f, group);
}

const dtsDir = fileURLToPath(new URL("../dist/components/ui/", import.meta.url));
const outDir = fileURLToPath(new URL("../docs/design-system/", import.meta.url));
rmSync(outDir, { recursive: true, force: true });
mkdirSync(outDir, { recursive: true });

let written = 0;
const ungrouped = [];
for (const file of readdirSync(dtsDir).filter((f) => f.endsWith(".d.ts"))) {
  const stem = file.slice(0, -5);
  if (stem === "index") continue;
  const group = groupOf.get(stem);
  if (!group) {
    ungrouped.push(stem);
    continue;
  }
  const src = readFileSync(dtsDir + file, "utf8");
  const names = new Set();
  for (const m of src.matchAll(/^export \{([^}]*)\};/gm)) {
    for (const raw of m[1].split(",")) {
      const name = raw.trim().split(/\s+as\s+/).pop()?.trim();
      if (name && /^[A-Z]/.test(name)) names.add(name);
    }
  }
  for (const name of names) {
    writeFileSync(`${outDir}${name}.md`, `---\ncategory: ${group}\n---\n`);
    written++;
  }
}

console.log(`ds docs: ${written} stubs`);
if (ungrouped.length) console.log(`ungrouped source files: ${ungrouped.join(", ")}`);
