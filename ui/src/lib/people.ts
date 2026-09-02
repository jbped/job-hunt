import type { Application, Person, PersonInvolvement } from "../api/types";

/** People notes name their applications in prose ("Globex — Engineer II"), not
 *  by path, so the match is on normalised company + position (index.html:1408). */
const normName = (value: string | null | undefined): string =>
  String(value || "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, " ")
    .trim();

export function involvementMatches(
  involvement: PersonInvolvement,
  app: Application,
): boolean {
  const title = normName(involvement.application);
  return (
    title.includes(normName(app.company)) && title.includes(normName(app.position))
  );
}

export function peopleFor(people: Person[], app: Application): Person[] {
  return people.filter((person) =>
    (person.applications || []).some((a) => involvementMatches(a, app)),
  );
}
