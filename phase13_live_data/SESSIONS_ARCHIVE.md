# SESSIONS_ARCHIVE.md — Phase 13 (Live-Datenfundament)

Newest-first. Rotation rule (`CLAUDE.md` root, mandatory since 2026-07-06): the phase head
carries exactly one `## Session stopped` block; the previously-newest block moves here
verbatim when a new one is appended.

---

## Session stopped — 2026-08-18 (Session 1: Planungssession — Phase 13 eröffnet, Plan committet, kein Code)

> **Auftrag:** den execution-ready Plan für Phase 13 schreiben, nachdem P12.5 formal gescheitert
> ist. **Volles Ergebnis:**
> [`../docs/concepts/phase13_live_data_plan.md`](../docs/concepts/phase13_live_data_plan.md) —
> dieser Block ist die Kurzfassung. **Keine Code-Änderung in dieser Session.**

### Completed

1. **Vier Entscheidungen beim Nikinger eingeholt** (Closeout §4/§5/§6 verlangte genau das):
   Label = **Phase 13 = Live-Datenfundament, V4 → Phase 14** · Umfang = **mehrstufig, mit einer
   zusätzlichen Beschaffungsstufe** · LS-Prozess = **im Scheduler-Prozess** · Messregel =
   **beides messen, Differenz ist eine eigene Messgröße**.
2. **Plan geschrieben** — L1–L16 gelockt, Blöcke A/B/C, Verbatim-Anker je Edit-Stelle,
   Testliste, PASS-Kriterien P1–P9, §8 „Fehlgriffe, die wie andere Fehler aussehen",
   §9 vollständige Drift-Liste.
3. **Drei neue Befunde selbst nachgemessen** (Plan §4) — keiner stand in einem Vordokument:
   - **F1:** `IX.D.IBEX.FWM2.IP` trägt 301 IG-Bars mit `ts_utc` 2026-07-17, aber `fetched_at`
     **2026-08-18T11:10:17.019Z**. IG liefert für diese Forward-Epic seit einem Monat tote
     Historie und meldet `ok=True`. Sie hatte am 18.08. mit **8** IG-Calls die meisten von
     allen — und null verwertbare Bars. **Korrigiert den Closeout §7:** FWM2 ist nicht der
     „Existenzbeweis für yF-only", sondern der teuerste Blindgänger des Tages.
   - **F2:** `DivergenceSampler.sample_epic` (`heartbeat.py:184-193`) ankert das
     Vergleichsfenster am IG-Bar-Zeitstempel; ist der einen Monat alt, findet es keine yF-Bar
     und kehrt **still** zurück. Der Alarm ist gegen genau F1 strukturell blind. Beleg: **0**
     `quote_divergence`-Events bei **12** bezahlten Samples.
   - **F3:** Eine Lücke *mitten* im Trade-Fenster erzeugt in `resolve_paper_trade`
     (`paper.py:234-278`) eine **erfundene** `TIME_STOP`-Zeile, die in DB und Heartbeat nicht
     von einem echten Time-Stop unterscheidbar ist. Das ist die Begründung dafür, dass die
     Abdeckungsprüfung dem **ganzen** Fenster gilt, nicht dem Schwanz.
4. **Extern bestätigt:** IGs Streaming-Kanal läuft gegen ein **anderes** Kontingent (~40
   gleichzeitige Subscriptions je Verbindung), nicht gegen die 10 000 Historienpunkte/Woche;
   `CHART:{epic}:{scale}` existiert mit fertigen Kerzenfeldern (`OFR_*`, `BID_*`, `CONS_END`,
   `CONS_TICK_COUNT`). **Aber:** die Feldliste stammt aus Drittbibliotheken, labs.ig.com gab
   HTTP 403 — deshalb ist der CHART-Live-Check **Block B0** und gatet Block B.
5. **Step-0-Ritual (Turbo-/Legacy-Grep) ausgeführt — dokumentierter No-Op:** 3 Treffer, alle
   `strike` im Sinne von *Fehlversuch* (`phase9_universe/universe/promotion.py:121`, `:277`,
   `tests/test_promotion.py:343`), kein Options-Vokabular. `turbo_candidates` = 19 Treffer,
   der eingefrorene P5-Gate-2-Contract-Name — nicht umbenennen. Identisch zu den Ritualen vom
   2026-06-27 und 2026-07-10.
6. **Nummerierungs-Kaskade ausgeführt** (L16, derselbe Commit): Root-`CLAUDE.md`, `ROADMAP.md`
   (neuer Phase-13-Abschnitt + V4 → Phase 14), `README.md`, `ARCHITECTURE.md`, `docs/INDEX.md`,
   `phase9_universe/CLAUDE.md`, `phase10_v3/CLAUDE.md`. Historische Aussagen wurden **nicht**
   umgeschrieben, sondern mit datierten `⟳ Korrektur`-Notizen superseded.

### Verified

- `pytest phase12_data_foundation/tests -q` → **123 passed** · `pytest phase10_v3/tests -q` →
  **160 passed** (beide heute, 2026-08-18, geteiltes Venv `phase1_broker_wrapper/.venv`).
  **Alle übrigen Phasen-Zählstände sind ungeprüft** — Plan §9.8, Block A0.2 misst sie neu.
- Alle Zahlen in §4 des Plans stammen aus eigenen `mode=ro`-Abfragen gegen `data/bars.sqlite`,
  `data/trading_bot.sqlite` und `data/state/research_health.jsonl`, nicht aus Vordokumenten.
- Jeder Datei:Zeile-Anker im Plan wurde per Grep auf seinen Verbatim-String geprüft.

### Next

- **Block A0** (Plan §6): Regression-Baseline **aller** Phasen, Phasen-Gerüst
  (`README.md`, `pyproject.toml`, `requirements.txt`, `live_data/`, `tests/`,
  `scripts/dev_install.sh`-Kette). Der Phasen-Kopf (dieses File) existiert bereits.
- Danach **A1 → A7 strikt der Reihe nach.** Block A ist eine Löschung und macht einen sicheren
  Neustart möglich, **bevor** Block B gebaut ist — deshalb ist die Reihenfolge gelockt (L4).

### Open questions / blockers

- **Kein technischer Blocker.** Bot steht, Recorder sammelt weiter kostenlos.
- **Offen bis Block B0:** ob `CHART:{epic}:1MINUTE` auf diesem Konto überhaupt liefert
  (Plan §9.2). Beide Zweige sind ausgeplant — die ausführende Session stallt daran nicht.
- **Offen bis Block C1:** welche Fremdquelle S3 wird. Auswahlkriterien stehen im Plan (§6 C1),
  die Recherche lief parallel zu dieser Session.
- **`main` liegt 4 Commits vor `origin/main`** (Stand vor diesem Commit) — Push bleibt eine
  bewusste Einzelfreigabe des Nikinger.
