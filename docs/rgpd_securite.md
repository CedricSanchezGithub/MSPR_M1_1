# RGPD et sécurité des données

## Objectif

Documenter la conformité du POC Electio-Analytics au RGPD (Règlement UE 2016/679) et les mesures de sécurité applicables. Périmètre : **341 communes** de l'Hérault, **12 datasets publics** open data (INSEE, data.gouv.fr, DGFiP, GASPAR), **1 base SQLite locale**, **1 dashboard Streamlit** sans authentification externe.

---

## 1. Nature des données traitées

L'ensemble des données mobilisées sont des **données publiques** publiées sous licence ouverte (Licence Ouverte Etalab 2.0 ou équivalente). Cinq familles, qualifiées RGPD ci-dessous.

### 1.1 Données électorales (`elections`)

- **Source** : `candidats_results.txt` (data.gouv.fr, Ministère de l'Intérieur).
- **Granularité** : résultats agrégés par bureau de vote, puis par commune dans la base.
- **Données nominatives présentes** : la table `elections` conserve `nom_candidat` et `prenom_candidat` (colonnes du DDL strict, lignes 158–159 d'`etl_pipeline.py`).
- **Qualification RGPD** : les **noms des candidats** sont des **données à caractère personnel**, mais ils relèvent du régime particulier des **personnalités publiques dans l'exercice d'un mandat électif** :
  - publication légalement obligatoire dans les bulletins officiels et au Journal officiel,
  - mise à disposition réutilisable sur data.gouv.fr sous Licence Ouverte,
  - **base légale** : exécution d'une mission d'intérêt public au sens de l'article 6.1.e du RGPD.
- **Conséquence** : un traitement nominatif est techniquement possible mais doit rester proportionné à la finalité (analyse électorale agrégée). Aucun croisement avec des données privées des candidats n'est effectué dans le POC.

### 1.2 Données socio-économiques INSEE (`revenus`, `csp`, `secteurs_activite`, `diplomes`, `csp_diplome`)

- **Granularité** : agrégats communaux (minimum 341 communes du 34).
- **Secret statistique INSEE** : seuil de publication de 11 ménages ou plus pour la diffusion d'un agrégat, ce qui exclut toute ré-identification.
- **Qualification RGPD** : statistiques publiques, **hors champ** des données à caractère personnel.

### 1.3 Données démographiques INSEE (`population`, `naissances_deces`)

- **Granularité** : comptages annuels par commune.
- **Qualification RGPD** : hors champ.

### 1.4 Données financières DGFiP (`comptes_communes`)

- **Granularité** : comptes consolidés par commune (recettes, dépenses, dette, fiscalité).
- **Sujet** : les communes sont des **personnes morales publiques** ; les données ne sont pas des données personnelles.
- **Qualification RGPD** : hors champ.

### 1.5 Données environnementales GASPAR (`catnat`, `risques`)

- **Granularité** : arrêtés administratifs et inventaire de risques par commune.
- **Sujet** : événements et risques territoriaux.
- **Qualification RGPD** : hors champ.

---

## 2. Conclusion RGPD du POC

| Élément | Statut |
|---|---|
| Données socio-éco, démographiques, financières, environnementales | **Hors champ** RGPD (agrégats, secret statistique) |
| Noms et prénoms des candidats (table `elections`) | **Données personnelles publiques** dans le cadre d'un mandat électif — base légale : article 6.1.e (mission d'intérêt public) |
| AIPD (analyse d'impact) | **Non requise** dans le périmètre du POC : pas de croisement personnel, pas de scoring individuel, pas de prise de décision automatisée sur un individu |
| Registre des traitements (article 30) | **Non requis** pour un POC mono-poste sans transmission tierce ; à constituer en cas de mise en production |
| DPO | Pas nécessaire pour ce POC ; à nommer en cas d'industrialisation impliquant des données nouvelles |

Conclusion : le POC **ne traite pas de données personnelles sensibles** au sens de l'article 9, et l'unique catégorie de données personnelles présente (identité des candidats) bénéficie d'une base légale claire et explicite.

---

## 3. Privacy by design — principes appliqués

Bien que le RGPD ne s'applique pas en l'état, les principes de **privacy by design** sont appliqués dès la conception, pour anticiper une future itération qui pourrait intégrer des données plus sensibles (sondages, données de campagne).

| Principe RGPD | Application dans le POC |
|---|---|
| **Minimisation** | Seules les colonnes utiles sont conservées en sortie d'ETL ; les autres colonnes nominatives ou identifiantes sont écartées (`drop columns` dans plusieurs `etl_*`). |
| **Limitation de finalité** | Données utilisées exclusivement pour la prédiction électorale ; aucun croisement à finalité marketing ou de profilage individuel. |
| **Exactitude** | Pipeline ETL reproductible, source unique par dataset, validation `validate()` en fin de chaîne. Détail : [`docs/qualite_donnees.md`](qualite_donnees.md). |
| **Limitation de conservation** | La base SQLite est **régénérée à chaque exécution** (`os.remove(DB_PATH)`, ligne 883) ; pas de fichiers intermédiaires durables. |
| **Intégrité et confidentialité** | Base locale, pas d'exposition réseau, pas de transmission cloud (cf. §4). |
| **Transparence** | Sources et transformations documentées (`SOURCES_DONNEES.md`, `docs/PIPELINE_ETL.md`, ce document). |

---

## 4. Mesures de sécurité techniques

| Mesure | Mise en œuvre dans le POC |
|---|---|
| **Stockage local** | Base SQLite (`data/output/electio_herault.db`), dashboard Streamlit lancé en local — pas de serveur exposé |
| **Pas de cloud** | Aucune donnée n'est hébergée sur un service tiers (AWS, GCP, Azure, …) ; pas de transfert hors UE |
| **Pas d'authentification externe** | `app.py` est une application Streamlit locale, sans login externe ; ne pas l'exposer publiquement sans ajouter une couche d'authentification |
| **Pas de credentials en clair** | Aucun secret, jeton ou mot de passe dans le code ou le repository ; les sources sont en open data, pas de clé d'API requise |
| **Exclusion des données brutes du Git** | `.gitignore` exclut `data/input/` (~3,5 GB de fichiers bruts) et `data/output/` ; seuls le code et la documentation sont versionnés |
| **Pas de PII dérivée** | Pas de calcul de scoring individuel, pas de tag personnel sur un votant |
| **Traçabilité** | Code versionné (Git) ; pipeline reproductible bit-à-bit (`random_state=42`) |

---

## 5. Conformité licences

Toutes les sources sont sous **Licence Ouverte Etalab 2.0** ou équivalente, qui autorise la réutilisation **y compris commerciale** sous condition de **citer la source** et la date de mise à jour.

| Source | Licence | Conditions |
|---|---|---|
| data.gouv.fr (élections, revenus, comptes communes via DGFiP, GASPAR) | Licence Ouverte v2.0 (Etalab) | Mention de la source |
| INSEE (population, CSP, secteurs, diplômes, état civil) | Licence Ouverte v2.0 (Etalab) | Mention de la source |
| DGFiP (comptes individuels) | Licence Ouverte v2.0 (Etalab) | Mention de la source |
| GASPAR (CatNat, risques) | Licence Ouverte v2.0 (Etalab) | Mention de la source |

Les références sont consignées dans [`SOURCES_DONNEES.md`](../data/input/SOURCES_DONNEES.md).

---

## 6. Recommandations pour une mise en production

Si le POC est industrialisé et que le périmètre de données s'élargit (sondages, données client, signaux sociaux, etc.), il faudra renforcer la conformité :

1. **AIPD (Analyse d'Impact sur la Protection des Données)** dès qu'une donnée à caractère personnel sera traitée à grande échelle ou avec des effets sur les personnes.
2. **DPO** désigné, point de contact unique avec la CNIL.
3. **Registre des traitements** (article 30 du RGPD) tenu à jour.
4. **Chiffrement** : au repos via SQLCipher / postgres + TDE, en transit via TLS pour toute API ou export.
5. **Authentification forte** sur le dashboard (SSO, MFA) et **journalisation des consultations**.
6. **Politique de conservation et purge** pour les données nominatives temporaires (logs, données de campagne).
7. **Anonymisation / pseudonymisation** des colonnes `nom_candidat` / `prenom_candidat` si elles ne servent pas à un usage légitime (par exemple, dans les exports vers des tiers non habilités).
8. **Hébergement UE** : exiger un hébergement souverain ou certifié SecNumCloud si des données personnelles transitent.

---

## 7. Pointeurs

- [`SOURCES_DONNEES.md`](../data/input/SOURCES_DONNEES.md) — URL canonique et licences des 12 datasets.
- [`docs/qualite_donnees.md`](qualite_donnees.md) — contrôles qualité côté pipeline.
- [`docs/architecture_bi.md`](architecture_bi.md) — architecture technique et points d'exposition réseau (aucun pour le POC).
- `scripts/etl/etl_pipeline.py` — implémentation du pipeline.
