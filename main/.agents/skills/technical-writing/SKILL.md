---
name: technical-writing
description: |
  House rules for non-creative text in English or zh-TW: specs, docs, work documents, runtime files, briefs, commit messages, code comments, and technical replies. Use before you write or review such text.
  觸發：寫或審規格、文件、工作文件、技術回覆、commit、註解；「照規範寫」「STE」「這份文件好讀嗎」。
  不觸發：行銷文案、社群貼文、故事等創意文字（用 readable-zh-tw）。
---

# Technical Writing

This skill sets controlled-language rules for non-creative text. The rules adapt
the concepts of ASD-STE100 Simplified Technical English. They do not copy the
STE specification or its dictionary. Creative text, such as marketing copy and
social posts, is out of scope: use `readable-zh-tw` for it.

## Structure

- Put the result, the rule, or the decision first. Put the background after it.
- Write one topic in each section and in each paragraph. Keep a paragraph to six
  sentences or fewer.
- Use a numbered list for steps in sequence. Use a bulleted list for independent
  items. Keep a reasoning chain, which joins sentences with because, so, or
  unless, in prose.
- Put a warning before the step that it applies to.
- Give each number one source. Name it, as a constant or a table row, and refer
  to the name in other places. Use one unit for one quantity.
- Use a diagram when a picture shows the structure better than prose. Put one
  paragraph of text after each diagram. `references/diagrams.md` gives the
  diagram type for each question.

## Sentences

- Write one fact or one instruction in each sentence.
- Put the condition before the action: "If X, do Y."
- Use the active voice. Name the actor when the reader cannot see it.
- Use one term for one concept. Use the term that the project glossary gives.
  Do not change a term for variety.
- Write a requirement with a requirement word, and only then. English: must,
  must not, should, may. zh-TW: 必須, 不得, 應該, 可以. Write behavior that the
  text only describes as a plain statement.
- Put the reason for a rule in a separate sentence after the rule.

## English

- Keep a procedural sentence to 20 words or fewer. Keep a descriptive sentence
  to 25 words or fewer.
- Write an instruction as a command.
- Use the simple tenses: present, past, and future.
- Do not stack more than three nouns. Rewrite "dispatch outcome ledger record"
  as "the ledger record of the dispatch outcome".
- Use a verb, not a noun made from a verb: "verify the pin", not "perform
  verification of the pin".

## zh-TW

STE has no Chinese dictionary, so these rules carry its concepts to Chinese.

- Keep a sentence to about 60 characters. Split a sentence that carries two
  facts.
- Write the subject when the actor is not clear from the sentence before.
- Do not chain three or more 的 modifiers in one sentence. Split the sentence.
- Taiwan terms, punctuation, and the removal of AI patterns follow
  `readable-zh-tw`.

## Glossary

A project keeps its approved terms in `docs/glossary.tsv`. Each row has the
approved term, a tab, and the rejected variants separated by `|`. Add a term
when two spellings of one concept appear. Do not add a term that only one
document uses.

## Check

Run `~/.agents/skills/technical-writing/scripts/writing-lint <files>`, with
`--glossary docs/glossary.tsv` when the project has one. The lint reports long
sentences, likely passive voice, chained 的 modifiers, and rejected terms. It only reports; it does not block.
Treat each finding as a question for the writer, not as a verdict.
