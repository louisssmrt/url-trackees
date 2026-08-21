# MEMORY - Créateur d'URL trackées

Outil web interne (remplace `OneDrive/Créateur URL Trackées.xlsm`). Créé le 2026-07-12.

## Hébergement
- Repo GitHub : `louisssmrt/url-trackees` (public, GitHub Pages).
- URL publique : https://louisssmrt.github.io/url-trackees/
- Compte GitHub : `louisssmrt`. Identité git commits : Louis Moret / moret.louis123@gmail.com.

## Backend Supabase
- Projet : `hpowqowzrxqokikadwni` ("Garmin project", org louisssmrt, eu-north-1). Réutilisé (pas de projet dédié).
- Tables :
  - `tracked_links` : 1 ligne / lien créé (brand, base_url, utm_*, final_url, short_url, created_by, notes, created_at). RLS ON, aucune policy publique.
  - `app_config` : clé/valeur. Contient `bitly_token`. RLS ON, aucune policy → lisible seulement via service_role dans les Edge Functions.
- Edge Functions (verify_jwt = false, appelées sans clé depuis la page) :
  - `create-link` (POST) : valide, shorten Bitly (lit le token dans app_config), insert dans tracked_links, renvoie {ok,id,short_url}.
  - `list-links` (GET ?brand=&q=&limit=) : renvoie les liens récents (order created_at desc).
- URLs fonctions : `https://hpowqowzrxqokikadwni.supabase.co/functions/v1/{create-link|list-links}`.

## Bitly
- Compte "Tisserin Immobilier" (procivisnord@gmail.com). Token (v4) stocké dans `app_config.bitly_token`.
- Récupéré depuis la macro VBA de l'ancien Excel (Module3.BitlyShorten).
- Les QR codes NE passent PAS par Bitly (Bitly fait payer ses QR) : générés côté client, gratuit.

## Bug de l'ancien Excel (corrigé ici)
- Onglet Tisserin Promotion : formule avec `?` au lieu de `&` entre les params → liens trackés cassés (`...?utm_source=X?utm_medium=Y`). Nacarat/MDFL étaient corrects (`&`).

## Convention UTM (décidée avec Louis 2026-07-12)
- Valeurs normalisées en minuscules propres (slugify : accents retirés, espaces → `_`).
- utm_campaign = nom du programme (slug). utm_content = détail/variante (prospecting, retargeting, 2m2...). utm_term = mot-clé.

## Taxonomie source/support (choix Louis 2026-07-15) - NE PAS "re-corriger"
Louis a délibérément choisi : **utm_source = le canal**, **utm_medium = le véhicule précis**. C'est INVERSÉ par rapport à la convention GA "textbook" (où source=plateforme, medium=type), mais c'est son choix assumé, à respecter :
- Source `lignage` → support = le portail (leboncoin, seloger_neuf, bienici...).
- Source `email` / `sms` → support = la base (bdd_nacarat, bdd_tp).
- Exception assumée : les **régies (google/meta/tiktok/linkedin/youtube)** gardent source=plateforme, support=format (cpc, social_ads...) car le budget par plateforme se suit individuellement.
- `qr_code` : source=qr_code, support=type physique (panneau_site, affichage...). Suit déjà le même schéma.
Ne pas remettre les portails/bases en source sous prétexte de "conformité GA".

## QR arrondi (piège technique, corrigé 2026-07-15)
Dessiner chaque module en rounded-rect pleine cellule ne se voit PAS (les voisins masquent les coins). Il faut un arrondi **conscient des voisins** : n'arrondir un coin QUE s'il est exposé (les 2 côtés adjacents sans voisin sombre). Canvas = `roundRect(x,y,s,s,[tl,tr,br,bl])` ; SVG = `<path>` avec arcs par coin (fonction `modPath`). Rayon = 0.5*cellule.

## Personnalisation du QR (ajoutee le 2026-08-21, demande Marie-Laure / Maxime)

Le panneau sous le QR permet : couleur unie ou **degrade** (diagonal / radial, 2 couleurs),
forme des **modules** (carre / arrondi / points), forme et couleur des **coins** (carre / arrondi /
cercle), **fond** (blanc / transparent / couleur), **logo** au centre (import ou preset) avec taille
et pastille. Tout est memorise dans le localStorage du navigateur, donc chaque personne garde son
style d'un lien a l'autre.

**Presets reseaux sociaux** : 8 boutons (Instagram, Facebook, LinkedIn, TikTok, YouTube, Pinterest,
X, WhatsApp) qui posent en un clic couleur + degrade + coins ronds + logo officiel du reseau. Les
glyphes viennent de **simple-icons v13.15.0**, inlines en dur dans `SOCIAL_ICONS` (aucun appel
reseau a l'execution). Pour en ajouter un : recuperer le `d=` du path sur
`https://unpkg.com/simple-icons@13.15.0/icons/<nom>.svg`, l'ajouter a `SOCIAL_ICONS` puis une entree
dans `SOCIAL_PRESETS`.

Canvas et SVG partagent les memes generateurs de chemin (`modsPath`, `eyesPath`), donc le PNG a
l'ecran et le SVG d'impression sont identiques par construction. Ne pas re-diverger les deux rendus.

### Pieges de scannabilite (verifies au decodeur, ne pas "reoptimiser" a l'oeil)

- **Modules "points" : rayon exactement `cell*0.5`**, pas moins. A 0.45 les pastilles ne se touchent
  plus et jsQR echoue a 300 px comme a 600 px, alors que le QR reste beau a l'ecran. C'est le
  reglage le plus fragile du fichier.
- **Degrade Instagram** : la vraie palette Instagram finit sur de l'orange (`#F58529`), trop clair,
  le coin du QR devient illisible. Preset cale sur `#833AB4` -> `#E1306C`, les deux assez sombres.
  Regle generale : la luminance des DEUX couleurs du degrade doit rester sous ~0.58.
- **Logo plafonne a 24 %** de la largeur (slider). A 28 % plus rien ne se decode, meme en correction
  d'erreur H (le niveau H est deja force automatiquement des qu'un logo est present).
- L'avertissement sous le QR est calcule (contraste, luminance, taille du logo, fond transparent) :
  s'il s'affiche, le QR est vraiment a risque.

### Harnais de test : `tests/test_qr_scan.py`

Rejoue les 27 combinaisons formes x coins x degrade + 5 tailles de logo + les 16 presets x formes,
et **decode chaque rendu** avec jsQR en PNG et en SVG, a 300 et 600 px. A lancer apres toute
modification du rendu QR : `python tests/test_qr_scan.py` (jsQR se telecharge tout seul dans
`tests/.cache/`). `cv2.QRCodeDetector` a ete essaye d'abord et ne convient pas : il refuse les
modules arrondis et les points alors qu'un telephone les lit sans probleme, donc il produit des faux
echecs. jsQR est le bon juge.

## Maintenance courante
- Ajouter une marque / source / support / programme : éditer les tableaux `BRANDS`, `SOURCES`, `PROGRAMS`, `PROGRAM_URLS` dans `index.html`, commit + push (Pages se met à jour tout seul).
- Changer la clé Bitly : `update app_config set value='...' where key='bitly_token';` (via MCP Supabase, aucune redeploy nécessaire).
- Redéployer une fonction : via MCP Supabase `deploy_edge_function` (les copies de référence sont dans `supabase/`).

## Déploiement Pages
```
cd projets/OUTILS/CREATEUR-URL-TRACKEES
git add -A && git commit -m "..." && git push
```
