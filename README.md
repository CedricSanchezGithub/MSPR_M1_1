## Points forts de l'approche

**Une masse de données suffisante malgré le faible nombre d'élections**

Le choix de travailler à l'échelle communale change complètement la donne. Au lieu de 5 observations (une par élection), on obtient environ 175 000 observations en croisant les 35 000 communes françaises avec les 5 scrutins de 2002 à 2022. C'est suffisant pour entraîner un modèle capable de détecter des relations significatives.

**Une diversité territoriale qui enrichit l'apprentissage**

Les communes françaises présentent des profils très variés : métropoles, zones périurbaines, territoires ruraux, bassins industriels en reconversion... Cette hétérogénéité offre au modèle un large éventail de situations contrastées pour apprendre les liens entre caractéristiques socio-économiques et comportement électoral.

**Des données open data bien documentées**

Sur la période 2002-2022, les sources comme l'INSEE, data.gouv.fr ou le Ministère de l'Intérieur proposent des jeux de données cohérents et faciles à croiser. Cela limite les problèmes de comparabilité et simplifie le travail de préparation.

**Une validation temporelle possible**

On peut entraîner le modèle sur quatre élections et le tester sur la cinquième. Ce protocole permet de vérifier concrètement si les relations identifiées tiennent dans le temps.

---

## Limites et précautions

**Une hypothèse de stabilité qui peut être mise en défaut**

Le modèle suppose que les mécanismes liant variables socio-économiques et vote restent globalement stables sur vingt ans. Or, des bouleversements comme l'émergence de La République En Marche en 2017 ont profondément recomposé le paysage politique. Le modèle pourrait peiner à capter ces ruptures.

**Des observations qui ne sont pas indépendantes**

Deux types de corrélation peuvent biaiser l'analyse :
- *Corrélation temporelle* : une commune qui vote à droite en 2002 tend à rester à droite en 2022
- *Corrélation spatiale* : les communes voisines ont souvent des comportements similaires

Ces dépendances risquent de faire surestimer la robustesse du modèle si on n'y prête pas attention.

**Des facteurs locaux impossibles à capter**

Un maire populaire, une fermeture d'usine juste avant le scrutin, un scandale local... Ces éléments peuvent faire basculer le vote d'une commune sans que les variables socio-économiques ne l'expliquent.

**Des complications liées aux fusions de communes**

Les codes INSEE évoluent, les périmètres changent. Il faut harmoniser soigneusement les données pour éviter les erreurs de jointure entre les différentes années.