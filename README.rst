Calcule les quantité d'ingrédients à partir de commandes de produits et de
recettes.

Le répertoire *produits* décrit les produits.

Le répertoire *recettes* décrit les recettes des produits.

Le répertoire *matieres-premires* décrit les matières premières des recettes.Le fichier de
matières premieres par défaut se nomme matieres-premieres.yaml.


Le répertoire *commandes* décrit les commandes de produits. Le fichier de
commandes par défaut se nomme commandes.yaml.

Lancement du programme : ::

    python3 calcule.py

On peut lancer le programme sur plusieurs commandes : ::

    python3 calcule.py -c commandes-sures commandes-en-attente

On peut générer un fichier html. Voir le fichier plan.html.

    python3 calcule.py -t plan.html
