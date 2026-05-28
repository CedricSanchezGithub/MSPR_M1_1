# Metabase — Blocs & Requêtes SQL

---

## Dashboard 1 — Prédictions 2026

**En-tête (bloc texte) :**
```
## 🗳 Prédictions municipales 2026 — Hérault (34)
Random Forest · 89,6 % de précision (test 2020) · 58 communes
```

**Carte :**
```
![Carte 2026](http://localhost:8080/phase4/04_carte_predictions_2026.png)
```

**Évolution temporelle :**
```
![Tendance 2008–2026](http://localhost:8080/phase4/03_predictions_temporelles.png)
```

**Distribution :**
```
![Distribution % Gauche](http://localhost:8080/phase4/05_distribution_probabilites.png)
```

**Tableau prédictions :**
```sql
SELECT nom_commune AS "Commune", camp_predit AS "Camp",
       ROUND(pred_pct_gauche, 1) AS "% Gauche",
       ROUND(ABS(pred_pct_gauche - 50), 1) AS "Écart à 50 %"
FROM predictions_2026
ORDER BY pred_pct_gauche DESC;
```

**Synthèse département :**
```sql
SELECT
    COUNT(*) AS "Total",
    SUM(CASE WHEN camp_predit = 'Gauche' THEN 1 ELSE 0 END) AS "Gauche",
    SUM(CASE WHEN camp_predit = 'Droite' THEN 1 ELSE 0 END) AS "Droite",
    ROUND(AVG(pred_pct_gauche), 1) AS "% Gauche moyen"
FROM predictions_2026;
```

**Bascules 2020 → 2026 :**
```sql
SELECT nom_commune AS "Commune", camp_2020 AS "2020", camp_predit AS "2026",
       ROUND(pct_gauche_2020, 1) AS "% Gauche 2020",
       ROUND(pred_pct_gauche, 1) AS "% Gauche 2026",
       ROUND(pred_pct_gauche - pct_gauche_2020, 1) AS "Évolution (pts)"
FROM comparaison_2020_2026
WHERE bascule = 1
ORDER BY ABS(pred_pct_gauche - pct_gauche_2020) DESC;
```

---

## Dashboard 2 — Validation du modèle

**En-tête :**
```
## 🔬 Validation — Train 2008+2014 / Test 2020
```

**Matrice de confusion :**
```
![Matrice de confusion](http://localhost:8080/phase4/02_matrice_confusion.png)
```

**Réel vs prédit :**
```
![Réel vs prédit](http://localhost:8080/phase4/06_reel_vs_predit_2020.png)
```

**Importance des features :**
```
![Importance features](http://localhost:8080/phase4/01_importance_features.png)
```

**Métriques :**
```sql
SELECT metrique AS "Métrique", valeur AS "Valeur", description AS "Description"
FROM metriques_modele ORDER BY id;
```

**Matrice de confusion (tableau) :**
```sql
SELECT camp_reel AS "Réel", camp_predit AS "Prédit", COUNT(*) AS "Nb communes"
FROM predictions_test_2020
GROUP BY camp_reel, camp_predit
ORDER BY camp_reel, camp_predit;
```

**Précision par camp :**
```sql
SELECT camp_reel AS "Camp", COUNT(*) AS "Total",
       SUM(correct) AS "Corrects",
       ROUND(100.0 * SUM(correct) / COUNT(*), 1) AS "Précision (%)"
FROM predictions_test_2020
GROUP BY camp_reel;
```

**Distribution des erreurs :**
```sql
SELECT
    CASE WHEN ecart_abs < 5  THEN '< 5 pts'
         WHEN ecart_abs < 10 THEN '5–10 pts'
         WHEN ecart_abs < 15 THEN '10–15 pts'
         WHEN ecart_abs < 20 THEN '15–20 pts'
         ELSE '≥ 20 pts' END AS "Tranche",
    COUNT(*) AS "Communes",
    ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM predictions_test_2020), 1) AS "%"
FROM predictions_test_2020
GROUP BY 1 ORDER BY MIN(ecart_abs);
```

**Top erreurs :**
```sql
SELECT nom_commune AS "Commune", camp_reel AS "Réel", camp_predit AS "Prédit",
       ROUND(pct_gauche_reel, 1) AS "% Réel", ROUND(pct_gauche_predit, 1) AS "% Prédit",
       ROUND(ecart_abs, 1) AS "Écart (pts)",
       CASE WHEN correct = 1 THEN '✓' ELSE '✗' END AS "OK"
FROM predictions_test_2020
ORDER BY ecart_abs DESC LIMIT 15;
```

**Faux positifs / négatifs :**
```sql
SELECT
    CASE WHEN camp_reel = 'Gauche' AND camp_predit = 'Droite' THEN 'Faux Droite'
         WHEN camp_reel = 'Droite' AND camp_predit = 'Gauche' THEN 'Faux Gauche'
         ELSE 'Correct' END AS "Type",
    COUNT(*) AS "Communes",
    ROUND(AVG(ecart_abs), 1) AS "Écart moyen (pts)"
FROM predictions_test_2020
GROUP BY 1 ORDER BY 2 DESC;
```

---

## Dashboard 3 — Profil socio-démographique

**En-tête :**
```
## 📊 Profil socio-démographique — Hérault (34)
INSEE · DGFiP · data.gouv.fr — 2008–2023
```

**Communes remarquables :**
```
![Communes remarquables](http://localhost:8080/phase4/07_evolution_communes_remarquables.png)
```

**Population — communes remarquables :**
```sql
SELECT c.nom AS "Commune", p.annee AS "Année", p.population AS "Population"
FROM population p JOIN communes c ON p.codgeo = c.codgeo
WHERE p.codgeo IN ('34172','34032','34301','34003','34129')
  AND p.annee IN (2008, 2014, 2020, 2023)
ORDER BY c.nom, p.annee;
```

**Top 20 communes par population (2020) :**
```sql
SELECT c.nom AS "Commune", p.population AS "Population"
FROM population p JOIN communes c ON p.codgeo = c.codgeo
WHERE p.annee = 2020
ORDER BY p.population DESC LIMIT 20;
```

**Revenus médians :**
```sql
SELECT c.nom AS "Commune",
       ROUND(r."[disp]_1ᵉʳ_decile_(€)", 0) AS "D1", ROUND(r."[disp]_1ᵉʳ_quartile_(€)", 0) AS "Q1",
       ROUND(r."[disp]_mediane_(€)", 0) AS "Médiane",
       ROUND(r."[disp]_3ᵉ_quartile_(€)", 0) AS "Q3", ROUND(r."[disp]_9ᵉ_decile_(€)", 0) AS "D9"
FROM revenus r JOIN communes c ON r.codgeo = c.codgeo
WHERE r."[disp]_mediane_(€)" IS NOT NULL
ORDER BY r."[disp]_mediane_(€)" DESC LIMIT 30;
```

**Communes les plus pauvres (pop > 200) :**
```sql
SELECT c.nom AS "Commune", ROUND(r."[disp]_mediane_(€)", 0) AS "Revenu médian (€)",
       p.population AS "Population"
FROM revenus r
JOIN communes c ON r.codgeo = c.codgeo
JOIN population p ON r.codgeo = p.codgeo AND p.annee = 2020
WHERE r."[disp]_mediane_(€)" IS NOT NULL AND p.population > 200
ORDER BY r."[disp]_mediane_(€)" ASC LIMIT 15;
```

**Résultats électoraux agrégés :**
```sql
SELECT annee AS "Année",
       SUM(CASE WHEN camp='Gauche' THEN voix ELSE 0 END) AS "Voix Gauche",
       SUM(CASE WHEN camp='Droite' THEN voix ELSE 0 END) AS "Voix Droite",
       ROUND(100.0 * SUM(CASE WHEN camp='Gauche' THEN voix ELSE 0 END)
             / NULLIF(SUM(voix),0), 1) AS "% Gauche"
FROM elections WHERE tour=1 AND annee IN (2008,2014,2020)
GROUP BY annee ORDER BY annee;
```

**Résultats 2020 par commune :**
```sql
SELECT c.nom AS "Commune",
       ROUND(100.0 * SUM(CASE WHEN e.camp='Gauche' THEN e.voix ELSE 0 END)
             / NULLIF(SUM(e.voix),0), 1) AS "% Gauche 2020"
FROM elections e JOIN communes c ON e.codgeo = c.codgeo
WHERE e.tour=1 AND e.annee=2020
GROUP BY c.nom ORDER BY 2 DESC;
```

**CatNat — communes les plus exposées :**
```sql
SELECT c.nom AS "Commune", COUNT(*) AS "Nb CatNat",
       MIN(cat.dat_deb) AS "Premier", MAX(cat.dat_deb) AS "Dernier"
FROM catnat cat JOIN communes c ON cat.codgeo = c.codgeo
GROUP BY c.nom ORDER BY 2 DESC LIMIT 20;
```

**Taux de natalité (2018–2020) :**
```sql
SELECT c.nom AS "Commune",
       ROUND(AVG(CAST(n.naissances AS REAL) * 1000.0 / NULLIF(p.population,0)), 1) AS "‰"
FROM naissances_deces n
JOIN communes c ON n.codgeo = c.codgeo
JOIN population p ON n.codgeo = p.codgeo AND p.annee = 2020
WHERE n.annee BETWEEN 2018 AND 2020
GROUP BY c.nom HAVING p.population > 500
ORDER BY 2 DESC LIMIT 20;
```

**Finances — dette par habitant :**
```sql
SELECT c.nom AS "Commune", p.population AS "Population",
       ROUND(cc.dette / NULLIF(p.population,0), 0) AS "Dette/hab (€)",
       ROUND(cc.depenses_investissement / NULLIF(p.population,0), 0) AS "Invest/hab (€)"
FROM comptes_communes cc
JOIN communes c ON cc.codgeo = c.codgeo
JOIN population p ON cc.codgeo = p.codgeo AND p.annee = 2020
WHERE cc.annee = (SELECT MAX(annee) FROM comptes_communes)
  AND p.population > 200 AND cc.dette > 0
ORDER BY cc.dette / NULLIF(p.population,0) DESC LIMIT 20;
```

**Vote Gauche × revenu médian :**
```sql
SELECT c.nom AS "Commune", ROUND(r."[disp]_mediane_(€)", 0) AS "Revenu médian (€)",
       ROUND(100.0 * SUM(CASE WHEN e.camp='Gauche' THEN e.voix ELSE 0 END)
             / NULLIF(SUM(e.voix),0), 1) AS "% Gauche 2020",
       p.population AS "Population"
FROM elections e
JOIN communes c ON e.codgeo = c.codgeo
JOIN revenus r ON e.codgeo = r.codgeo
JOIN population p ON e.codgeo = p.codgeo AND p.annee = 2020
WHERE e.tour=1 AND e.annee=2020 AND r."[disp]_mediane_(€)" IS NOT NULL
GROUP BY c.nom, r."[disp]_mediane_(€)", p.population
ORDER BY r."[disp]_mediane_(€)";
```
