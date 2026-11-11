# Coverage: how much of a set the evidence has to reach

The ladder next door answers *how hard* to check one thing. This answers *how many* things.
That is the other way a conclusion goes wrong: you inspect every item you open properly, and
never open the ones that mattered.

Sampling is the default failure because it is invisible. A report that read three of forty
files looks exactly like a report that read forty, unless someone says which.

## The dial

One setting for the whole task, three notches. Breadth and depth move together, because in
practice they do:

| Notch | Breadth | Depth per item | Buys |
|---|---|---|---|
| `Sample` | a few representatives | read it | a feel for the shape, fast |
| `One per category` | every kind of case, at least once | actually exercised | no whole class goes unseen |
| `Every item` | all of them | evidence you can cite per item | a per-item answer |

Ask for it **once**, before starting, and only when breadth actually decides the answer. A task
whose conclusion does not depend on how much you read needs no dial and no question.

State the cost of the cheap notch when you ask. "Sample, and the check can miss individual
exceptions" is a decision the user can make; "Sample" alone is one they cannot.

## The one thing that is not a question

A step whose output feeds an action that cannot be undone takes `Every item`, whatever the dial
says, and without asking. The actions are already enumerated, identically, in three role
contracts: **push, deploy, publish, send, delete shared data**.

This is what keeps the mechanism cheap. The task does not spread precision evenly; it spends
precision where nobody can recover a miss, and the dial governs everything else.

## Why one question and not one per step

A task with many steps has many places where breadth matters. Asking at each one is how a
useful rule becomes an interruption the user turns off.

The steps differ in exactly one variable: whether someone can undo a mistake. The action
decides that variable, not the user. So it is a rule, not a question. Everything else
inherits the single dial:

```text
task starts
   │
   ├─ does breadth decide the answer? ── no ──→ no dial, no question
   │            │ yes
   │            ▼
   │      ask once, three notches ──→ dial is set
   │
   └─ each later step:
         feeds something irreversible?
            │ yes                      │ no
            ▼                          ▼
      `Every item`, no ask        the dial, no ask
```

## The one thing that reopens it

Sampling rests on a premise: the items are alike enough that a few stand for the rest. A
counterexample kills that premise — and it is the only finding that must go back to the user
before the task continues.

Say three things: which item broke the pattern, what that implies the sample cannot support,
and what the next notch would cost. Do not silently upgrade the dial. The user chose it with a
budget in mind, and the counterexample may be the cheap kind they already expected.

## Reading an inherited claim

This applies to someone else's report as much as to your own work. "No other occurrences", "all
call sites updated", and "the rest are the same" are coverage claims. A coverage claim with no
stated breadth is worth what a sample is worth. Ask what the author actually opened, or open it.
