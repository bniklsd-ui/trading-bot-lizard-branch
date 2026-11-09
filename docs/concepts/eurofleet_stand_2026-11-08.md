---
status: live
purpose: Note from other project (eurofyx-fleet, 2026-11-08) — Stand der Ausführer-Pläne (z.ai abgelaufen und entfernt, MiniMax als M Plan Go verlängert), Ergebnis der Ausführer-Bewertung, geplante Harness-Re-Evaluation, Sharefyx-MCP in opencode
read-when: vor der Wahl des Ausführers oder Harness; bevor ein MiniMax-Modell benutzt wird; bei Fragen zum MiniMax-Kontingent
detail: L2
up: ../INDEX.md
updated: 2026-11-08 (angelegt von eurofyx-fleet auf Wunsch des Nikingers; §1/§2/§4/§5 am selben Abend nachgezogen: z.ai entfernt, MiniMax verlängert; committet von eurofyx-fleet mit Freigabe des Nikingers, INDEX-Zeile im selben Commit; §6 und §7 am selben Abend angehängt, **nicht committet**, siehe §6)
---

# eurofleet → Trading-Bot: Stand Ausführer und Harness (2026-11-08)

> Fremder Text aus dem Infra-Projekt eurofyx-fleet, geschrieben auf Wunsch des Nikingers.
> Nichts davon ist eine Freigabe für Änderungen an Diensten oder an der opencode-Konfiguration.

## 1 Pläne (Nikinger, 2026-11-08)

- **z.ai Coding-Plan: gekündigt und abgelaufen, entfernt.** eurofleet hat am 2026-11-08 den Eintrag `zai-coding-plan` aus `~/.local/share/opencode/auth.json` gelöscht (diese VM und die Sharefyx-VM) und den Wrapper `claude-glm` auf der Sharefyx-VM entfernt. GLM steht nicht mehr zur Verfügung.
- **MiniMax: am 2026-11-08 verlängert als „M Plan Go“** (monatlich, nächste Verlängerung 2026-12-07, automatisch). Der frühere größere Plan war nicht mehr buchbar. Go hat das kleinste Kontingent der drei Stufen (Go/Explore/Build = 1×/3×/7,5×), gezählt im 5-Stunden- und im Wochenfenster. Die Herstellerdoku nennt als Textmodell nur `MiniMax-M3.1-Flash`; **gemessen** am 2026-11-08: `MiniMax-M3` und `MiniMax-M3.1-Flash` antworten beide mit dem bisherigen Key über `https://api.minimax.io/v1`. Der Key bleibt gleich, an der opencode-Konfiguration ändert sich nichts.

## 2 Ergebnis der Ausführer-Bewertung (eurofleet, aus den Rohdaten beider Repos)

Grundlage: Rohdaten aus Sharefyx (P10.5, Lock P10.5-B) und Trading-Bot (Phase 17, Plan §14.2). Eine vorab festgelegte Rubrik gab es nicht; das ist eine Bewertung aus Rohdaten, kein vorregistrierter Vergleich.

| Ausführer | Belege | Schwäche |
|---|---|---|
| **MiniMax M3** (opencode, Trading-Bot, Exec-Sessions #1–#18) | keine Rückfallregel ausgelöst, alle Suites grün, Plan-AKs je Block getroffen; das Opus-Review AK22 über 27 Code-Commits fand einen echten Code-Befund (R1), keinen in Order-Pfad, Breaker oder LLM-Verdrahtung | keine Modell-Trailer je Commit; Kontingent nicht erfasst |
| **MiniMax M3.1 Flash** (opencode, Sharefyx, Blöcke 0–12 und 14.0–14.6) | 61 Commits mit Trailer, fast überall 0 Eingriffe | Block 14.6: Bildurteil im Bericht falsch → Blöcke mit Sichtung danach bei Claude Code |
| **GLM 5.3 Flash / 5.3** (opencode, Sharefyx, 2026-10-18/19) | — | Kontingent leer, weil ohne Kontextgrenze nie kompaktiert wurde (Konfiguration, nicht Modell); mit 400-K-Grenze nie wiederholt, Plan inzwischen abgelaufen |

**Empfehlung eurofleet (Entscheidung beim Nikinger):** MiniMax-Plan verlängern (erledigt, §1); M3 für Code-Blöcke, M3.1 Flash für planbare Blöcke; Sichtungen und Reviews bleiben bei Claude Code. M3 gegen M3.1 Flash ist **kein** Gleichstandsvergleich (verschiedene Projekte und Aufgaben).

## 3 Bilder

Der opencode-Katalog führt `MiniMax-M3.1-Flash` und `MiniMax-M3` mit Bild- und Videoeingabe (`attachment: true`). opencode kann Bilder also nativ an das Modell geben. **Nicht gemessen:** ob der Ausführer in Sharefyx Block 14.6 die Bilder selbst angesehen hat oder das Urteil über den MCP `local_vision` (kleines lokales Vision-Modell) geholt hat.

## 4 Geplant: Harness-Re-Evaluation (Nikinger, 2026-11-08)

**MiniMax Code gegen opencode**, beide mit einem MiniMax-Modell als Ausführer, **Claude Code bleibt Planer**. Noch nicht entworfen und nicht gestartet; die Verlängerung des MiniMax-Plans ist erfolgt (§1). Die Anbindung (Installation, Auth, Konfiguration) macht eurofleet. Vorschlag für die Rubrik, **vor** dem ersten Lauf festzuschreiben: gleiche Aufgabe je Harness, Modell-Trailer je Commit, Wanduhr, Kontingent laut MiniMax-Konsole, Eingriffe, Befunde eines Opus-Reviews, eine Bildaufgabe mit **nativer** Bildeingabe (ohne `local_vision`). Wegen des Go-Kontingents gehört der Verbrauch je Lauf in die Rubrik.

**Bitte an diese Session:** bis dahin wie bisher arbeiten; Modell-Trailer in **jedem** Commit des Ausführers setzen; Kontingent je Block notieren, wenn sichtbar. Die opencode-Konfiguration (`~/.config/opencode/`, `auth.json`, `opencode.service`) ändert weiter nur eurofleet.

## 5 Trading-Bot-spezifisch

- **Frist 2026-11-15 entfällt:** der MiniMax-Plan ist verlängert (§1). Der Ausführer (opencode + MiniMax M3) und das Research-LLM des Bots (Profil `research_m3`, MiniMax-Abo-Key) laufen weiter; die eigene Regel „nach dem 15.11. zurückflippen“ wird damit nicht ausgelöst. **Kontingent:** wenn `research_m3` denselben Abo-Key nutzt, teilen sich Bot und Ausführer das Go-Kontingent (nicht gemessen); eine Exec-Session während des Shakedowns kann also das Research-LLM ausbremsen.
- **Sharefyx-MCP in opencode:** auf dieser VM seit 2026-11-08 (`opencode mcp list`: `sharefyx connected`, Login durch den Nikinger am Desktop, `opencode.service` danach neu gestartet). Agenten von `opencode serve` können damit im Sharefyx-Space des Nikingers lesen und schreiben. Die Datei `~/.config/opencode/opencode.json` ändert weiter nur eurofleet.
- **E-3-Timer (Mo 2026-11-09 07:30):** eurofleet weiß davon und fasst ihn nicht an. eurofleet startet oder stoppt auf dieser VM nichts außerhalb des Fensters Sa 00:00 – So 20:00. Der nächste Wochenlauf von eurofleet ist **Sa 2026-11-14 ab 00:00** (nach dem Shakedown-Fenster): bei einem Reboot wird der Scheduler zuerst sanft gestoppt (SIGTERM, bis 360 s). Falls das den Bot-Betrieb stört, bitte dem Nikinger sagen, bevor der Lauf kommt.
- **Trailer:** die Exec-Commits dieses Repos tragen bisher keinen Modell-Trailer (nur die Opus-Commits). Für die Harness-Re-Evaluation (§4) wird er gebraucht.

## 6 Nachtrag 2026-11-08 abends: HEAD beim E-3-Start

- Die E-3-Dateien aus Exec-Session #18 lagen bis 2026-11-08 unkommittet im Checkout. eurofleet hat sie auf Wunsch des Nikingers committet und gepusht: `0af06c3` (Deploy-Skript, Units, Tests), `3bc66a1` (Runbook, Plan §23, Session #18), `28ecf2b` (diese Notiz bis §5).
- **Runbook §4 erwartet beim Start HEAD `b372649`.** Tatsächlich ist HEAD `28ecf2b` (= `origin/main`), solange vor dem Start niemand committet. Der **Bot-Code ist seit `b372649` unverändert**: `git diff --name-only b372649..28ecf2b` zeigt nur `scripts/e3_deploy.sh`, die zwei Deploy-Units unter `phase17_testbed/systemd/`, `tests/test_e3_deploy.py` und Doku. Beim Eintragen des Aktiv-Blocks also `28ecf2b` eintragen und auf diesen Abschnitt verweisen. Das Runbook ist gesperrt, eurofleet hat es nicht geändert; ob es eine `PHASE17_E3_RUNBOOK_v2.md` braucht, entscheidet die Bot-Session.
- Der Wächter in `scripts/e3_deploy.sh` vergleicht nur `HEAD` mit `origin/main`; unkommittete Dateien wie dieser Abschnitt stören ihn nicht. **Dieser Abschnitt ist bewusst nicht committet** (ein Commit vor dem Start verschiebt HEAD erneut, im Shakedown-Fenster wäre jeder Commit ein Befund). Committen nach D2 oder verwerfen, Entscheidung der Bot-Session.
- Tests: root 141/141 grün am 2026-11-08, aber nur mit gesetztem `XDG_RUNTIME_DIR`. Über `sudo` oder einen Gast-Agenten fehlt er, dann scheitert `systemd-analyze --user verify` in `test_e3_deploy.py` und `test_scheduler_hold.py` (Umgebung, kein Code-Fehler).

## 7 Nachtrag 2026-11-08 abends: Scheduler-Hold und Capital.com

**Scheduler-Hold (Nikinger: der Bot bleibt länger in Entwicklung, eurofleets „Projektende 201“ ist verschoben).** Ab sofort entscheidet **diese Session** über die eigene Datei `data/state/SCHEDULER_HELD`, nicht mehr ein fester Schalter bei eurofleet. eurofleet **liest nur**, ob die Datei da ist, und schreibt sie nie.

- **Datei da** (`bash scripts/install_units.sh --hold`): ein gestoppter Scheduler gilt im Health-Check als erwartet; nach einem Reboot durch eurofleet startet eurofleet ihn **nicht** (recorder, discovery, webui schon). `failed` bleibt rot.
- **Datei weg** (`--release-hold`, macht auch der E-3-Deploy am 2026-11-09): der Scheduler **muss laufen**. Ein gestoppter Scheduler ist dann rot, und eurofleet startet ihn nach einem Reboot im Fenster wieder (nächster Wochenlauf **Sa 2026-11-14 ab 00:00**: sanfter Stopp bis 360 s, Reboot falls nötig, Entsperren, Neustart der vier Units).
- **Also:** wer den Scheduler bewusst stoppt, setzt vorher `--hold`; wer ihn wieder laufen lassen will, `--release-hold`. Das Testfenster Mo–Fr 18:00–07:00 für beobachtete eurofleet-Läufe bleibt.

**Capital.com:** Der Nikinger muss bis **2026-11-20** seine Steuer-Identifikationsnummer bei Capital.com angeben. eurofleet hat lesend geprüft: der Bot nutzt Capital.com **derzeit nicht aktiv** (Broker ist IG; `instrument_source_availability` führt nur `ig`, `ls`, `yf`; in den Logs der letzten 14 Tage kein Treffer; laut Plan §2 Capital-Bars nur vom 2026-08-21, Operator-Probe Phase 13). Auf Capital.com verweisen nur die Operator-Pfade aus Phase 13 (`phase13_live_data/scripts/capital_backfill.py`, `probe_capital.py`, `gap_rescue_operator.py`, `live_data/rescue.py`, `live_data/backfill.py`). Wird der Zugang ohne Nummer eingeschränkt, fallen nur diese aus. Plant diese Session, Capital.com wieder zu nutzen, bitte dem Nikinger vor dem 20.11. sagen. Die Nummer gibt der Nikinger selbst bei Capital.com ein; sie gehört nicht ins Repo, nicht in Notizen und nicht in den Keyring-Code.

## 8 Nachtrag 2026-11-09: E-3-Deploy, Schritt 7 brach ab (Skriptfehler, Bot läuft)

eurofleet hat am 2026-11-09 um 07:31 und 11:16 nur gelesen und nichts gestoppt, gestartet oder geändert.

- **Ergebnis:** `tradingbot-e3-deploy.service` steht auf `failed` (exit 1, 07:30:23). Schritte 1–6 liefen vollständig: Hold freigegeben, Stopp, Backups `*.bak-20261109-pre-p17-*`, 3770 ig-Bars gelöscht, 29 Instincts markiert, Units installiert, vier Units gestartet. Das Log endet nach `--- Schritt 7: Startzeile ---` ohne Fehlermeldung.
- **Wahrscheinliche Ursache:** `scripts/e3_deploy.sh` läuft mit `set -euo pipefail`. Zeile 183 (`new_line="$(tail … | grep "starting scheduler daemon" | tail -1)"`): findet `grep` die Zeile noch nicht, endet die Pipe mit 1, die Zuweisung scheitert, `set -e` beendet das Skript, bevor `sleep 2` und die nächste Runde kommen. Die Datei `run_scheduler.log` gab es schon, die Startzeile kam erst um 07:30:23,789, der Abbruch lag in derselben Sekunde. Nicht nachgestellt, Fehlerbild und Zeitstempel passen.
- **Gleiches Muster:** Zeile 205 (`grep -c … || echo 0`) gibt bei vorhandener Datei ohne Treffer `0` doppelt aus (`grep -c` schreibt selbst `0` und endet mit 1, dann folgt `echo 0`). Zeile 198 hat schon `|| true`.
- **Vorschlag:** in Zeile 183 `… | tail -1 || true`; in Zeile 205 `|| true` statt `|| echo 0`. Ein Test, der die Startzeile erst nach dem ersten Poll schreibt, fände den Fehler. Das Skript ist einmalig, das Muster kann aber woanders wiederkommen.
- **Übersprungene Checks, von eurofleet um 11:16 lesend nachgeholt:** #2 grün (Startzeile 07:30:23 mit `llm_profile=research_m3`), #1 grün (heute kein `preflight failed`), #5 grün (60 Zeilen `discovery cycle`), #8 grün (alle vier Units `active`, Scheduler `NRestarts=0`).
- **Nicht geprüft:** #3, #4, #6, #7 (laut Skript bis 09:00 nötig, Runbook §3) und der Aktiv-Block (Runbook §4, HEAD `28ecf2b`, siehe §6). Das macht diese Session.
