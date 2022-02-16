Calcule les quantités d'ingrédients à partir de commandes de produits et de
recettes.

Le répertoire *produits* décrit les produits.

Le répertoire *recettes* décrit les recettes des produits.

Le répertoire *matieres-premieres* décrit les matières premières des recettes.Le fichier de
matières premieres par défaut se nomme matieres-premieres.yaml.


Le répertoire *commandes* décrit les commandes de produits. Le fichier de
commandes par défaut se nomme commandes.yaml.

Lancement du programme : ::

    python3 calcule.py

On peut lancer le programme sur plusieurs commandes : ::

    python3 calcule.py -c commandes-sures commandes-en-attente

On peut générer un fichier html. Voir le fichier plan.html.

    python3 calcule.py -t plan.html

En plus des quantités, le programme calcule le prix de revient et la marge
brute.

Exemple de sortie du programme : ::

        banneton-1kg-nature:
          poids-paton: 1.180
          prix-de-revient-piece-ht: 1.512
          prix-de-vente-piece-ttc: 4.500
          quantite: 2
          recette:
            pate-base-campagne: 2.431
          taux-marge-brute: 64.557
        banneton-500g-nature:
          poids-paton: 0.588
          prix-de-revient-piece-ht: 0.753
          prix-de-vente-piece-ttc: 2.250
          quantite: 19
          recette:
            pate-base-campagne: 11.507
          taux-marge-brute: 64.678
        faconne-700g-graines:
          poids-paton: 0.825
          prix-de-revient-piece-ht: 1.314
          prix-de-vente-piece-ttc: 4.550
          quantite: 17
          recette:
            eau-hydratation-graines: 1.605
            melange-graines-1: 1.605
            melange-graines-2: 0.535
            pate-base-campagne: 10.701
          taux-marge-brute: 69.540
        securite-levain:
          poids-paton: 0.300
          quantite: 1
          recette:
            eau: 0.164
            farine-t170: 0.136

        campagne-graines-topping:
          poids-total: 14.446
          recette:
            eau-hydratation-graines: 1.605
            melange-graines-1: 1.605
            melange-graines-2: 0.535
            pate-base-campagne: 10.701
        campagne-nature:
          poids-total: 13.938
          recette:
            pate-base-campagne: 13.938
        levain-seigle-120pch:
          poids-total: 2.801
          recette:
            eau: 1.528
            farine-t170: 1.273
        melange-graines-1:
          poids-total: 1.605
          recette:
            lin-brun: 0.214
            lin-dore: 0.214
            sesame: 0.107
            tournesol: 1.070
        melange-graines-2:
          poids-total: 0.535
          recette:
            avoine-gros: 0.141
            lin-brun: 0.056
            lin-dore: 0.056
            tournesol: 0.282
        pate-base-campagne:
          poids-total: 24.639
          recette:
            eau-de-bassinage: 0.875
            eau-de-frasage: 8.505
            farine-t80: 12.507
            levain-seigle-120pch: 2.501
            sel: 0.250

Internationalization
====================

Creation: ::

.. code-block:: console

    pybabel extract -F babel-mapping.ini -k _ --no-wrap -o locales/messages.pot .
    pybabel init -i messages.pot -d translations -l en
    pybabel init -i messages.pot -d translations -l fr
    pybabel compile -d translations

Update: ::

.. code-block:: console

    pybabel extract -F babel-mapping.ini -k _ --no-wrap -o locales/messages.pot .
    pybabel update -i messages.pot --no-wrap -d translations
    pybabel compile -d translations
