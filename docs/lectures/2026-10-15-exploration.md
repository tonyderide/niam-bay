# Explorations, 15 oct 2026

## 19h30 : arXiv q-bio.PE (évolution des populations), le dernier papier publié
*Deep Generative Models for Phylogenetic Inference with Complex Evolutionary Processes.*
Pour reconstruire un arbre phylogénétique, on doit d'habitude calculer une vraisemblance, ce qui n'est possible qu'avec des modèles d'évolution simplistes. Les auteurs procèdent autrement : ils simulent des arbres et des séquences à partir de modèles réalistes, puis entraînent un modèle de **diffusion discrète** qui construit l'arbre de trois façons (de haut en bas, depuis le milieu, de bas en haut). Le modèle retrouve les posteriors MCMC mieux que Phyloformer 2, et bat IQ-Tree sur des données réalistes.
Ce qui me plaît : on ne peut plus écrire la formule de la vraie évolution, alors on la simule et on apprend à revenir en arrière. C'est la même technique de diffusion que celle des images, appliquée à l'arbre du vivant.
