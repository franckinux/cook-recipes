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
    def __init__(self, repertoires):
        self.cache = {}
        self.repertoires = repertoires

    def load_json(self, basename):
        if basename not in self.cache:
            ok = False
            for dir in self.repertoires:
                try:
                    fichier = os.path.join(dir, basename + ".json")
                    json_data = open(fichier, "r")
                    ok = True
                except Exception:
                    continue
            if not ok:
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

    def detail(self, produit, quantite):
        if produit in self.matieres:
            return self.matieres[produit]["prix"] * quantite
        else:
            recette = self.cache.load_json(produit)
            facteur = sum(recette["ingredients"].values())
            quantite *= recette.get("taux-perte", 1)
            quantite *= recette.get("poids-paton", 1)
            securite = recette.pop("securite", 0)
            if produit not in self.ingredients:
                self.ingredients[produit] = {"recette": {}}
                if "prix-de-vente-1kg-ttc" in recette:
                    self.ingredients[produit]["prix-de-revient"] = 0
            prix = 0
            for ingredient, quantite_ingredient in recette["ingredients"].items():
                # la sécurité est répercutée sur les quantités...
                quantite += securite
                quantite_ingredient_2 = (quantite * quantite_ingredient) / facteur
                if ingredient in self.ingredients[produit]["recette"]:
                    self.ingredients[produit]["recette"][ingredient] += quantite_ingredient_2
                else:
                    self.ingredients[produit]["recette"][ingredient] = quantite_ingredient_2
                # ... mais pas sur les coûts !
                quantite -= securite
                quantite_ingredient_2 = (quantite * quantite_ingredient) / facteur
                prix += self.detail(ingredient, quantite_ingredient_2)

            self.ingredients[produit]["poids-total"] = sum(self.ingredients[produit]["recette"].values())
            if "prix-de-vente-1kg-ttc" in recette:
                self.ingredients[produit]["prix-de-revient"] += prix

            if "prix-de-vente-1kg-ttc" in recette:
                prix_de_vente_1kg_ht = recette["prix-de-vente-1kg-ttc"] / self.general["tva"]
                prix_de_revient_1kg_ht = prix / quantite
                taux_marge_brute = (prix_de_vente_1kg_ht - prix_de_revient_1kg_ht ) / prix_de_vente_1kg_ht
                self.ingredients[produit]["taux-marge-brute"] = taux_marge_brute * 100

            return prix

    def touille(self, matieres, commandes, general):
        self.commandes = self.cache.load_json(commandes)
        self.matieres = self.cache.load_json(matieres)
        self.general = self.cache.load_json(general)

        for commande, quantite_commande in self.commandes.items():
            self.detail(commande, quantite_commande)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--commandes", nargs='*', default=["commandes"])
    parser.add_argument("-m", "--matieres-premieres", default="matieres-premieres")
    parser.add_argument("-r", "--repertoires", nargs='*', default=[".", "recettes","commandes","matieres-premieres"])
    args = parser.parse_args()

    cache = CacheJson(args.repertoires)
    touille = Touille(cache)
    for cmd in args.commandes:
        touille.touille(args.matieres_premieres, cmd, "general")
    FormatPrinter({float: "%.2f"}).pprint(touille.ingredients)
