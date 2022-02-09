#! /usr/bin/env python3
import argparse
from jinja2 import Environment, PackageLoader
from pathlib import Path
import sys
import yaml


class CacheYaml:
    def __init__(self):
        self.cache = {}

    def load_yaml(self, repertoire, basename):
        if (repertoire, basename) not in self.cache:
            fichier = Path("data", repertoire, basename).with_suffix(".yaml")
            try:
                stream = open(fichier, 'r')
            except FileNotFoundError:
                print(f"{fichier} non trouvé")
                sys.exit(1)
            try:
                self.cache[(repertoire, basename)] = yaml.safe_load(stream)
            except yaml.YAMLError as e:
                print(f"erreur de syntaxe dans le fichier {fichier} (\"{e}\")")
                sys.exit(2)

        return self.cache[(repertoire, basename)]


class Touille:
    def __init__(self, cache):
        self.ingredients = {}
        self.produits = {}
        self.cache = cache
        self.env = Environment(loader=PackageLoader("calcule", "templates"))

    def detail(self, ingredient, quantite_ingredient):
        if ingredient in self.matieres:
            return self.matieres[ingredient]["prix"] * quantite_ingredient, {}
        else:
            recette = self.cache.load_yaml("recettes", ingredient)
            facteur = sum(recette.values())
            if ingredient not in self.ingredients:
                self.ingredients[ingredient] = {"recette": {}}
                if "prix-de-vente-1kg-ttc" in recette:
                    self.ingredients[ingredient]["quantite"] = 0
            prix = 0
            ingredients_recette = {}
            for sous_ingredient, quantite_sous_ingredient in recette.items():
                ingredients_dual = sous_ingredient.split('|')
                if len(ingredients_dual) == 1:
                    nom_ingredient, alias_ingredient = (sous_ingredient,) * 2
                else:
                    nom_ingredient, alias_ingredient = ingredients_dual
                quantite_ingredient_2 = (quantite_ingredient * quantite_sous_ingredient) / facteur
                if alias_ingredient in self.ingredients[ingredient]["recette"]:
                    self.ingredients[ingredient]["recette"][alias_ingredient] += quantite_ingredient_2
                else:
                    self.ingredients[ingredient]["recette"][alias_ingredient] = quantite_ingredient_2
                ingredients_recette[alias_ingredient] = quantite_ingredient_2
                prix2, _ = self.detail(nom_ingredient, quantite_ingredient_2)
                prix += prix2

            self.ingredients[ingredient]["poids-total"] = sum(self.ingredients[ingredient]["recette"].values())
            return prix, ingredients_recette

    def touille(self, matieres, commandes, general):
        self.commandes = self.cache.load_yaml("commandes", commandes)
        self.matieres = self.cache.load_yaml("matieres-premieres", matieres)
        self.general = self.cache.load_yaml(".", general)

        for produit, quantite in self.commandes.items():
            if quantite == 0:
                continue

            infos_produit = self.cache.load_yaml("produits", produit)
            self.produits[produit] = {}

            poids_paton = infos_produit["poids-paton"]
            poids = quantite * poids_paton
            taux_perte = infos_produit.get("taux-perte", 1)
            prix, recette = self.detail(infos_produit["recette"], poids * taux_perte)

            self.produits[produit]["recette"] = recette
            self.produits[produit]["quantite"] = quantite
            self.produits[produit]["poids-paton"] = poids_paton

            if "prix-de-vente-1kg-ttc" in infos_produit:
                prix_de_vente_piece_ttc = infos_produit["prix-de-vente-1kg-ttc"] * infos_produit["poids-pain-cuit"]
                self.produits[produit]["prix-de-vente-piece-ttc"] = prix_de_vente_piece_ttc

                prix_de_vente_piece_ht = prix_de_vente_piece_ttc / self.general["tva"]
                prix_de_revient_piece_ht = prix / quantite
                self.produits[produit]["prix-de-revient-piece-ht"] = prix_de_revient_piece_ht
                taux_marge_brute = (prix_de_vente_piece_ht - prix_de_revient_piece_ht) / prix_de_vente_piece_ht
                self.produits[produit]["taux-marge-brute"] = taux_marge_brute * 100

    def presente(self, html):
        print(yaml.dump(self.produits, default_flow_style=False))
        print(yaml.dump(self.ingredients, default_flow_style=False))

        if html is not None:
            template = self.env.get_template("template.html")
            with open(html + ".html", "w") as fichier:
                fichier.write(template.render(ingr=self.ingredients, prod=self.produits))


def float_representer(dumper, value):
    text = '{0:.3f}'.format(value)
    return dumper.represent_scalar(u'tag:yaml.org,2002:float', text)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--commandes", nargs='*', default=["commandes"])
    parser.add_argument("-m", "--matieres-premieres", default="matieres-premieres")
    parser.add_argument("-t", "--html")
    args = parser.parse_args()

    cache = CacheYaml()
    yaml.add_representer(float, float_representer)

    touille = Touille(cache)
    for cmd in args.commandes:
        touille.touille(args.matieres_premieres, cmd, "general")

    touille.presente(args.html)
