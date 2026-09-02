import { useState } from "react";
import { useIndexQuery, useSchemaQuery } from "../api/queries";
import { useFormModal } from "../components/FormModal";
import { ObsidianLink } from "../components/NoteViewer";
import PersonCard from "./people/PersonCard";
import Network from "./people/Network";

/** Port of `renderPeople()`'s folder grouping (index.html:1328): people are
 *  bucketed by `folder`, folders ordered per `schema.people_folders` with
 *  "Unfiled" last; the heading is suppressed when everyone shares one folder. */
export default function PeopleView() {
  const index = useIndexQuery().data;
  const schema = useSchemaQuery().data;
  const openForm = useFormModal();
  const [openEditors, setOpenEditors] = useState<Set<string>>(new Set());

  const people = index?.people ?? [];
  const byFolder = new Map<string, typeof people>();
  for (const person of people) {
    const key = person.folder || "Unfiled";
    if (!byFolder.has(key)) byFolder.set(key, []);
    byFolder.get(key)!.push(person);
  }
  const order = [...(schema?.people_folders ?? []), "Unfiled"];
  const folders = [...byFolder.keys()].sort((a, b) => {
    const ia = order.indexOf(a);
    const ib = order.indexOf(b);
    return (ia < 0 ? order.length : ia) - (ib < 0 ? order.length : ib);
  });

  function toggle(path: string, nextOpen: boolean) {
    setOpenEditors((current) => {
      const next = new Set(current);
      if (nextOpen) next.add(path);
      else next.delete(path);
      return next;
    });
  }

  return (
    <section data-view="people" data-active="">
      <div className="actionbar">
        <button className="btn btn-primary" id="addPerson" onClick={() => void openForm("person")}>
          Add person
        </button>
        <span className="hint">
          One note per person — professional history, job-search roles, and reference consent stay
          distinct on that note.
        </span>
      </div>
      <h2>People</h2>
      <div id="people">
        {!people.length ? (
          <div className="empty">
            "Add person" records both how you worked together and any role they play in your job search. A
            referral is not automatically a reference.
          </div>
        ) : (
          folders.map((folderName) => (
            <div key={folderName}>
              {byFolder.size > 1 || folderName !== "Unfiled" ? <h3 className="muted">{folderName}</h3> : null}
              {byFolder.get(folderName)!.map((person) => (
                <PersonCard
                  key={person.path}
                  person={person}
                  open={openEditors.has(person.path)}
                  onToggle={(next) => toggle(person.path, next)}
                />
              ))}
            </div>
          ))
        )}
      </div>
      <h2>Introductions</h2>
      <p className="muted">
        Chains built from each person's <code>via</code> field: target ← the person whose introduction
        makes them reachable.
      </p>
      <div id="network">
        <Network people={people} />
      </div>
      <h2>Application contacts</h2>
      <p className="muted">
        Per-application involvement, recorded in each application's Contacts note. The person's own
        details live on their People note.
      </p>
      <div id="contacts">
        {!index?.contacts.length ? (
          <div className="empty">No application contacts yet. Add one from an application's Actions.</div>
        ) : (
          <div className="card scroll">
            <table>
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Role</th>
                  <th>Company</th>
                  <th>Follow-up</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {index.contacts.map((c, i) => (
                  <tr key={i}>
                    <td>
                      <span className="title">{c.name}</span>
                    </td>
                    <td>
                      <span className="muted">{c.application_role || "—"}</span>
                    </td>
                    <td>{c.company}</td>
                    <td>
                      <span className="muted">{c.next_follow_up || "—"}</span>
                    </td>
                    <td>
                      <ObsidianLink path={c.note} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </section>
  );
}
