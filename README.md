# paris-coffee-place

Projet portfolio (open-source, gratuit) : estimer le potentiel d'un emplacement à Paris pour ouvrir un café — score de "clientélisabilité", carte de concurrence, et courbe heuristique de fréquentation horaire pour aider au dimensionnement du staffing.

Contrairement aux solutions du marché (MyTraffic, Esri...), qui reposent sur des données mobiles propriétaires payantes, ce projet vise une alternative **100% open data, reproductible et transparente**.

## Mode de fonctionnement de ce repo

Projet d'apprentissage : Mathis écrit tout le code lui-même dans VSCode, pas à pas, avec Claude comme guide (explication des concepts, revue de code, pas d'implémentation à sa place). Claude maintient uniquement ce README. Plan technique complet : `/Users/mathis.gj/.claude/plans/tingly-giggling-eich.md`.

## Décisions méthodologiques

- **Cible (label) du modèle** : survie des cafés/restaurants existants, dérivée de la base **Sirene** (INSEE), plutôt qu'une prédiction directe de CA/fréquentation (aucun dataset public de ce type n'existe — c'est ce que vend MyTraffic).
- **Deux fichiers Sirene sont nécessaires, à croiser sur `siret`** :
  - `StockEtablissement_utf8` (état courant de chaque établissement — adresse, code commune, code postal, NAF, date de création, état administratif actuel A/F) → sert à filtrer Paris + secteur café, et donne une première approximation de la cible.
  - `StockEtablissementHistorique_utf8` (historique complet des changements d'état par établissement — une ligne par période de validité) → sert à fiabiliser la date de fermeture exacte, via la colonne `changementEtatAdministratifEtablissement` qui distingue un vrai changement d'état d'un simple changement d'attribut (enseigne, etc.).
  - Une observation encore active à la date d'extraction est **censurée** (vocabulaire d'analyse de survie) : on ne sait pas si/quand elle fermera dans le futur, ce n'est pas un "succès" garanti à vie.
- **Filtrage géographique Paris** : `codeCommuneEtablissement.str.startswith('75')`, plus robuste qu'un filtre sur `codePostalEtablissement` en range (`75001`-`75020`) — le département 75 est exclusivement Paris (Paris = à la fois commune et département), donc aucun faux positif possible.
- **Codes NAF retenus** pour le secteur café/restauration :
  - `56.30Z` — Débits de boissons (le plus proche de "café" au sens strict, priorité du projet)
  - `56.10A` — Restauration traditionnelle
  - `56.10B` — Cafétérias et libres-services
  - `56.10C` — Restauration de type rapide
- **Chaîne vs indépendant** : feature prévue via `enseigne1/2/3Etablissement` + `denominationUsuelleEtablissement` + comptage d'établissements par SIREN (pas encore implémenté).
- **Traitement mémoire** : les fichiers Sirene font plusieurs Go — lecture systématique par chunks (`pd.read_csv(..., chunksize=...)`) directement depuis le zip (`ZipFile.open(...)`, sans extraction sur disque), jamais chargement complet en mémoire.
- **Piège pandas rencontré et à retenir** : les colonnes de type "code" (`codeCommuneEtablissement`, `codePostalEtablissement`, `siren`, `siret`, `nic`...) doivent être forcées en `str` via le paramètre `dtype` de `pd.read_csv` — sinon pandas les infère en `float64` dès qu'il y a des valeurs manquantes dans la colonne, ce qui casse les méthodes `.str.*` et peut faire perdre des zéros de tête.
- Autres sources prévues (pas encore intégrées) : RATP (trafic stations), Paris Data (zones piétonnes, compteurs vélo/routiers), INSEE Filosofi (pop/revenu par carreau), OSM via osmnx (POIs), API BAN (géocodage).
- Limite assumée : la courbe horaire de staffing sera une heuristique (typologie de zone × profil horaire générique des compteurs), pas une prédiction calibrée sur de la fréquentation réelle par café.

## État d'avancement

**Étape 0 (Setup) : terminée.** `.venv`, `requirements.txt`, `.gitignore`, structure de dossiers (`data/raw`, `data/processed`, `src/ingestion`, `src/features`, `src/api`, `src/app`, `notebooks`, `tests`).

**Étape 1 (Ingestion) : en cours.** `src/ingestion/sirene.py` contient à ce stade :
- `explore_columns()` : liste les CSV présents dans un zip Sirene.
- `read_csv()` : lit un chunk depuis un CSV zippé (sans extraction), affiche colonnes/valeurs uniques d'état/date max.
- `filtre_paris_cafe()` : filtre un DataFrame sur NAF `56.30Z` + Paris.
- `print_df()` : utilitaire d'affichage pour l'exploration.

**Prochaine tâche** : croiser la liste des `siret` cafés parisiens (fichier actuel) avec le fichier historique, en filtrant ce dernier par chunks sur `siret.isin(...)`, puis calculer par SIRET la date de fermeture (si elle existe) pour construire la cible de survie définitive.

## Données locales (non versionnées, dans `data/raw/`, gitignored)

- `siren-actual.zip` = `StockEtablissement_utf8` (état courant, ~2,9 Go)
- `siren-historic.zip` = `StockEtablissementHistorique_utf8` (historique complet, ~1,2 Go)

Téléchargeables sur https://www.data.gouv.fr/datasets/base-sirene-des-entreprises-et-de-leurs-etablissements-siren-siret (les URLs directes changent régulièrement, passer par la page du dataset).

## Points en attente / connus

- **Push Git cassé** : le compte GitHub `Mathis222` est authentifié via `gh`, mais le token utilisé (fine-grained PAT) n'a pas les droits d'écriture sur le repo (403 en push, et même en listant les clés SSH). Tentative de bascule en SSH commencée (clé générée dans `~/.ssh/id_ed25519`) mais pas encore validée côté GitHub. À reprendre : soit corriger les permissions du token, soit finir la config SSH (ajouter la clé publique sur https://github.com/settings/ssh/new puis `git remote set-url origin git@github.com:Mathis222/paris-coffee-place.git`).

## Reprendre une session de travail

1. `cd ~/paris-coffee-place && source .venv/bin/activate`
2. Vérifier que `data/raw/siren-actual.zip` et `data/raw/siren-historic.zip` sont bien présents en local (pas versionnés).
3. Lire ce README pour le contexte, puis `src/ingestion/sirene.py` pour l'état du code.
