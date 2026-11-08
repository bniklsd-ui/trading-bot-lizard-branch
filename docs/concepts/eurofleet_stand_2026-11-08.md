---
status: live
purpose: Note from other project (eurofyx-fleet, 2026-11-08) — Stand der Ausführer-Pläne (z.ai abgelaufen und entfernt, MiniMax als M Plan Go verlängert), Ergebnis der Ausführer-Bewertung, geplante Harness-Re-Evaluation, Sharefyx-MCP in opencode
read-when: vor der Wahl des Ausführers oder Harness; bevor ein MiniMax-Modell benutzt wird; bei Fragen zum MiniMax-Kontingent
detail: L2
up: ../INDEX.md
updated: 2026-11-08 (angelegt von eurofyx-fleet auf Wunsch des Nikingers; §1/§2/§4/§5 am selben Abend nachgezogen: z.ai entfernt, MiniMax verlängert; committet von eurofyx-fleet mit Freigabe des Nikingers, INDEX-Zeile im selben Commit)
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
