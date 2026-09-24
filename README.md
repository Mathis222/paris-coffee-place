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

**Étape 1 (Ingestion) : terminée pour Sirene.**
- `src/ingestion/utils.py` : `explore_columns()` (liste les CSV d'un zip Sirene), `print_df()` (utilitaire d'affichage exploratoire).
- `src/ingestion/sirene.py` : `filtre_paris_cafe()` (filtre NAF `56.30Z` + Paris), `build_cafe_paris_dataset()` (lecture par chunks du fichier actuel, filtrage, accumulation) → sauvegarde `data/processed/siren-actual-processed.parquet`.

**Étape 2 (Construction du label) : label binaire terminé, flag chaîne/indépendant restant.**
- `src/ingestion/labels.py` :
  - `filtre_siret()` + `build_label()` : filtre le fichier historique par chunks sur la liste des `siret` cafés parisiens (résultat : ~17 300 lignes de transitions d'état pour ~5 700 cafés).
  - `main()` : ne garde que les transitions réellement marquées comme changement d'état (`changementEtatAdministratifEtablissement == 'true'`) et fermées (`'F'`), groupe par `siret` pour prendre la date de fermeture la plus ancienne (`groupby('siret')['dateDebut'].min()`), merge sur le dataset actuel.
  - **Label final `survecu_2ans`** (binaire) : seuil fixé à 2 ans. Calcul de `duree_annee_observee` = (date_fermeture − date_création) si fermé, sinon (date_référence fixe − date_création) si actif. Les cafés **encore actifs et observés depuis moins de 2 ans** sont **censurés** (label mis à `NaN` puis lignes supprimées) — on ne peut pas savoir s'ils passeront le seuil. Les cafés `'F'` sans transition trouvée dans l'historique (incohérence entre les deux fichiers Sirene, 71 cas rencontrés) sont traités pareil (exclus).
  - Résultat sur les données actuelles : **5 652 cafés labellisés**, répartition **88 % survécu (4 958) / 12 % non-survécu (694)** — déséquilibré, à gérer au moment de l'entraînement (AUC/precision-recall plutôt qu'accuracy, pondération des classes).
  - Sauvegarde : `data/processed/cafe-labeled.parquet`.
  - Vérification faite : `dateDebut` (fichier actuel) et `dateFermeture` (calculée depuis l'historique) coïncident pour la quasi-totalité des cafés fermés testés — confirme que `dateDebut` d'une ligne historique à l'état `'F'` correspond bien à la date de fermeture. Un écart d'1 jour observé sur un cas isolé, probablement un cycle fermeture/réouverture rapide — à noter comme limite connue si ça revient.
  - **Flag chaîne/indépendant** : `build_chaine_label()` — `df.groupby('siren')['siret'].transform('count')` (compte d'établissements café par siren, redistribué sur chaque ligne sans réduire le nombre de lignes, façon fenêtre SQL `COUNT(*) OVER (PARTITION BY siren)`), puis `est_chaine = nb_etablissement_siren > 1`. Résultat : 635 chaînes (~11%) / 5017 indépendants (~89%). Limite connue et non traitée : rate les franchises où chaque point de vente a un siren différent (signal par `enseigne1Etablissement` à ajouter plus tard si besoin).
  - Sauvegarde finale : `data/processed/cafe-labeled-chaine.parquet`.
- **Important — ce que le modèle prédit** : une ligne d'entraînement = un café passé/présent, `X` = caractéristiques de son **emplacement** au moment de l'ouverture (concurrence, transport, socio-démo...), `y` = a-t-il survécu ≥ 2 ans. Le modèle apprend un pattern "quel type d'emplacement favorise la survie", appliqué ensuite à une **nouvelle adresse** saisie par un utilisateur (sans historique). Piège de fuite de données identifié et évité : ne jamais utiliser la durée d'ouverture du café lui-même comme feature (elle n'existe pas pour une adresse qui n'a pas encore de café) — la durée sert uniquement à construire le label, pas à prédire dessus.

**Étape 2 : terminée.**

**Étape 3 (Feature engineering spatial) : en cours.**
- **RATP (métro)** : `src/ingestion/ratp.py`. Deux sources croisées : trafic annuel par station (data.ratp.fr) + coordonnées géographiques réelles des stations en Lambert93 (data.iledefrance-mobilites.fr — pas le dataset RATP "plan schématique", qui donne des pixels, pas de vraies coordonnées). Jointure sur nom de station harmonisé (`.str.upper()`, suffixe `-RER` retiré côté trafic pour recoller aux stations partagées métro/RER), doublons métro+RER fusionnés par `groupby('station_key').agg(...)` (trafic sommé). ~420 stations de banlieue hors périmètre RATP écartées (attendu, hors scope Paris). Résultat : `data/processed/ratp-processed.parquet`.
- **Distance au métro + concurrents** : `src/features/localisation.py`. Coordonnées cafés = `coordonneeLambertAbscisseEtablissement/Ordonnee` du fichier Sirene actuel (déjà en Lambert93, pas besoin de géocoder pour les données d'entraînement — le géocodage BAN est réservé à l'adresse saisie par l'utilisateur final). Piège rencontré : la colonne contient parfois la valeur littérale `"[ND]"` (non déterminé) en plus des vrais `NaN` — nécessite `pd.to_numeric(..., errors='coerce')` avant tout calcul, sinon `min()/max()` sur une colonne texte donne un résultat absurde. ~1116 cafés sans coordonnées exploitables, exclus des features spatiales.
  - `scipy.spatial.KDTree` utilisé pour toutes les requêtes de proximité (outil réutilisable, appris ici, à réutiliser pour tout calcul de distance/densité futur) : `.query()` pour le plus proche voisin (station de métro), `.query_ball_point()` pour compter les voisins dans un rayon (concurrents).
  - Features produites : `dist_station_proche`, `trafic_station_proche`, `nb_voisin_200` (concurrents à 200m), `nb_voisin_500` (concurrents à 500m).
  - Décision de conception : pas de somme pondérée par décroissance de distance façon Huff à ce stade (trafic multi-stations, "probabilité d'entrer au café") — trop de coefficients à inventer sans données pour les calibrer. Les features restent simples et brutes ; c'est à XGBoost d'apprendre les combinaisons non-linéaires utiles. La vraie pondération à la Huff est prévue à l'étape 4 dédiée.
  - **Reste à faire** : sauvegarder le résultat (`.to_parquet`, pas encore fait).
- **Pas commencé** : zones piétonnes (Paris Data), compteurs vélo/routiers (proxy rythme horaire), INSEE Filosofi (pop/revenu par carreau), POI OSM, échantillon de points négatifs/contrôle.

## Données locales (non versionnées, dans `data/raw/`, gitignored)

- `siren-actual.zip` = `StockEtablissement_utf8` (état courant, ~2,9 Go)
- `siren-historic.zip` = `StockEtablissementHistorique_utf8` (historique complet, ~1,2 Go)

Téléchargeables sur https://www.data.gouv.fr/datasets/base-sirene-des-entreprises-et-de-leurs-etablissements-siren-siret (les URLs directes changent régulièrement, passer par la page du dataset).

## Points en attente / connus

- ~~Push Git cassé~~ **Résolu** : bascule en SSH (le token `gh` fine-grained n'avait pas les droits d'écriture). Remote configuré en `git@github.com:Mathis222/paris-coffee-place.git`, clé dans `~/.ssh/id_ed25519` ajoutée au compte GitHub. Push fonctionnel.

## Reprendre une session de travail

1. `cd ~/paris-coffee-place && source .venv/bin/activate`
2. Vérifier que `data/raw/siren-actual.zip` et `data/raw/siren-historic.zip` sont bien présents en local (pas versionnés).
3. Lire ce README pour le contexte, puis `src/ingestion/sirene.py` pour l'état du code.
