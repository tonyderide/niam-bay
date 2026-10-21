# Vérification de la mémoire de NB (2026-10-22 00:23)

18/19 souvenirs confirmés par le monde, **1 contredits**.

- ✅ `project_martin_local_second_instance` : martin-local ne tourne plus (désactivé, aucun process java)
- ❌ `project_niambay_own_capital_20260826` : le capital NB (equity actuelle, pas l'equity aux stops) est de quelques dollars (2-5 $ depuis le 1015)
  - observé : `equity_now inconnue`
- ✅ `project_exchange_truth` : ~/et/run.sh tourne en cron chaque minute sur la VM
- ✅ `project_exchange_truth` : exchange-truth est public sur github
- ✅ `project_nb_wake_cron` : cron local 23 */6 lance niambay-vacation-wake.sh
- ✅ `reference_martin_repo` : la VM suit origin/master
- ✅ `reference_martin_repo` : le clone local Martin existe dans ~/projets/tonyderide/martin
- ✅ `pc-et-jarvis (docs)` : aucun secret en clair dans les fichiers suivis du repo public niam-bay
- ✅ `project_nb_vm_architecture` : le bot Telegram tourne sur la VM (24/7)
- ✅ `project_brave_fullscreen_workaround` : Brave est forcé en X11 par l'override desktop utilisateur
- ✅ `project_cockpit_redesign_b` : le chassis InstrumentPanel.tsx existe dans cockpit
- ✅ `reference_projets_dir` : les repos de Tony sont dans ~/projets/tonyderide
- ✅ `project_martin_bug_2026-04-22` : backup de config dans ~/martin/archive/strategy-config.json.orphan-20260509
- ✅ `project_memoire_falsifiable` : le cron quotidien verify.py est installé
- ✅ `project_calibration_nb` : le cron horaire resolve.py est installé
- ✅ `project_memoire_falsifiable` : le hook Stop contradicteur est déclaré dans niam-bay/.claude/settings.json
- ✅ `project_nb_vm_architecture` : le résumé du matin (sans LLM) est planifié sur la VM (05h et 06h UTC, envoi à 07h Paris)
- ✅ `project_memoire_falsifiable` : le juge horaire du jumeau (twin.py) est planifié sur la VM
- ✅ `project_capset_236` : cap7_236.txt est un cap valide de 236 points dans F_3^7
