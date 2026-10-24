# Brewing rules

How to turn the picked ingredients into one skill that is better than any of them alone. Read this before writing the brew.

## Order of precedence

1. **The job sentence** the user approved. It decides what stays.
2. **The user's habits.** They beat ingredients whenever the two disagree.
3. **Ingredient techniques**, adapted to fit the two above.

If two habits conflict, or an ingredient's core idea fights the job (a skill built for open-ended questioning, a job that caps questions at three), take the job's side and note the trade-off in RECIPE.md's "Left out" column.

## The job sentence comes first

Every brew does one job. For each line you consider writing, ask whether the skill would do that job worse without it. If not, cut it. A brew that keeps everything from every ingredient becomes the kitchen-sink skill that performs worse than no skill.

## Habits become rules with reasons

Write each habit as a concrete instruction plus the reason it holds, phrased so it stays true when someone else installs the brew:

- Weak: "Write concise documents."
- Weak: "The user has asked for this repeatedly." (false once the brew is shared)
- Strong: "Keep the PRD lean and move prototype detail into a separate companion doc. A long PRD goes unread, and the prototype is easier to keep current on its own."

The reason lets the model apply the habit to cases nobody mentioned. Step 1 stored only a paraphrase; if past-chat search is available, look up the original messages behind each picked habit to get the user's exact terms and reasons before writing.

## Take techniques from ingredients, not text

From each skill ingredient, take up to three techniques that serve the job: a step order, a check, a question pattern, a format. Rewrite them in the brew's own voice and fit them to the habits. Don't paste a skill wholesale or stack two skills' procedures end to end.

**A weak ingredient.** If an ingredient turns out to add nothing to this job (a code-review skill picked for a writing job, say), take nothing from it, tell the user in one line, and offer a better-fitting swap from the live row. Don't stretch to justify the pick.

**Scripts, tools and prompt templates.** Don't copy third-party scripts, subagent prompt templates or tool setups into the brew. If that is the ingredient's real value, make the brew depend on it ("use the X skill for step 3; install it with ...") instead of vendoring it. If the user insists on including a script, list it in RECIPE.md by its path and have them review it; `bottle.py` fails on any script RECIPE.md doesn't list.

**Licenses.** Check each ingredient repo's license and record it. Rewriting ideas in your own words needs only the credit in RECIPE.md. If you copy any text, even a short passage, the license usually requires its notice to travel with it (MIT and Apache-2.0 do), so paste the notice into RECIPE.md. With no license or a restrictive one, copy nothing; take the idea only.

## Shape of a good brew

- **Frontmatter**: `name` and `description` only. claude.ai drops other keys. Don't carry over an ingredient's settings such as `disable-model-invocation`; if manual-only invocation matters, say so in RECIPE.md as a Claude Code option.
- **Description**: when to trigger, nothing else. Name the tasks and phrases that should load it, and lean slightly pushy, since skills tend to under-trigger. Under 400 characters. Quote it if it contains `: `. Don't summarize the procedure.
- **Body**: under 120 non-empty lines (`bottle.py` warns past that). A short purpose line, the procedure as numbered steps, then one or two short examples if the format matters. No persona preamble ("You are an expert..."), no filler, no empty sections.
- **Explain why, sparingly.** One clause of reason beats an all-caps MUST.
- **Leave room.** Say what good looks like and let the model handle what it can see. Over-specified steps break on the first case that doesn't fit.
- **Name**: kebab-case, at most 64 characters, without "claude" or "anthropic". Something the user would say out loud ("lean-prd", "teardown-maya").
- **Personal data**: keep client names, people's names and anything sensitive out unless the user asks. A brew may be shared later.

## Where the brew goes

Write it in your working directory as `brews/<name>/` with `SKILL.md` and `RECIPE.md`, and run the scripts by their full path inside this skill's folder.

## RECIPE.md

```markdown
# Recipe: lean-prd

Brewed by Maya on 2026-10-24 with skill-cauldron.

**Job:** Writes a lean PRD that matches the prototype, then grills the author on gaps before it ships.

## Ingredients

| Ingredient | Source | Version | License | Took | Left out |
|---|---|---|---|---|---|
| Lean PRDs | Maya's chats | 2026-10 | n/a | Lean PRD plus companion doc | n/a |
| acme-prd | Maya's skill | installed copy | private | Section order, house style | Deck styling |
| grill-me → grilling | mattpocock/skills, skills/productivity/grilling | 5beb35b, 2026-10-19 | MIT | One round of numbered questions with recommended answers | Multi-round questioning (job caps it at three) |

## Taste test

2 tasks from Maya's past chats, blind A/B, judged by Maya: brew won 2 of 2.
```

- Keep exactly one table under `## Ingredients`; `bottle.py` counts its rows. Tables in other sections are fine.
- Version is the commit hash and date for repo skills, "installed copy" for local ones, and the month for habits.
- If the brew wasn't tested, the Taste test section says "Untested." and why.

## Before you bottle

- Does the brew do the job sentence and nothing else?
- Would the user recognize their own habits in it?
- Is every ingredient credited, with what was taken and left out?
- Did `bottle.py --check-only` pass?
