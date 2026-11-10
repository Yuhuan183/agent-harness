# Diagrams

Use a diagram when the reader must see a structure that prose shows badly.
Write the diagram as Mermaid source in the Markdown file. GitHub renders
Mermaid blocks without a build step.

## Diagram type for each question

| Question | Diagram | Mermaid keyword |
|---|---|---|
| What happens in which order, and where does it branch? | Flowchart | `flowchart TD` |
| Which states exist, and what moves the system between them? | State diagram | `stateDiagram-v2` |
| Which actor sends what to whom, and when? | Sequence diagram | `sequenceDiagram` |
| What contains what? | Tree | `flowchart TD` without cycles, or `mindmap` |
| Which types exist, and how do they relate? | UML class diagram | `classDiagram` |
| Which entities store data, and how do they link? | Entity relationship diagram | `erDiagram` |

## Rules

- Draw one question in each diagram. Split a diagram that answers two.
- Use the same terms in the diagram and in the text.
- Put one paragraph of text after each diagram. The text must give the same
  result as the diagram, so a reader without the picture loses nothing.
- Keep a diagram to about 15 nodes. Split a larger one.
- If a document needs an image file, store it as SVG under
  `docs/assets/<document-name>/`. Keep the source file beside it, with the same
  base name.

## Render and check

`scripts/render-diagrams.py` in the agent-harness repository checks the Mermaid
blocks in Markdown files. It also exports `.mmd` sources to SVG. It runs a
pinned `@mermaid-js/mermaid-cli` through `npx`.
