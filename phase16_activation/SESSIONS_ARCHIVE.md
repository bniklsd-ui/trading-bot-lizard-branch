# SESSIONS_ARCHIVE.md — Phase 16 (Freischaltung)

Newest-first. Rotation rule (root `CLAUDE.md`, mandatory since 2026-07-06): the phase head
carries exactly one `## Session stopped` block; archives have no size cap. See
[`../CLAUDE.md`](../CLAUDE.md) "Rotation rule (mandatory since 2026-07-06)" for the full
contract, and [`../docs/DOC_LAYERS_CONVENTION.md`](../docs/DOC_LAYERS_CONVENTION.md) for
the L0/L1/L2/L3 model.

Plan-Session-Block trägt bewusst **keine** `Session #N`-Nummer im Heading (Phase-15-Vorbild
„Plan-Session, Opus 5") — das P14-F-Step-2-Regex `_SESSION_NUM_RE` matcht darauf nicht;
`_max_session_num` returnt `None`; für die erste Exec-Session (`head_max == 1`) ist das
Archiv-Max `None` korrekt (check_archive_sequence, Z. 134-138).

---

## Session stopped — 2026-09-05 (Plan-Session, Fable 5.1 — Phase 16 eröffnet, Plan committet)

> **Auftrag:** Nikinger-Chat 2026-09-05: „Phase 16 sollte mind. alle Löcher, die der Bot noch hat,
> stopfen, sodass alle Funktionen freigeschaltet werden, und nach Phase 16 ein ausgiebiger Test
> von z. B. 2 Wochen komplett autonom." Plan bis Ausführungsreife, Fragen gebündelt vorab,
> Advisor-Ersatz per Agent (Opus vor dem Festlegen, Sonnet-Cold-Read vor „fertig").

### Completed
- **Recherche read-only** (Live-DB `mode=ro`, Logs, `/proc`, git): 9 Löcher L1–L9 verifiziert
  (Plan §3), Σ-Baseline **1843** selbst gemessen (Plan §2.1), 7 Commits lokal ahead (`2f9eb82`).
- **Nikinger-Fragerunde** (10 Entscheidungen, alle gelockt → Plan §1 P1–P17).
- **Opus-Plan-Agent-Review** (Plan §13): 3 Struktur-Änderungen übernommen — B1 = Schema-Floor
  statt In-Daemon-Migration (gelockte Preflight-Entscheidung `wiring.py:1070` + Lock-Risiko),
  D1.2 = Bar-Stream-Token-Wrapper (latenter Bug seit Phase 13 B3), E2 = append-only Messquellen;
  C3b Caching gestrichen (Meter zählt Cache-Reads voll + Präfix < 1024); Ledger-Restore nach B2;
  P17 erlaubte Operator-Ereignisse vorregistriert. Ein Dissens (Compiler) dokumentiert.
- **Sonnet-Cold-Read** (Anker-Verifikation): 8 Anker-Korrekturen + `InstinctValidation.decision` verifiziert + D2.6-Einfügepunkt (`wiring.py:832`) festgelegt — Plan §13.
- **Nikinger Runde 2** (Plan P18): Push ✅ · P3 für C5 freigegeben · Allein-Entscheidungen bestätigt · **Exec-Modell = OpenCode / MiniMax M3** für alle Blöcke.
- `docs/concepts/phase16_activation_plan.md` (📕, NEU) · dieser Phasenkopf (NEU) · `docs/INDEX.md`
  2 Zeilen · `ROADMAP.md` Phase-16-Abschnitt · root `CLAUDE.md` Status-Absatz + Tabellenzeile.
- **0 Code-Edits, 0 Bot-Touch** (Bot lief die ganze Session, PID 124569 seit 09-03).

### Findings
- 🔴 **L3 ist die eine Doku-Lüge, die Code-Wahrheit widerlegt:** „`db.py:run_migrations()` wendet
  beim nächsten Service-Restart automatisch an" steht in root-CLAUDE.md:108, ROADMAP.md:441 und
  im P15-Handover (§7 E1, §9.13, §10 #4) — kein Produktions-Caller existiert. Korrektur = Plan A-3.
- 🟡 **Zwei Stellen, an denen die Plan-Session allein entschieden hat** (**in Runde 2 bestätigt**): (a) `InstinctConfig.enable_instinct_promotion` → Default True (P5, supersedet
  P15-P10, Begründung: VETO 5 kann nur vetoen); (b) Caching **nicht** bauen trotz „können wir
  testen" (P3, zwei verifizierte Fakten machen den Test ergebnislos).
- 🟢 C5 (L9): P3-Freigabe in Runde 2 erteilt — Step ist regulär.
- 🟢 `LiveQuoteCache` existiert nicht (0 Treffer) — ROADMAP 9b + phase9-Head führen eine Leiche (A-3).

### Next
- **Exec-Session (OpenCode / MiniMax M3, Einstieg über `AGENTS.md`):** Plan §6 **Block A, Step A-0** — diesen Block per
  Rotationsregel nach `SESSIONS_ARCHIVE.md` (neu anlegen) rotieren, `check_doc_rotation.py:66` um
  `phase16_activation` ergänzen, dann A-1 (Ritual), A-2 (Σ = 1843 erwartet), A-3 (Sweep).
- ~~Push~~ erledigt in der Plan-Session (Runde 2).
- **Operator im B2-Fenster** (alle vier Dienste gestoppt): Backup → `init_db.py --db-path
  data/trading_bot.sqlite` → Verify v9 → Ledger-Restore SQL (Plan §6 B2).

### Open questions / blockers
- Keine. Runde 2 hat alle drei Punkte geklärt (Plan P18).