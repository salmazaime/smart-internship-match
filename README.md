# Smart Internship Match par Salma Zaime

Système personnel d'aide à la décision pour ma recherche de **stage de fin d'études en sécurité cloud** (6 mois à partir de mars 2027) : collecter de vraies offres, les structurer, exclure celles qui sont impossibles pour moi, comparer les autres à mes compétences, m'aider à agir (lettres), puis suivre les résultats.

**Dashboard :** https://salmazaime.github.io/smart-internship-match/

## 1. Pipeline

| Étape | Fichier | Où | Rôle |
|---|---|---|---|
| Profil | `data/profile/my_skills.csv` | repo | 18 compétences (niveau 1-5) + une preuve concrète pour chacune (stages Atlas Cloud et ONDA, projets, certifications) |
| Acquisition officielle | `scripts/fetch_offers.py` + `fetch_offers.yml` | GitHub Actions, chaque lundi | API France Travail « Offres d'emploi v2 » (OAuth2) |
| Acquisition 2e source | Indeed (via Claude) | local | 11 offres réelles « sécurité cloud / DevSecOps / IAM » collectées le 14/11/2026 |
| Structuration (IA) | prompt de `scripts/extract_offers.py` | local | `required_skills`, `responsibilities`, `experience_required`, `compensation_mentioned` |
| KPI de matching | `scripts/match_offers.py` | local | filtre de faisabilité, puis score, couverture, compétences trouvées, lacunes |
| Action (IA) | `scripts/draft_cv.py` | local | paragraphe d'accroche pour les 3 meilleures offres, uniquement à partir de mes preuves |
| Suivi | `data/tracking/applications.csv` | repo | tableau tenu par moi, jamais par l'IA |
| Monitoring | `scripts/monitor_search.py` + `monitor.yml` | GitHub Actions, chaque jour | 3 règles d'alerte, historique dans `docs/data/monitoring.json` |
| Restitution | `docs/index.html` | GitHub Pages | dashboard Chart.js |

Restent **en local** (gitignorés) : `structured_offers.json`, `matches_all_local.json` et `output/cv_drafts/`.

## 2. Mon KPI de matching : exclure, puis comparer

**Étape 1 : filtre de faisabilité (CM1).** Une offre est **exclue** avant toute comparaison si elle ne peut pas être mon PFE :
- durée connue **inférieure à 6 mois** ;
- niveau d'études visé trop bas (BUT, Bac+2…).

Une information absente ne fait jamais exclure une offre.

**Étape 2 : score des offres faisables.**
- `coverage` = compétences demandées que j'ai / compétences demandées
- `score` = Σ (mon niveau / 5) pour les compétences trouvées / compétences demandées
- Les noms de compétences sont normalisés (casse, espaces et vrais synonymes, comme `Entra ID` = `Microsoft Entra ID` ou `OAuth2` = `OAuth 2.0 / OIDC / SAML`), parce que l'IA n'écrit pas toujours une compétence de la même façon.

**Pourquoi le filtre change tout.** Sans lui, l'offre classée 1ʳᵉ aurait été un stage DevOps de **3 mois** (couverture de 75 %), destiné à des étudiants en BUT : une offre à laquelle je ne peux pas postuler. Le filtre en exclut 2 sur 11 (3 mois et 2 mois).

**Limite.** Une compétence « obligatoire » et une compétence « appréciée » ont le même poids.

## 3. KPI (3 catégories)

| Catégorie | KPI | Valeur |
|---|---|---|
| Santé du pipeline | Offres collectées / par source | 11 (Indeed 11, France Travail 0) |
| Santé du pipeline | Offres avec compétences extraites | 100 % |
| Santé du pipeline | Erreurs d'extraction corrigées à la relecture | 3 (voir §5) |
| Santé du pipeline | Rémunération indiquée | 2 / 11 : trop peu pour un graphique |
| Efficacité de la recherche | Offres faisables | 9 / 11 |
| Efficacité de la recherche | Score moyen / couverture moyenne (offres faisables) | 0,35 / 47 % |
| Efficacité de la recherche | **Lacune n°1** | **Kubernetes** (4 offres faisables sur 9) |
| Résultat | Candidatures envoyées / taux de réponse | 0 / — |
| Résultat | Exécutions du monitoring | 2 manuelles, puis 1 par jour |

KPI qui ne cherche pas à faire « plus de candidatures, plus vite » : **la lacune n°1**. Elle me dit quoi apprendre avant mars 2027.

## 4. Choix des graphiques

| Visuel | Pour qui | Décision | Pourquoi ce type |
|---|---|---|---|
| Cartes KPI regroupées par catégorie | moi | « puis-je faire confiance aux chiffres ? ma recherche est-elle bien ciblée ? » | un chiffre et son contexte, dans l'ordre des 3 catégories |
| Barres des scores (faisables en bleu, exclues en gris) | moi | dans quel ordre postuler | barres triées ; les offres exclues restent visibles pour montrer ce que le filtre écarte |
| Barres empilées « je l'ai / me manque » par compétence | moi | quoi apprendre en premier | la longueur donne la demande, la couleur dit si j'ai la compétence : la plus longue barre rouge est la priorité |
| Tableau des offres anonymisées | moi | choisir une offre précise | il faut le détail exact des compétences, pas une tendance |
| Historique du monitoring | moi / l'enseignant | « dois-je agir ? » | un journal chronologique avec un statut OK/ALERT |

## 5. Erreurs d'IA repérées (relecture critique, CM5)

1. **Compétence inventée.** « FinOps » a été extrait d'une offre DevSecOps qui dit seulement « suivi et analyse des coûts Cloud ». Je l'ai retiré.
2. **Phrase générique prise pour une compétence.** « Cloud security », tiré de « sensibilité aux sujets de sécurité Cloud », a été compté comme une **lacune**. Résultat absurde : la sécurité cloud apparaissait comme une compétence qui me manque, alors que c'est ma spécialité. Je l'ai retiré : le score de l'offre passe de 0,28 à 0,37.
3. **Métadonnée contradictoire.** Indeed classe une offre en « contrat d'apprentissage », alors que son texte décrit un stage de fin d'études. J'ai gardé le texte.
4. **Brouillons de lettre.** J'ai vérifié qu'aucune compétence absente de mon profil (Kubernetes, Ansible, Keycloak, agents IA) n'est revendiquée, et que la SC-300 est bien présentée comme « en préparation », pas comme obtenue.

## 6. Monitoring

Ma définition de « ma recherche va mal » :
- **M1** : une offre de mon top 3 est encore `to_apply` plus de 5 jours après. Je n'agis pas.
- **M2** : une candidature est `sent` depuis plus de 14 jours, sans réponse. Il faut relancer.
- **M3** : il reste moins de 3 offres faisables. Mes mots-clés ou mes sources sont trop étroits.

**Exécutions :** run n°1 et run n°2 le 14/11/2026 (manuels), puis un run chaque jour.

**Ce que ça a montré :** `OK`, avec 9 offres faisables et 0 candidature envoyée. Si les 3 meilleures offres ne sont toujours pas postulées le 20/11, M1 passera en ALERT.

## 7. Confidentialité

- Les offres Indeed sont du contenu scrapé, non republiable (`publishable: false`). Le dashboard public ne montre que **mes** scores, anonymisés (« Offre indeed n°1 ») : jamais d'entreprise, de lieu, de lien ni de description.
- Le repo est public, donc le profil ne contient que des compétences et des preuves professionnelles : aucune coordonnée, aucune information administrative personnelle.
- Les lettres et le classement nominatif restent sur mon ordinateur.

## 8. Limites

- **France Travail :** l'API « Offres d'emploi v2 » ne figure plus dans la liste des API proposées aux nouvelles applications. Le script et le workflow sont conservés, avec `continue-on-error`, pour fonctionner dès que l'API sera de nouveau disponible.
- **Petit échantillon** (11 offres) et **profil auto-évalué** : le score sert à classer les offres, ce n'est pas une probabilité d'embauche.
- **Contraintes non modélisées :** certaines offres (défense) exigent une habilitation de sécurité. Le filtre ne la prend pas en compte ; je la vérifie à la main avant de postuler.

## 9. Décisions

1. Postuler d'abord à l'offre de conformité Cyber Resilience Act : c'est la plus proche de mon stage chez Atlas Cloud. Viennent ensuite IAM (après vérification de l'habilitation) et DevOps.
2. **Apprendre Kubernetes avant mars 2027** : c'est la lacune n°1, elle apparaît dans 4 offres faisables, et elle est cohérente avec mon profil cloud.
3. Mettre en avant dans chaque lettre l'automatisation de contrôles de conformité dans un pipeline CI/CD, mon point fort le plus différenciant.
