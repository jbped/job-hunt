import type { ReactNode } from "react";

/** The vault's own note renderer, ported line-for-line from the vanilla page
 *  (`markdown()`/`inline()`, index.html:467/445). Deliberately small: it
 *  renders the vault's notes for reading, not arbitrary markdown. Everything is
 *  escaped before any tag is introduced, so a note containing HTML displays as
 *  text rather than executing — which is why the output is safe to inject. */

const NUL = "\u0000";

function escapeHtml(text: string): string {
  const map: Record<string, string> = {
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
  };
  return String(text).replace(/[&<>"']/g, (c) => map[c] ?? c);
}

export function inline(text: string): string {
  const code: string[] = [];
  let out = escapeHtml(text).replace(
    /`([^`]+)`/g,
    (_, body: string) => `${NUL}${code.push(body) - 1}${NUL}`,
  );
  // Wikilinks become real links; a delegated click handler resolves them
  // server-side and routes inside the app. Text is already HTML-escaped, so
  // the target is attribute-safe as-is.
  const wikilink = (target: string, label: string) =>
    `<a href="#" class="wikilink" data-wikilink="${target.trim()}">${label}</a>`;
  out = out
    .replace(/\[\[([^\]|]+)\|([^\]]+)\]\]/g, (_, target: string, label: string) =>
      wikilink(target, label),
    )
    .replace(/\[\[([^\]]+)\]\]/g, (_, target: string) =>
      wikilink(target, target.split("#")[0].split("/").pop()?.trim() ?? ""),
    )
    .replace(
      /\[([^\]]+)\]\((https?:[^)\s]+)\)/g,
      '<a href="$2" target="_blank" rel="noreferrer">$1</a>',
    )
    .replace(
      /(^|[\s(])(https?:\/\/[^\s<)]+)/g,
      '$1<a href="$2" target="_blank" rel="noreferrer">$2</a>',
    )
    .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
    .replace(/(^|[^*])\*([^*\n]+)\*(?!\*)/g, "$1<em>$2</em>");
  return out.replace(
    new RegExp(`${NUL}(\\d+)${NUL}`, "g"),
    (_, i: string) => `<code>${code[Number(i)]}</code>`,
  );
}

export function markdownToHtml(source: string): string {
  const lines = String(source).split("\n");
  const out: string[] = [];
  let list: string | null = null;
  let fence: string | null = null;
  let fenced: string[] = [];

  const closeList = () => {
    if (list) {
      out.push(`</${list}>`);
      list = null;
    }
  };

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];

    if (fence !== null) {
      if (line.trim().startsWith("```")) {
        out.push(
          `<pre class="verbatim"><code>${escapeHtml(fenced.join("\n"))}</code></pre>`,
        );
        fence = null;
        fenced = [];
      } else fenced.push(line);
      continue;
    }
    if (line.trim().startsWith("```")) {
      closeList();
      fence = line;
      fenced = [];
      continue;
    }

    // Frontmatter is metadata the dashboard already shows as fields; rendering
    // it again as a wall of key/value lines just pushes the content down.
    if (i === 0 && line.trim() === "---") {
      const end = lines.indexOf("---", 1);
      if (end > 0) {
        i = end;
        continue;
      }
    }

    if (!line.trim()) {
      closeList();
      continue;
    }

    const heading = line.match(/^(#{1,6})\s+(.*)$/);
    if (heading) {
      closeList();
      const level = Math.min(heading[1].length + 1, 6);
      out.push(`<h${level}>${inline(heading[2])}</h${level}>`);
      continue;
    }
    if (/^([-*_])\1{2,}\s*$/.test(line.trim())) {
      closeList();
      out.push("<hr>");
      continue;
    }
    if (line.trim().startsWith("> ")) {
      closeList();
      out.push(`<blockquote>${inline(line.trim().slice(2))}</blockquote>`);
      continue;
    }

    const bullet = line.match(/^\s*[-*+]\s+(.*)$/);
    const numbered = line.match(/^\s*\d+[.)]\s+(.*)$/);
    if (bullet ?? numbered) {
      const want = bullet ? "ul" : "ol";
      if (list !== want) {
        closeList();
        out.push(`<${want}>`);
        list = want;
      }
      const item = bullet ?? numbered;
      out.push(`<li>${inline(item ? item[1] : "")}</li>`);
      continue;
    }

    closeList();
    out.push(`<p>${inline(line.trim())}</p>`);
  }
  if (fence !== null)
    out.push(
      `<pre class="verbatim"><code>${escapeHtml(fenced.join("\n"))}</code></pre>`,
    );
  closeList();
  return out.join("\n");
}

/** The rendered note as a node. The wrapper div is inert: every `.note-body`
 *  rule in the stylesheet is a descendant selector. */
export function renderMarkdown(text: string): ReactNode {
  return <div dangerouslySetInnerHTML={{ __html: markdownToHtml(text) }} />;
}
