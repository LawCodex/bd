# LawCodex — Bangladesh (`bd`)

Legislation of the People's Republic of Bangladesh as plain Markdown, one file per law, taken from
**Laws of Bangladesh** (<http://bdlaws.minlaw.gov.bd>), the official consolidated database of the
Legislative and Parliamentary Affairs Division, Ministry of Law, Justice and Parliamentary Affairs.

Part of [LawCodex](https://github.com/LawCodex): the laws of every country as Markdown in git.

Retrieved: 2026-10-12. **1,348 files.**

## Contents

| Category | Directory | Files |
|---|---|---:|
| Constitution of the People's Republic of Bangladesh — English text | `constitution/constitution-en.md` | 1 |
| গণপ্রজাতন্ত্রী বাংলাদেশের সংবিধান — Bangla text | `constitution/constitution-bn.md` | 1 |
| Acts (incl. Bengal / East Bengal / East Pakistan Acts still in force) | `laws/<year>/` | 1,076 |
| Ordinances | `laws/<year>/` | 159 |
| President's Orders | `laws/<year>/` | 71 |
| Regulations (Bengal Regulations 1799–1833 etc.) | `laws/<year>/` | 40 |
| **Total** | | **1,348** |

The laws span 1799–2026 (162 year directories). 603 laws are in English (generally those enacted
before 1987, when Bangla became the language of legislation) and 743 in Bangla; each law is published
in the language the source gives it in (the source does not provide translations).

18 ordinances are marked `status: repealed` with `status_note: "lapsed ..."`: the source keeps them in
its list but prints that they have lapsed under article 93(2) of the Constitution.

### Not covered

- The 334 laws the source's chronological index marks as **[Repealed]** (their pages only carry the
  repeal note).
- **Schedules and appendices published as separate PDF files** (742 laws, including the Constitution's
  schedules): they are not converted, but their official URLs are listed in the front matter
  (`attachments`) and at the end of each file.
- Subordinate legislation (rules, notifications, SROs) — not in the source database.

## Structure

```
constitution/constitution-en.md, constitution-bn.md
laws/<year>/act-<bdlaws-id>[-<english-title-slug>].md
```

`<bdlaws-id>` is the identifier used by bdlaws.minlaw.gov.bd (`act-<id>.html`). Laws with a Bangla
title have no slug. The title in its original script is in the front matter and the H1.

Front matter: `title`, `identifier` (e.g. `ACT NO. XXI OF 1860`, `২০২৬ সনের ০২ নং অধ্যাদেশ`),
`bdlaws_id`, `type` (`constitution`, `act`, `ordinance`, `order`, `regulation`), `jurisdiction`,
`language` (`en` or `bn`), `date` (date of assent/promulgation as printed by the source),
`status`, `attachments`, `source`, `retrieved`.

Body: the long title / preamble, then `## Part`, `### Chapter`, cross-headings in bold, and
`#### <number>. <marginal heading>` for each section followed by its text. Amendment footnote markers
are `<sup>n</sup>` and the footnotes themselves are listed at the end under *Footnotes* / *পাদটীকা*,
as on the source.

## Sources

- Laws of Bangladesh — <http://bdlaws.minlaw.gov.bd>: chronological index
  (`/laws-of-bangladesh-chronological-index.html`), full text pages (`/act-details-<id>.html`) and
  summary pages (`/act-<id>.html`, for the schedule PDF links). Pages are served as UTF-16.
- No robots.txt; no terms of use restricting reuse were found on the site. Requests were made at
  ≤ 3 in parallel with a 1-second delay per worker.

## Licence

Laws of Bangladesh are official public texts. This compilation adds no copyrightable content.

## Regenerate

```
pip install -r scripts/requirements.txt
python scripts/bd_fetch.py      # caches pages under ../_raw/bd
python scripts/bd_convert.py .  # writes the Markdown files
```
