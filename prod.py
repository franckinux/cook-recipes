import argparse
import json
import os
import pprint
import sys


class FormatPrinter(pprint.PrettyPrinter):
    def __init__(self, formats):
        super(FormatPrinter, self).__init__()
        self.formats = formats

    def format(self, obj, ctx, maxlvl, lvl):
        if type(obj) in self.formats:
            return self.formats[type(obj)] % obj, 1, 0
        return pprint.PrettyPrinter.format(self, obj, ctx, maxlvl, lvl)


class CacheJson:
    def __init__(self):
        self.cache = {}

    def load_json(self, repertoire, basename):
        if basename not in self.cache:
            fichier = os.path.join(repertoire, basename + ".json")
            try:
                json_data = open(fichier, "r")
            except Exception:
                print(f"{basename}.json non trouvé")
                sys.exit(1)
            try:
                self.cache[basename] = json.load(json_data)
            except json.decoder.JSONDecodeError as e:
                print(f"erreur de syntaxe dans le fichier {basename}.json (\"{e}\")")
                sys.exit(2)

        return self.cache[basename]


class Touille:
    def __init__(self, cache):
        self.ingredients = {}
        self.cache = cache

    def detail(self, ingredient, quantite_ingredient):
        if ingredient in self.matieres:
            return self.matieres[ingredient]["prix"] * quantite_ingredient, {}
        else:
            recette = self.cache.load_json("recettes", ingredient)
            try:
                facteur = sum(recette.values())
            except:
                import pdb; pdb.set_trace()
            if ingredient not in self.ingredients:
                self.ingredients[ingredient] = {"recette": {}}
                if "prix-de-vente-1kg-ttc" in recette:
                    self.ingredients[ingredient]["prix-de-revient-ht"] = 0
                    self.ingredients[ingredient]["quantite"] = 0
            prix = 0
            ingredients_recette = {}
            for sous_ingredient, quantite_sous_ingredient in recette.items():
                if sous_ingredient.startswith('-'):
                    continue
                ingredients_dual = sous_ingredient.split(':')
                if len(ingredients_dual) == 1:
                    nom_ingredient, alias_ingredient = sous_ingredient, sous_ingredient
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
        self.commandes = self.cache.load_json("commandes", commandes)
        self.matieres = self.cache.load_json("matieres-premieres", matieres)
        self.general = self.cache.load_json(".", general)

        for produit, quantite in self.commandes.items():
            infos_produit = self.cache.load_json("produits", produit)
            self.ingredients[produit] = {}

            poids_paton = infos_produit["poids-paton"]
            poids = quantite * poids_paton
            taux_perte = infos_produit.get("taux-perte", 1)
            prix, recette = self.detail(infos_produit["recette"], poids * taux_perte)

            self.ingredients[produit]["recette"] = recette
            self.ingredients[produit]["quantite"] = quantite
            self.ingredients[produit]["poids-paton"] = poids_paton

            if "prix-de-vente-1kg-ttc" in infos_produit:
                prix_de_vente_piece_ttc = infos_produit["prix-de-vente-1kg-ttc"] * infos_produit["poids-pain-cuit"]
                self.ingredients[produit]["prix-de-vente-piece-ttc"] = prix_de_vente_piece_ttc

                prix_de_vente_piece_ht = prix_de_vente_piece_ttc / self.general["tva"]
                prix_de_revient_piece_ht = prix / quantite
                taux_marge_brute = (prix_de_vente_piece_ht - prix_de_revient_piece_ht) / prix_de_vente_piece_ht
                self.ingredients[produit]["taux-marge-brute"] = taux_marge_brute * 100


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--commandes", nargs='*', default=["commandes"])
    parser.add_argument("-m", "--matieres-premieres", default="matieres-premieres")
    args = parser.parse_args()

    cache = CacheJson()
    touille = Touille(cache)
    for cmd in args.commandes:
        touille.touille(args.matieres_premieres, cmd, "general")
    FormatPrinter({float: "%.3f"}).pprint(touille.ingredients)
