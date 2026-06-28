"""Phase 8 — Module 12: the read-mostly Web-UI (``webui`` package).

A localhost dashboard that **observes** the autonomous demo trader and **controls** it only
through the files the trader already trusts — the kill-switch (:mod:`scheduler.killswitch`) and
the start/stop command channel (:mod:`scheduler.command`). It never imports the executor / broker
/ runner and never opens the DB read-write: a UI crash can structurally not touch trading
(concept Decision 14 — the trader never hangs on the UI).

Built **last** in the phase and the first thing dropped under time pressure (never the safety).
``fastapi`` + ``uvicorn`` are the only new runtime deps, used here only.
"""
