#! /usr/bin/env python3
import argparse
from jinja2 import Environment, PackageLoader
from pathlib import Path
import sys
import yaml

def load_yaml(repertoire, basename):
    fichier = Path("data", repertoire, basename).with_suffix(".yaml")
    try:
        stream = open(fichier, 'r')
    except FileNotFoundError:
        print(f"{fichier} non trouvé")
        sys.exit(1)
    return yaml.safe_load(stream)


def follow_recipe(raw_materials, ingredients, ingredient, quantite_ingredient):
    if ingredient in raw_materials:
        return raw_materials[ingredient]["prix"] * quantite_ingredient, {}
    else:
        recette = load_yaml("recettes", ingredient)
        facteur = sum(recette.values())
        if ingredient not in ingredients:
            ingredients[ingredient] = {"recette": {}}
            if "prix-de-vente-1kg-ttc" in recette:
                ingredients[ingredient]["quantite"] = 0
        prix = 0
        ingredients_recette = {}
        for sous_ingredient, quantite_sous_ingredient in recette.items():
            ingredients_dual = sous_ingredient.split('|')
            if len(ingredients_dual) == 1:
                nom_ingredient, alias_ingredient = (sous_ingredient,) * 2
            else:
                nom_ingredient, alias_ingredient = ingredients_dual
            quantite_ingredient_2 = (quantite_ingredient * quantite_sous_ingredient) / facteur
            if alias_ingredient in ingredients[ingredient]["recette"]:
                ingredients[ingredient]["recette"][alias_ingredient] += quantite_ingredient_2
            else:
                ingredients[ingredient]["recette"][alias_ingredient] = quantite_ingredient_2
            ingredients_recette[alias_ingredient] = quantite_ingredient_2
            prix2, _ = follow_recipe(raw_materials, ingredients, nom_ingredient, quantite_ingredient_2)
            prix += prix2

        ingredients[ingredient]["poids-total"] = sum(ingredients[ingredient]["recette"].values())
        return prix, ingredients_recette


def presente(html, produits, ingredients):
    print(yaml.dump(produits, default_flow_style=False))
    print(yaml.dump(ingredients, default_flow_style=False))

    if html is not None:
        env = Environment(loader=PackageLoader("calcule", "templates"))
        template = env.get_template("template.html")
        with open(html + ".html", "w") as fichier:
            fichier.write(template.render(ingr=ingredients, prod=produits))


def float_representer(dumper, value):
    text = '{0:.3f}'.format(value)
    return dumper.represent_scalar(u'tag:yaml.org,2002:float', text)


def main(raw_materials, orders, html):
    yaml.add_representer(float, float_representer)

    ingredients = {}
    produits = {}

    for order in orders:
        commandes = load_yaml("commandes", order)
        matieres = load_yaml("matieres-premieres", raw_materials)
        general = load_yaml(".", "general")

        for produit, quantite in commandes.items():
            if quantite == 0:
                continue

            infos_produit = load_yaml("produits", produit)
            produits[produit] = {}

            poids_paton = infos_produit["poids-paton"]
            poids = quantite * poids_paton
            taux_perte = infos_produit.get("taux-perte", 1)
            prix, recette = follow_recipe(matieres, ingredients, infos_produit["recette"], poids * taux_perte)

            produits[produit]["recette"] = recette
            produits[produit]["quantite"] = quantite
            produits[produit]["poids-paton"] = poids_paton

            if "prix-de-vente-1kg-ttc" in infos_produit:
                prix_de_vente_piece_ttc = infos_produit["prix-de-vente-1kg-ttc"] * infos_produit["poids-pain-cuit"]
                produits[produit]["prix-de-vente-piece-ttc"] = prix_de_vente_piece_ttc

                prix_de_vente_piece_ht = prix_de_vente_piece_ttc / general["tva"]
                prix_de_revient_piece_ht = prix / quantite
                produits[produit]["prix-de-revient-piece-ht"] = prix_de_revient_piece_ht
                taux_marge_brute = (prix_de_vente_piece_ht - prix_de_revient_piece_ht) / prix_de_vente_piece_ht
                produits[produit]["taux-marge-brute"] = taux_marge_brute * 100

    presente(html, produits, ingredients)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--commandes", nargs='*', default=["commandes"])
    parser.add_argument("-m", "--matieres-premieres", default="matieres-premieres")
    parser.add_argument("-t", "--html")
    args = parser.parse_args()

    main(args.matieres_premieres, args.commandes, args.html)
