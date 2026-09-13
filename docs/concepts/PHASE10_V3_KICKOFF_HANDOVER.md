---
status: handover
purpose: Kickoff-Handover für den Phase-10/V3-Planungschat (Abstain-Lessons + Persistenz-Reform
  + Daten-Vorbereitung). Geschrieben vom M1-Wrap-up-Chat nach Nikinger-Freigabe der
  Priorisierung (V3 vor M2). Einstiegspunkt, keine Plan-Kopie — Code ist Wahrheit.
read-when: Start des V3-Planungschats, VOR dem Entwurf des detaillierten Claude-Code-Plans
detail: L3
up: ../../phase10_v3/CLAUDE.md
updated: 2026-07-09
---

# PHASE10_V3_KICKOFF_HANDOVER → V3-Planungschat

> Format: **Status + Delta seit letztem Handover + offene Entscheidungen + Datei-Pfade.**
> Keine Implementierungsdetails, die schon in Code, Tests oder Plan-Docs stehen.
> Companion: `meta_m1_harness/META_M1_CLOSEOUT_HANDOVER.md` (schließt M1); dieses Dokument
> eröffnet V3.

---

## 1. Status

**M1 ist geschlossen** — 20/20 Trials, Gap 0,00 pp („nicht unterscheidbar"), Entscheidung
per vorregistrierter Regel: keine Migration; Feuerlöscher beidseitig belegt (OpenCode als
Build-Pfad + kalter OpenRouter-Fallback mit Smoke-PASS). Alles Weitere: Closeout-Handover,
nicht hier duplizieren.

**Der Bot läuft wieder** (Baseline-Datensammlung unter dem V2-Universum, 8 aktive Epics).
Daraus folgt die harte Arbeitsteilung dieser Phase: **Bot-berührende Steps nur am
Wochenende** (Markt zu, Bot steht ohnehin); **wochentags nur docs-only/read-only-Arbeit.**
Der Planungschat muss jeden Step explizit einem der beiden Fenster zuordnen.

**Priorisierung (Nikinger-Entscheidung 2026-07-09):** V3 jetzt, M2 geparkt. Begründung im
Kurzform-Protokoll: zwei Meta-Phasen in Folge, während der Bot aus 40+ Abstains nichts
lernt, wäre Werkzeug-Optimierung als Prokrastination; M2 hat keine Deadline und heute
Entscheidungswert ≈ 0.

**Fork-Klarstellung (Nikinger, wichtig gegen Verwechslung):** Der Bake-off-Fork ist bewusst
als **Wegwerf-Instrument für Meta-Phasen** konzipiert und bleibt das auch. Der echte
V3-Build findet **auf main am Haupt-Bot** statt — nichts aus dem Fork wird gemerged, der
Fork ist keine Vorstufe des echten Builds, nur die Specs wandern (als Text) mit.

## 2. Delta seit `PHASE10_META_KICKOFF_HANDOVER.md`

- M1 komplett durchgeführt und geschlossen (Details: Closeout §1–§2, inkl. aller bewusster
  Plan-Drifts — u. a. Effort high statt medium, keyring-only-Auth, `--dir`+Write-Lock nach
  realem Fork-Ausbruch, Cost-JSON-Parsing).
- **Specs S1–S7 existieren als fertiger, zweifach real durchgebauter Bauplan** für das
  Abstain-Lessons-Modul (`meta_m1_harness/specs/`). Der V3-Chat plant damit NICHT von null:
  Hauptarbeit ist Contract-Verifikation gegen den echten Executor/Runner (die Specs haben
  ihre Input-Contracts bewusst selbst definiert — `[VERIFY]` gegen As-Built ist Pflicht,
  Datei-/Symbol-Anker inklusive) plus Persistenz-Entscheidungen (§3).
- `AGENTS.md` (Root) und `OpenAICompatLLMClient` (kalt, additiv) liegen auf main.
- ROADMAP trägt den Meta-Strang; funktionale Nummerierung unverändert (Phase 10 = V3).

## 3. Auftrag an den V3-Planungschat

Detaillierten Claude-Code-Plan schreiben (Format wie gehabt: gelockte Decision-Tabelle mit
Empfehlungen zuerst, Schritt-Sequenz, exakte Namen, Anker mit `[VERIFY]`, Testlisten,
Akzeptanzkriterien). Scope in drei Blöcken + Standard-Housekeeping:

**Step 0 — Daten-Auswertung & -Vorbereitung (docs-only, wochentagstauglich; Nikinger-
Vorschlag 2026-07-09):** Die bereits laufende Datensammlung auswerten UND für V3
vorbereiten. Konkret: (a) V2-Baseline-Auswertung nachholen — erster echter open→close-Trade
unter V2? Variety-These (Abstain-Quote bei 8 Epics)? (b) Abstain-Ist-Analyse: welche
Abstain-Gründe dominieren real in `debate_log.json` / `research_health.jsonl` /
Scheduler-State — als empirische Gewichtung der REASON_*-Taxonomie aus S1. (c) Gap-Check:
loggt der laufende Bot heute schon alles, was Abstain-Klassifizierer (S2-Contract) und
Persistenz-Reform-Schema später brauchen? Fehlende Felder nur **identifizieren und
dokumentieren** — nichts am laufenden Bot ändern. Output: kurzes dated Analyse-Doc, das
die V3-Decisions informiert.

**Block A — Abstain-/No-Trade-Lessons echt (Bot-berührend → Wochenende):** S1–S7 als
Bauplan übernehmen; Contracts/Anker gegen As-Built verifizieren; Wiring-Nähte (S5-Muster:
`abstain_sink` default None, bit-identisch) real setzen. Bekannt aus M1: die
bare-pytest-/`__init__.py`-Sensitivität der Specs — beim echten Build irrelevant machen
(normale Projekt-Konventionen gelten), aber wissen, dass sie existiert.

**Block B — Persistenz-Reform (Bot-berührend → Wochenende):** Marktregime-Snapshots pro
Trade (Volatilität, Spread, Tageszeit) + Entscheidungskontext (Bull/Bear-Argumente,
VETO-Faktoren, Confidence-Verlauf). Scope-Schnitt ist eine offene Decision (§4) — Step 0
liefert die Datengrundlage dafür.

**Block C — UI (optional, fällt zuerst):** nur wenn A+B stehen; nie vor Safety.

## 4. Offene Entscheidungen für den V3-Chat

1. **Persistenz-Mechanik Abstain-Store:** S3 baute bewusst einen eigenständigen Store
   (Fork-Pragmatik). Echt-Build: eigener Store beibehalten oder ins P2-Migrationsframework
   (nächste Migrations-Nr. `[VERIFY]`, nach 004)? Empfehlungspflicht im Plan.
2. **Paket-Ort:** `phase10_v3/abstain_lessons/` bestätigen oder umschneiden (V3 umfasst
   mehr als dieses Modul).
3. **S6 (Research-Injektion der Lessons in den P4-Prompt):** V3-Scope oder V4 (gated auf
   reale Outcomes)? Berührt die Lern-Schleife — konservativ entscheiden.
4. **Scope-Schnitt Persistenz-Reform:** was genau in V3, was bleibt V4 (Lesson-Embeddings
   sind explizit langfristig).
5. **M2 ja/wann:** geparkter Seed in Closeout §3 (Code-Qualität, ganze Configs, braucht
   eigene Metrik + eigene Preregistration). Kein V3-Blocker; frühestens Wochentags-Abende
   nach V3-Start.

## 5. Geparkt / Watch-Items (Kontext, keine V3-Pflicht)

- **Safety-Breaker-Fire (5b)** — seit P8 nie live demonstriert.
- **point_value EuroStoxx/CAC/IBEX** — strukturell via Resolver erledigt, vor JEDEM
  Live-Konto hart bestätigen.
- **yFinance-Root-Cause** ungepinnt; P1-Lightstreamer nie in den Research-Datenpfad
  verdrahtet.
- **Decision H** (echter P4/P6-Laufzeit-Swap) — bewusst vertagt, Fallback liegt kalt.

## 6. Datei-Pfade (Einstiegspunkte, erst bei Bedarf lesen)

- M1-Abschluss: `meta_m1_harness/META_M1_CLOSEOUT_HANDOVER.md` (→ RESULTS/DECISION/
  PREREGISTRATION daneben).
- Bauplan-Specs: `meta_m1_harness/specs/S1…S7.md`; Struktur-Vorbild Plan:
  `docs/concepts/meta_m1_harness_plan.md`.
- Kalter Fallback: `phase4_research/research/llm_openai_compat.py`.
- Datenquellen für Step 0: `data/state/debate_log.json`, `data/state/research_health.jsonl`,
  `data/trading_bot.sqlite` (Pfade `[VERIFY]` gegen As-Built).
- Harness-neutraler Einstieg: `AGENTS.md` (Root); Konventionen: `docs/DOC_LAYERS_CONVENTION.md`.
- Roadmap: `ROADMAP.md` (Phase 10 = V3; `## Meta-Strang` separat).

## 7. Ein Satz für den Kaltleser

M1 hat die Werkzeugfrage abgeschlossen und als Nebenprodukt den Bauplan für V3s wichtigstes
Modul geliefert — V3 macht den Bot jetzt lernfähig aus seinen eigenen Abstains, beginnend
mit einer docs-only-Auswertung der Daten, die er gerade sammelt, gebaut wird am Wochenende
auf main, und der Wegwerf-Fork bleibt, was er ist: ein Messinstrument.
