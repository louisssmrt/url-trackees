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

## Maintenance courante
- Ajouter une marque / source / support / programme : éditer les tableaux `BRANDS`, `SOURCES`, `PROGRAMS`, `PROGRAM_URLS` dans `index.html`, commit + push (Pages se met à jour tout seul).
- Changer la clé Bitly : `update app_config set value='...' where key='bitly_token';` (via MCP Supabase, aucune redeploy nécessaire).
- Redéployer une fonction : via MCP Supabase `deploy_edge_function` (les copies de référence sont dans `supabase/`).

## Déploiement Pages
```
cd projets/OUTILS/CREATEUR-URL-TRACKEES
git add -A && git commit -m "..." && git push
```
