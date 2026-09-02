import type { Person } from "../../api/types";
import { ObsidianLink } from "../../components/NoteViewer";

/** Wikilink values ("[[People/Network/Jo Doe]]") display as their leaf name
 *  (`inlineText()`, index.html:1199). */
function inlineText(value: string | null | undefined): string {
  const match = /^\[\[([^\]]+)\]\]$/.exec(String(value ?? "").trim());
  return match ? (match[1].split("|").pop() ?? match[1]).split("/").pop()! : (value ?? "");
}

interface Chain {
  chain: Person[];
  missing: string | null;
}

/** Port of `renderNetwork()` (index.html:1373): introduction chains walked
 *  through each person's `via` field until it ends, goes missing, or loops. */
export default function Network({ people }: { people: Person[] }) {
  const byLeaf = new Map<string, Person>();
  for (const p of people) {
    byLeaf.set(String(p.name).toLowerCase(), p);
    byLeaf.set(
      p.path
        .replace(/\.md$/, "")
        .split("/")
        .pop()!
        .toLowerCase(),
      p,
    );
  }
  const resolveVia = (value: string): Person | undefined => {
    const leaf = inlineText(value).toLowerCase();
    return leaf ? byLeaf.get(leaf) : undefined;
  };

  const chains: Chain[] = [];
  const dangling: Chain[] = [];
  for (const person of people.filter((p) => p.via)) {
    const chain = [person];
    const seen = new Set([person.path]);
    let current: Person | undefined = person;
    let missing: string | null = null;
    while (current && current.via) {
      const next = resolveVia(current.via);
      if (!next) {
        missing = inlineText(current.via);
        break;
      }
      if (seen.has(next.path)) break;
      chain.push(next);
      seen.add(next.path);
      current = next;
    }
    (missing ? dangling : chains).push({ chain, missing });
  }

  if (!chains.length && !dangling.length)
    return (
      <div className="empty">
        No introduction chains yet. Set "Via" on a person to record who the introduction runs through.
      </div>
    );

  return (
    <>
      {chains.map(({ chain }, i) => (
        <div className="card row" key={i}>
          <span className="grow title">{chain.map((p) => p.name).join(" ← ")}</span>
          {(chain[0].relationships ?? []).map((r) => (
            <span className="pill" key={r}>
              {r}
            </span>
          ))}
          <ObsidianLink path={chain[0].path} />
        </div>
      ))}
      {dangling.length ? (
        <>
          <div className="group-label">Missing connector notes</div>
          {dangling.map(({ chain, missing }, i) => (
            <div className="card row" key={i}>
              <span className="grow">
                <span className="title">{`${chain.map((p) => p.name).join(" ← ")} ← ${missing}`}</span>
                <div className="muted">{`"${missing}" has no People note yet — add one so the chain resolves.`}</div>
              </span>
              <ObsidianLink path={chain[0].path} />
            </div>
          ))}
        </>
      ) : null}
    </>
  );
}
