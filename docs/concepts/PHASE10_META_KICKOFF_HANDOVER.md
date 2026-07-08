---
status: handover
purpose: Kickoff-Handover für den nächsten Planungs-Chat nach Phase 9 (V2). Was steht, was offen ist, wo es steht — bevor ein detaillierter Claude-Code-Plan entworfen wird.
read-when: Onboarding des nächsten Phasen-Chats (Meta-Phase); NICHT während laufender Implementierung
detail: L3
up: ./CLAUDE.md
updated: 2026-07-07
---
# Kickoff-Handover → nächste Phase (Meta-Phase) · nach Phase 9 (V2)

> Format: **Status + Delta + offene Entscheidungen + Datei-Pfade**. Keine Re-Ausschrift von
> Implementierungsdetails — **Code ist Wahrheit**. Dieser Text ist der Einstieg, nicht der Plan.
> Namensgebung `PHASE10_*` provisorisch: die nächste Phase ist per Nikinger-Entscheidung die
> **Meta-Phase** (orthogonal), nicht das ursprünglich als „V3" geplante Persistenz/UI-Paket —
> siehe offene Entscheidung **O1**.

---

## 1. Status — wo Phase 9 (V2) steht

**V2a (autonome Epic-Research) ist live end-to-end bewiesen.** Die DB-gestützte Pipeline
`discover → verify → activate` läuft ohne manuellen Code-Edit; der Neustart-Beweis
(`context built: 8 tradeable epic(s), brain=8/8`, 2026-07-07 11:31) schließt den letzten
V2a-Beweispunkt. **V2b** ist gebaut und verdrahtet (BarProvider-Kette hinter `enable_ig_bars`,
default aus; yFinance-Härtung aktiv; Divergenz-Check vorhanden). **Alle Steps 0–7a fertig,
getestet, committet, gepusht, auf Drive.** Der Baseline-Live-Lauf läuft beim Schreiben **noch**
(seit 2026-07-06, geplant ~2–3 Tage).

**Noch nicht bewiesen (kein Mechanik-Problem, marktabhängig):**
1. Ein echter `open→close`-Trade unter dem V2-Universum (bislang 0 Trades; 40+ Abstains sind
   inhaltlich on-merit begründet, Lessons sichtbar im Reasoning).
2. Variety-These (v1.5-Carry-over): sinkt die Abstain-Quote mit 8 statt 2–4 aktiven Epics?

Belege/Details (nicht hier duplizieren):
`phase9_universe/PHASE9_V2_LIVE_RESULTS_HANDOVER.md` (dated snapshot) und die Session-Blöcke
in `phase9_universe/CLAUDE.md` (Nachträge 1–3).

---

## 2. Delta seit letztem Handover (Phase-8-Closeout → jetzt)

Nur was sich strukturell geändert hat; Begründungen stehen in den referenzierten Dateien.

- **Universum ist DB-gestützt** (`instrument_universe`, Migration 004). `EXTENDED_UNIVERSE`
  ist nur noch einmaliger Seed-Input (`seed_curated`, `source="curated"`). Research liest das
  aktive DB-Universum, nicht mehr das hartkodierte Tuple.
- **`point_value` ist deterministisch code-bewiesen** (Pfad 1 `ig_fields`), freigeschaltet durch
  ein P1-Hardening (Pip-Feld-Passthrough in `get_market_info`). Der carried-over-Punkt für
  STXE/CAC/IBEX ist damit **strukturell erledigt** (D6), nicht per Behauptung.
- **Lightstreamer-Multi-Epic: NEGATIV-Befund.** Der vermutete Bug existiert nicht — 7a-Diagnose
  (live 2026-07-06) zeigte alle 4 Epics subscribing, H1–H4 alle False. 7b hat **kein Fix-Target**;
  re-run erst bei ~10+ aktiven Epics (H2-Grenze bei 4 ungeprüft). Details:
  `phase1_broker_wrapper/lightstreamer_integration_notes.md`.
- **yFinance-Härtung greift real:** yF war am 07-07 vormittags hart down (`possibly delisted`,
  30 Fehler) — **0 Quarantänen**, alle Rows `data_degraded=1` statt eingefroren. Vor dem
  C3-Fix hätte genau das das Universum stundenlang eingefroren.
- **Doc-Layers-Konvention repo-weit** (seit 2026-07-06): Root-`CLAUDE.md` 208 KB → 15 KB
  (wortgleich ausgelagert, kein Umschreiben). Neu: `docs/INDEX.md` (L0), Header-Cards (L1),
  per-Phase `SESSIONS_ARCHIVE.md` + Rotationsregel (eine Session pro Phasen-CLAUDE.md).
  Voller Spec: `docs/DOC_LAYERS_CONVENTION.md`. **Diese Navigations-Disziplin ab jetzt befolgen.**
- **Root-`CLAUDE.md` hat einen `## Working style`-Block** (2026-07-06, Fable-5-Pass) — Source-of-
  truth-Präzedenz, act-vs-ask, locked-decisions-stay-locked, faithful reporting. Vor dem Planen lesen.
- **Test-Bestand (Endstand):** P1 87 · P2 76 · P3 100 · P4 141 · P5 154 · P6 70 · P7 133 ·
  P8 217 · **P9 72** · root 77. Alle grün.
- **Phase 8 ist geschlossen** (zweiter autonomer open→close + real auslösender Safety-Breaker,
  Nikinger-bestätigt 2026-07-03) — nur zur Vollständigkeit, war beim letzten Handover noch offen.

---

## 3. Offene Entscheidungen (für den nächsten Chat, vor dem Plan)

- **O1 — Welche Phase ist als nächstes, und wie nummeriert?** Nikinger-Spoiler (2026-07-07):
  die nächste Phase ist die **Meta-Phase (Harness-Unabhängigkeit)**. Sie ist **orthogonal** zum
  funktionalen Strang und damit kein echtes „V3". Das ROADMAP-geplante V3 (Persistenz-Reform +
  No-Trade-Lessons + UI) bleibt separat bestehen. Der nächste Chat muss Einschubpunkt/Strang und
  Nummerierung festlegen. Konzept: `docs/concepts/meta_phase_unabhaengigkeit_konzept.md` (bzw. im
  Repo unter dem geführten Namen) — Status dort: **Vorschlag, nicht gelockt**.
- **O2 — Δ und X vorregistrieren (Meta-Phase, Decision F/G).** Bevor **irgendein** Bake-off-Trial
  läuft, müssen `Δ` (max. akzeptierter Build-Gate-Pass-Abstand) und `X` (Ausfall-Erwartungswert =
  P(Anthropic für mich unbrauchbar in 12 Mon.) × Kosten eines ~2-Wochen-Ausfalls) **schriftlich**
  stehen. Nachträgliches Setzen = „nach migrationsfreundlichem Ergebnis shoppen", im Konzept
  explizit verboten. Das ist die erste inhaltliche Handlung der Meta-Phase, nicht Code.
- **O3 — P4/P6-Laufzeit-Swap: in der Meta-Phase oder später?** (Decision H, offen.) Empfehlung
  des Konzepts: Build-Front zuerst (billig, throwaway-Fork), Laufzeit-Swap als eigener späterer
  Schritt. Bestätigen oder umstoßen.
- **O4 — Baseline-Lauf: laufen lassen, dann was?** Der Lauf soll ~2–3 Tage weiterlaufen. Die zwei
  offenen V2-Beweispunkte (echter Trade, Variety-These) sind **kein** Blocker für den Start der
  Meta-Phase (orthogonal), aber jemand muss entscheiden, ob vor der Meta-Phase noch ein
  V2-Abschluss-Auswertungsschritt eingeschoben wird.

---

## 4. Watch-Items (klein, bewusst NICHT am laufenden System gefixt — Kontext, keine To-dos)

- **`fail_count`-Reset-Lücke: bereits gefixt** (Nachtrag 3, +1 Test → P9 72). Nur erwähnt, damit
  niemand sie erneut „entdeckt". Live-DAX heilte ohne DB-Eingriff.
- **Mid-Run-Propagation:** Universums-Änderungen erreichen Research **erst per Neustart**
  (Step-5-Wiring-Designentscheidung, kein Bug). Dokumentiert als möglicher **V3-Kandidat**
  „Universe-Rebuild pro Refresh".
- **yFinance-Zuverlässigkeit der VM:** intermittierend ganztags. Mit C3 nur Signalverlust; die
  strukturelle Antwort ist die V2b-Kette (IG-primär) — deren Scharf-Beobachtungslauf
  (`--enable-ig-bars`, `bar_fetch`-Events) steht noch aus und ist gerade attraktiv.

---

## 5. Datei-Pfade (Einstiegspunkte, nicht lesen bis gebraucht)

- **Aktueller Stand + Navigation:** `CLAUDE.md` (root, 15 KB) → `docs/INDEX.md` (L0-Karte).
- **Phasen-Kopf V2 (As-Built, Session-Blöcke, Test-/Wiring-Konventionen):** `phase9_universe/CLAUDE.md`.
- **Live-Ergebnisse (dated snapshot):** `phase9_universe/PHASE9_V2_LIVE_RESULTS_HANDOVER.md`.
- **Voller V2-Plan (Referenz, nicht neu herleiten):** `docs/concepts/phase9_v2_foundation_plan.md`.
- **Meta-Phasen-Konzept (nächste Phase, Vorschlag):** `docs/concepts/meta_phase_unabhaengigkeit_konzept.md`.
- **Roadmap-Buckets (Phase 9/10/11):** `ROADMAP.md`. **Architektur:** `ARCHITECTURE.md`.
- **Doc-/Session-Konvention:** `docs/DOC_LAYERS_CONVENTION.md`.
- **LS-Diagnose-Befund:** `phase1_broker_wrapper/lightstreamer_integration_notes.md`.
- **Cross-Phase-Edit-Register V2:** in `phase9_universe/CLAUDE.md` (Pointer) → Plan §11 (Details).

---

## 6. Ein Satz für den kalten Leser

Phase 9 hat die zwei strukturellen Lücken des v1.5→v1.7-Hotfix-Arcs geschlossen (autonome
Epic-Research + gehärteter Datenpfad) und live bewiesen; die nächste Phase ist **orthogonal** —
eine vorregistrierte Messung, ob sich der Bot künftig mit einem offenen Harness statt Claude Code
bauen lässt, **ohne** Δ und X vorher zu setzen wird sie wertlos.
