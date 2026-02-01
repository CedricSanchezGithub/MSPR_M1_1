"""
Analyse exploratoire du dataset électoral
Script réutilisable pour examiner la structure et la pertinence des données
"""

import pandas as pd
from pathlib import Path


def charger_donnees(fichier: str = "participation_electorale.parquet") -> pd.DataFrame:
    """Charge le fichier parquet et retourne un DataFrame."""
    chemin = Path(fichier)
    if not chemin.exists():
        raise FileNotFoundError(f"Fichier non trouvé: {fichier}")
    return pd.read_parquet(chemin)


def afficher_dimensions(df: pd.DataFrame) -> None:
    """Affiche les dimensions du dataset."""
    print("\n" + "=" * 70)
    print("1. DIMENSIONS DU DATASET")
    print("=" * 70)
    print(f"   Nombre de lignes:   {df.shape[0]:,}")
    print(f"   Nombre de colonnes: {df.shape[1]}")


def afficher_colonnes(df: pd.DataFrame) -> None:
    """Affiche la liste des colonnes avec leurs types."""
    print("\n" + "=" * 70)
    print("2. COLONNES DISPONIBLES")
    print("=" * 70)
    for i, col in enumerate(df.columns, 1):
        print(f"   {i:2}. {col} ({df[col].dtype})")


def afficher_apercu(df: pd.DataFrame, n: int = 5) -> None:
    """Affiche un aperçu des premières lignes."""
    print("\n" + "=" * 70)
    print(f"3. APERÇU DES {n} PREMIÈRES LIGNES")
    print("=" * 70)
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)
    print(df.head(n).to_string())


def afficher_elections(df: pd.DataFrame) -> None:
    """Affiche la répartition des élections dans le dataset."""
    print("\n" + "=" * 70)
    print("4. ÉLECTIONS PRÉSENTES")
    print("=" * 70)
    elections = df['id_election'].value_counts()
    print(elections.to_string())

    print("\n   Types d'élections:")
    types = df['id_election'].str.extract(r'\d{4}_(\w+)_')[0].value_counts()
    for type_elec, count in types.items():
        print(f"   - {type_elec}: {count:,} lignes")


def afficher_presidentielles(df: pd.DataFrame) -> None:
    """Analyse spécifique des élections présidentielles."""
    print("\n" + "=" * 70)
    print("5. FOCUS ÉLECTIONS PRÉSIDENTIELLES")
    print("=" * 70)
    pres = df[df['id_election'].str.contains('pres')]

    if pres.empty:
        print("   Aucune élection présidentielle trouvée")
        return

    print(pres['id_election'].value_counts().to_string())
    print(f"\n   Total lignes présidentielles: {len(pres):,}")

    annees = sorted(pres['id_election'].str[:4].unique())
    print(f"   Années couvertes: {annees}")


def afficher_couverture_geo(df: pd.DataFrame) -> None:
    """Affiche la couverture géographique."""
    print("\n" + "=" * 70)
    print("6. COUVERTURE GÉOGRAPHIQUE")
    print("=" * 70)
    print(f"   Départements:    {df['Code du département'].nunique()}")
    print(f"   Communes:        {df['Code de la commune'].nunique()}")
    print(f"   Bureaux de vote: {df['id_brut_miom'].nunique():,}")


def afficher_participation(df: pd.DataFrame) -> None:
    """Affiche les statistiques de participation."""
    print("\n" + "=" * 70)
    print("7. STATISTIQUES DE PARTICIPATION")
    print("=" * 70)

    stats = {
        'Abstention': '% Abs/Ins',
        'Votants': '% Vot/Ins',
        'Blancs': '% Blancs/Vot',
        'Nuls': '% Nuls/Vot',
        'Exprimés': '% Exp/Vot'
    }

    for nom, col in stats.items():
        if col in df.columns:
            moy = df[col].mean()
            mini = df[col].min()
            maxi = df[col].max()
            print(f"   {nom:12} - Moy: {moy:6.2f}% | Min: {mini:6.2f}% | Max: {maxi:6.2f}%")


def afficher_valeurs_manquantes(df: pd.DataFrame) -> None:
    """Affiche les colonnes avec des valeurs manquantes."""
    print("\n" + "=" * 70)
    print("8. VALEURS MANQUANTES")
    print("=" * 70)

    missing = df.isnull().sum()
    missing_pct = (missing / len(df) * 100).round(2)

    cols_manquantes = [(col, missing[col], missing_pct[col])
                       for col in df.columns if missing[col] > 0]

    if not cols_manquantes:
        print("   Aucune valeur manquante")
        return

    for col, nb, pct in sorted(cols_manquantes, key=lambda x: -x[1]):
        print(f"   {col:35} {nb:>10,} ({pct:5.2f}%)")


def afficher_couverture_temporelle(df: pd.DataFrame) -> None:
    """Affiche la couverture temporelle."""
    print("\n" + "=" * 70)
    print("9. COUVERTURE TEMPORELLE")
    print("=" * 70)
    annees = sorted(df['id_election'].str[:4].unique())
    print(f"   Période: {annees[0]} - {annees[-1]}")
    print(f"   Années:  {', '.join(annees)}")


def evaluer_pertinence(df: pd.DataFrame) -> None:
    """Évalue la pertinence du dataset pour la prédiction."""
    print("\n" + "=" * 70)
    print("10. ÉVALUATION DE PERTINENCE POUR LA PRÉDICTION")
    print("=" * 70)

    colonnes_presentes = set(df.columns)

    # Vérifier les données de participation
    cols_participation = {'Inscrits', 'Votants', 'Abstentions', 'Blancs', 'Nuls', 'Exprimés'}
    participation_ok = cols_participation.issubset(colonnes_presentes)

    # Vérifier les données de résultats (colonnes typiques)
    cols_resultats_possibles = {'Voix', 'voix', 'Candidat', 'candidat', 'Nom', 'Prénom'}
    resultats_ok = bool(cols_resultats_possibles.intersection(colonnes_presentes))

    print("\n   DONNÉES PRÉSENTES:")
    print(f"   ✅ Participation (inscrits, votants, abstentions)" if participation_ok else "   ❌ Participation")
    print(f"   ✅ Localisation (département, commune, bureau)" if 'Code du département' in colonnes_presentes else "   ❌ Localisation")
    print(f"   ✅ Temporalité (plusieurs élections)" if df['id_election'].nunique() > 1 else "   ❌ Temporalité")

    print("\n   DONNÉES MANQUANTES CRITIQUES:")
    if not resultats_ok:
        print("   ❌ Résultats par candidat (votes, pourcentages)")
        print("   ❌ Nom des candidats")
        print("   ❌ Partis politiques")

    print("\n   VERDICT:")
    if resultats_ok:
        print("   ✅ Dataset COMPLET pour la prédiction")
    else:
        print("   ⚠️  Dataset PARTIEL - Contient uniquement les données de participation")
        print("   → Nécessite les résultats par candidat pour prédire les élections")


def analyser(fichier: str = "participation_electorale.parquet") -> pd.DataFrame:
    """Exécute l'analyse exploratoire complète."""
    print("\n" + "=" * 70)
    print("   ANALYSE EXPLORATOIRE - DONNÉES ÉLECTORALES")
    print("=" * 70)

    df = charger_donnees(fichier)

    afficher_dimensions(df)
    afficher_colonnes(df)
    afficher_apercu(df)
    afficher_elections(df)
    afficher_presidentielles(df)
    afficher_couverture_geo(df)
    afficher_participation(df)
    afficher_valeurs_manquantes(df)
    afficher_couverture_temporelle(df)
    evaluer_pertinence(df)

    print("\n" + "=" * 70)
    print("   FIN DE L'ANALYSE")
    print("=" * 70 + "\n")

    return df


if __name__ == "__main__":
    df = analyser()
