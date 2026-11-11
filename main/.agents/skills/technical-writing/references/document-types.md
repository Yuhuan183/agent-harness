# Document types

Pick the type before you write. The type sets the sections and their order.
The sentence rules in [SKILL.md](../SKILL.md) apply to every type.

Write one type in each document. If a document must hold two types, give each
type its own section. For example, keep measured results apart from the rules
of a spec.

## Types and their sections

| Type | Question for the reader | Sections, in order |
|---|---|---|
| Spec | What does the system do, why, and how do we check it? | See [Spec](#spec) |
| Design | Which option do we choose, and why? | Context, goals and non-goals, options, chosen design, risks, decision |
| Explainer | How does this part work? | Summary, concept diagram, parts, data flow, limits |
| Operations | How do I do this task? | Purpose, prerequisites, warnings, numbered steps, check, rollback |
| README or index | What is this, and where do I start? | Purpose in one paragraph, entry table by reader goal, links to owners |
| Record | What happened, and what did we decide? | Date, context, result or decision, evidence. Add entries only at the end |

## Spec

The user chose a work spec as the reference on 2026-11-10. This section
distills how that spec makes its purpose, its scenarios, its process, and its
results clear. Use it as the pattern for a spec about system behavior.

### Sections, in order

1. Goal and scope. The first paragraph gives the problem, the behavior, the
   limit, and the fallback. If the design follows a known model, name it in
   one clause. Then list the covered cases in a table. Use the names that the
   code uses.
2. Overview. Show the whole flow before any detail. Give a diagram, a
   paragraph that says the same thing, a state table, and the invariants. An
   invariant is always true, for example "one page sends one reload at most."
3. Scenarios. See [Scenarios](#scenarios).
4. Rules, with one section for each mechanism. Use a table for a decision, a
   list for timing, and a parameter table with constant names.
5. Interface: each UI text as the user sees it, and its text key.
6. Observability: a table that gives each event, the time when it is sent, and
   how it is sent. Then list the fields. Say which existing events do not
   change.
7. Acceptance: each row gives the scenario, the action, and the expected
   result. Include a row for real devices.
8. Header and change log, if the platform does not record the owner, the
   status, and the history.

### Scenarios

- Before the first scenario, state the template that each scenario follows.
  State where the numbers come from, and that real values can differ.
- Name each scenario by the condition that the user sees, not by an internal
  state. Example: "The network fails, then it recovers."
- Start each scenario with an example from real life: a lift, a hotel Wi-Fi
  login page, an ad blocker, a release during the outage.
- Choose scenarios that cover the decision space:
  - the normal recovery
  - a failure that does not end
  - a partial failure
  - a case where the system must do nothing
  - a false signal
  - a different entry point
  - a change on the server side
- In each step, say what the user sees and what the system does.
- Use numbered steps when the order matters. Use bullets for independent facts.
- End each scenario with the result that the user sees. If the result costs
  some users an extra action, say so.
- Put a follow-up case in the same scenario, under a bold label, at the point
  where the reader asks the question. Example: "**If the check also fails:**".
- If a measured run exists, add it after the steps under the label
  "Measured". Use the field names that the logs use. When you can, add the
  date and the build.

### Reasons

- Put the reason next to the rule or the step that it explains.
- Write the reason as the bad result that the rule prevents. Example: "so a
  slow network is not taken as a failure."
- Give each prohibition its reason, so that a later maintainer does not undo
  it. Example: "Do not use HEAD. WebKit does not fetch the failed module
  again."
- Say what the system does not do when a reader can expect it to. Example:
  "There is no time-out rule, so a slow network only loads slowly."

### Names and numbers

- Use the same identifiers in the scope table, the scenarios, the rules, and
  the log fields. The reader can then follow one name from start to end.
- Put each number in one row of the parameter table, with a name and a unit.
  In other sections, use the name.
- Write each identifier, constant, storage key, event name, and file name in
  code format.

### Diagrams

Use a flowchart or a state diagram for the overview. Put a paragraph after it
that gives the same result. Use a sequence diagram when a message crosses a
page reload or a process boundary. [diagrams.md](diagrams.md) gives the rules
for each diagram.

## Review checklist for a spec

1. After the first paragraph, can the reader state the goal, the limit, and
   the fallback?
2. Does the overview show the whole flow before the details?
3. Does each scenario start with a real example and end with the result that
   the user sees?
4. Do the scenarios include a case where the system must do nothing?
5. Does each step say what the user sees and what the system does?
6. Does each rule and each prohibition have its reason next to it?
7. Does each name mean the same thing in every section and in the logs?
8. Is each number in the parameter table, one time, with one unit?
9. Does each diagram have a paragraph after it that gives the same result?
10. Does each scenario have an acceptance row?
