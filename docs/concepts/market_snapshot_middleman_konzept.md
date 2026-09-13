---
status: proposal
purpose: Middleman-Theorie festhalten — ein deterministischer Assembler, der mehrere Datenquellen zu EINEM kanonischen, LLM-blinden Datenblatt (MarketSnapshot) verdichtet. Bedingtes V2.5/V3-Thema, NICHT gebaut, NICHT gelockt.
read-when: wenn nach V2b-Live-Betrieb gemessene Divergenz/Degrade-Events die Frage aufwerfen, ob die Prioritätskette reicht; sonst nicht lesen
detail: L2
up: ../../ROADMAP.md
down:
  - ./phase9_v2_foundation_plan(1).md          # V2b-Kette + Divergenz-Check (der Ist-Zustand)
updated: 2026-07-07
---
# Middleman / MarketSnapshot — kanonisches Datenblatt (Konzeptnotiz)

> **Status: Vorschlag, gegatet, nicht gebaut.** Diese Notiz hält eine Idee fest, damit sie nicht
> verloren geht — sie ist **keine** Freigabe und **kein** Plan. Quelle der Wahrheit bleibt der Code.
> **Bewusst außerhalb des Scopes dieser Notiz:** Krypto / alternative Asset-Klassen. Hier geht es
> ausschließlich um die Verdichtung der bestehenden EU-Index-CFD-Datenquellen.

---

## 1. Kernthese

Statt dass die LLM-Schicht (P4-Research) sich ihre Felder aus verstreuten Quellen (IG-Bars,
LiveQuoteCache, yFinance-Kontext) selbst zusammenklaubt, verdichtet ein **deterministischer
Middleman** alle Quellen vorab zu **einem kanonischen Datenblatt** pro Epic pro Zyklus. Die
LLM-Schicht sieht nur dieses fertige Blatt und **weiß nichts von Quellen, Latenzen oder Konflikten**.
Das ist keine neue Idee, sondern die konsequente Zuspitzung des bestehenden Bauprinzips
(„Code bereitet auf, AI entscheidet") auf den Datenpfad.

## 2. Die entscheidende Unterscheidung (hier stirbt oder lebt die Idee)

**Auswählen + Annotieren = richtig. Verschmelzen = gefährlich.**

Die Quellen sind **keine gleichwertigen Redundanzen**: IG ist real-time, yFinance ist ~15 min
delayed. Jede Form von Blending (Mittelwert, gewichtete Fusion, „optimierter" Preis) erzeugt eine
Zahl, **die auf keinem Markt je existiert hat** — schlechter als jede Einzelquelle, weil der Fehler
unsichtbar wird statt sichtbar. Belegt durch die dokumentierte Quellen-Divergenz (Volumen bis
~30 %, 1-min-Bar-Preise messbar auseinander — siehe `INDEPENDENT_MARKETDATA_EVALUATION.md`).
Divergenz ist ein **Alarm-Signal**, kein Misch-Input.

## 3. Was der Middleman tut — und was nicht

**Tut (drei Operationen, alle deterministisch):**
1. **Wählen** — pro Feld eine feste Quellen-Priorität (z. B. `live_price`: LiveQuoteCache → IG-Bar-Close → yF-Last).
2. **Stempeln** — pro Feld `source` + `age_s` (Staleness) mitführen.
3. **Flaggen** — Divergenz/Qualität als Metadatum (`quality_flag`), nie in den Wert eingerechnet.

**Tut NICHT:** rechnen im Sinne von verschmelzen. Kein Feld ist je ein Mittel zweier Quellen.

## 4. Vorgeschlagenes Artefakt: `MarketSnapshot`

Ein `@dataclass(frozen=True)` pro Epic pro Zyklus. Jedes Feld trägt sein Tupel
`(value, source, age_s, quality_flag)`. Gebaut von reinem Code aus den bereits vorhandenen
Quellen; konsumiert vom `context_builder` (P4) **anstelle** der heutigen verstreuten Feldbeschaffung.
LLM-blind. Ehrlicher Nutzen: ein **Datenvertrag** statt verstreuter Felder, und Datenqualität wird
**pro Feld sichtbar** statt implizit.

## 5. Verhältnis zum Ist-Zustand (der ehrliche Teil)

**~70 % davon existieren bereits in V2b.** Die `ChainedBarProvider`-Kette + der `quote_divergence`-
Check + der deterministische `context_builder` **sind** schon ein Middleman: mehrere Quellen rein,
Code wählt, LLM sieht nur das Ergebnis. Der einzige echte Delta dieser Notiz ist das **kanonische,
annotierte Datenblatt** (ein typisierter Snapshot mit Per-Feld-Provenance) statt einer Prioritätskette
ohne explizites Qualitäts-Tagging.

## 6. Gating (Advisor-Flag: NICHT jetzt bauen)

Diese Idee hat dieselbe Signatur wie klassisches Tool-Hunting — eine zusätzliche Abstraktionsschicht,
die sich sauber anfühlt, bevor Evidenz zeigt, dass sie ein reales Problem löst. **Baubedingung:**
messbare Divergenz-/Degrade-Events aus dem V2b-Live-Betrieb (`quote_divergence`, `bar_fetch`,
`data_degraded`), die zeigen, dass die reine Prioritätskette Entscheidungen nachweislich
verschlechtert. Ohne diese Messung ist der Snapshot Architektur-Ästhetik.

**Akzeptanzkriterium für „lohnt sich"** (vorregistriert, bevor gebaut wird): der Snapshot muss einen
*quantifizierten* Vorteil gegenüber der bestehenden Kette zeigen (z. B. X vermiedene Fehlentscheidungen
oder messbar bessere Kontext-Health), nicht bloß „ist sauberer".

## 7. Einordnung

Bedingtes **V2.5**- (kleiner Snapshot-Layer) oder **V3**-Thema (gekoppelt an die Persistenz-Reform,
falls Snapshots ohnehin persistiert werden). **Kein V2-Item.** Reihenfolge unverändert: erst V2b
fertig betreiben und *messen*, dann entscheiden.

---

> **TODO bei Aufnahme ins Repo:** One-Liner in `docs/INDEX.md` ergänzen (Doc-Layers-Regel:
> neue .md → INDEX-Eintrag im selben Commit).
