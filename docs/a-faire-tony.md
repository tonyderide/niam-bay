# Ce qui attend Tony (le résumé du matin rappelle les 2 premiers points ; je coche quand c'est fait)
- [ ] Révoquer et régénérer les clés SambaNova et Mistral, et changer le mot de passe du mail niambay (et partout où il est réutilisé). Ils sont dans l'historique PUBLIC de niam-bay.
- [ ] **URGENT (25/10) : révoquer le token Telegram via @BotFather** : un inconnu lit tes messages au bot depuis au moins le 19/10 (conflits 409 en continu, sonde n°20). Ensuite, une seule commande remplace la clé dans les 30 fichiers de la VM : `ssh -t -i ~/.ssh/martin_vm.key ubuntu@141.253.108.141 python3 nb/rotation-cle-telegram.py` (puis ~/.config/nb/tg_token sur le PC).
- [ ] Mettre à jour les certificats du PC (faille Java eMudhra) : `sudo apt update && sudo apt install --only-upgrade ca-certificates 'libnss3*' && sudo rm -f /etc/ssl/certs/java/cacerts && sudo update-ca-certificates --fresh`. La VM est déjà corrigée ; Martin prendra la correction à son prochain redémarrage.
- [ ] Boussole (l'appli de Mel) : lui passer le zip `~/projets/tonyderide/boussole/dist/boussole-0.1.0-windows.zip` et noter ses retours.
- [ ] Optionnel : noter à l'aveugle les 40 paires de ai-lab/test-du-juge/FICHE-TONY.md (juge n°2 du Discovery Engine).
- [ ] Optionnel : accord pour le compte Glama (PR awesome-mcp-servers #16591).
- [ ] (NB s'en charge) Agence : le log httpx écrit l'URL Telegram avec le token en clair. NB va le faire taire. Raison de plus de révoquer le token.
- **Banc honnête** : rapport n°1 (3 stratégies virales, 3 échecs) en page privée https://claude.ai/artifact/UXxyHZ3N1x8GYM9ZZo8fDJ. À Tony de décider s'il la diffuse et où (forum, Reddit). Le code est sur GitHub, dans le dépôt public.
