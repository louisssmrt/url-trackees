# Créateur d'URL trackées - Groupe Tisserin

Outil web interne pour générer des liens UTM propres, un lien court Bitly et un QR code, en 30 secondes. Chaque lien créé est enregistré automatiquement dans une base (Supabase) et consultable dans l'historique de la page.

Remplace le fichier Excel `Créateur URL Trackées.xlsm`.

## Pour l'équipe : comment on s'en sert

1. Ouvrir la page (lien partagé par Louis).
2. Mettre son **prénom** en haut à droite (retenu automatiquement).
3. Choisir la **marque** → l'URL de destination se pré-remplit.
4. Vérifier / coller l'**URL de destination** (la page où on envoie les gens).
5. Choisir **Source** (d'où vient le clic) puis **Support** (le format, la liste s'adapte à la source).
6. Taper la **Campagne / Programme** (ex. `osmose`). Des suggestions apparaissent.
7. (Optionnel) **Détail** (ex. `prospecting`, `retargeting`, `2m2`) et **Mot-clé**.
8. Cliquer **Générer & enregistrer** → on obtient :
   - le lien complet (bouton copier),
   - le lien court Bitly (si la case est cochée),
   - le QR code (téléchargeable en PNG haute résolution pour le print).

Tout est enregistré dans l'historique en bas, cherchable par programme / source / prénom.

## Ce qui a changé vs l'Excel

- **Bug corrigé** : l'onglet Tisserin Promotion mettait des `?` au lieu de `&` entre les paramètres → les liens trackés étaient cassés (Google Analytics ne lisait qu'`utm_source`). Ici les liens sont toujours corrects.
- **Valeurs normalisées** en minuscules propres (`qr_code`, `bdd_tp`, `panneau_site`...) pour un reporting GA cohérent.
- **Toutes les marques** (Nacarat, Tisserin Promotion, MDFL, MDFN, ECC, TMI), plus seulement 3.
- **QR code gratuit** généré dans le navigateur (aucun coût, contrairement aux QR Bitly payants).
- **Historique partagé** : tout le monde voit les liens déjà créés.

## Technique

- Page statique (HTML/JS) hébergée sur GitHub Pages. Aucun secret dans le code.
- QR : librairie `qrcode.js` (Kazuhiko Arase, MIT) servie en local (marche même si les CDN sont bloqués).
- Backend : 2 Edge Functions Supabase (projet `hpowqowzrxqokikadwni`) :
  - `create-link` : shorten Bitly + insert en base.
  - `list-links` : lecture de l'historique.
- La clé Bitly n'est **jamais** dans le code : stockée dans la table Supabase `app_config` (lisible seulement par la service_role, côté serveur).
- Table `tracked_links` : un enregistrement par lien créé.

Voir `MEMORY.md` pour les détails de maintenance.
