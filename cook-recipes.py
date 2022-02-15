#! /usr/bin/env python3
import argparse
from functools import cache
from jinja2 import Environment, PackageLoader
from pathlib import Path
import sys
from typing import List
from typing import Optional
import yaml


@cache
def load_yaml(directory: str, basename: str) -> dict:
    file_path = Path("data", directory, basename).with_suffix(".yaml")
    try:
        stream = open(file_path, 'r')
    except FileNotFoundError:
        print(f"{file_path} not found")
        sys.exit(1)
    return yaml.safe_load(stream)


def follow_recipe(
    base_ingredients: dict, recipes: dict, recipe_name: str, recipe_quantity: float
) -> (float, dict):
    if recipe_name in base_ingredients:
        return base_ingredients[recipe_name]["price"] * recipe_quantity, {}
    else:
        recipe = load_yaml("recipes", recipe_name)
        denominator = sum(recipe.values())
        if recipe_name not in recipes:
            recipes[recipe_name] = {"recipe": {}}
            if "selling_price_per_kg_incl_taxes" in recipe:
                recipes[recipe_name]["quantity"] = 0
        recipe_price = 0
        recipe_ingredients = {}
        for ingredient, ingredient_quantity in recipe.items():
            ingredient_names = ingredient.split('|')
            if len(ingredient_names) == 1:
                ingredient_name, ingredient_alternate_name = (ingredient,) * 2
            else:
                ingredient_name, ingredient_alternate_name = ingredient_names
            quantity = (recipe_quantity * ingredient_quantity) / denominator
            if ingredient_alternate_name in recipes[recipe_name]["recipe"]:
                recipes[recipe_name]["recipe"][ingredient_alternate_name] += quantity
            else:
                recipes[recipe_name]["recipe"][ingredient_alternate_name] = quantity
            recipe_ingredients[ingredient_alternate_name] = quantity
            ingredient_price, _ = follow_recipe(base_ingredients, recipes, ingredient_name, quantity)
            recipe_price += ingredient_price

        recipes[recipe_name]["total_weight"] = sum(recipes[recipe_name]["recipe"].values())
        return recipe_price, recipe_ingredients


def text_report(products: dict, recipes: dict):
    print(yaml.dump(products, default_flow_style=False))
    print(yaml.dump(recipes, default_flow_style=False))


def html_report(products: dict, recipes: dict, html_file: str):
    env = Environment(loader=PackageLoader("cook-recipes", "templates"))
    template = env.get_template("template.html")
    html_path = Path(html_file).with_suffix(".html")
    with open(html_path, "w") as f:
        f.write(template.render(recipes=recipes, products=products))


def float_representer(dumper, value):
    text = '{0:.3f}'.format(value)
    return dumper.represent_scalar(u'tag:yaml.org,2002:float', text)


def main(
    base_ingredients_file: str, order_files: List[str], html_file: Optional[str]
):
    yaml.add_representer(float, float_representer)

    recipes = {}
    products = {}

    general = load_yaml(".", "general")
    base_ingredients = load_yaml("ingredients", base_ingredients_file)
    for order_file in order_files:
        orders = load_yaml("orders", order_file)

        for order_product, order_quantity in orders.items():
            if order_quantity == 0:
                continue

            product = load_yaml("products", order_product)
            products[order_product] = {}

            dough_weight = product["dough_weight"]
            weight = order_quantity * dough_weight
            loss_rate = product.get("loss_rate", 1)
            price, recipe = follow_recipe(
                base_ingredients, recipes, product["recipe"], weight * loss_rate
            )

            products[order_product]["recipe"] = recipe
            products[order_product]["quantity"] = order_quantity
            products[order_product]["dough_weight"] = dough_weight

            if "selling_price_per_kg_incl_taxes" in product:
                selling_price_per_piece_incl_taxes = product["selling_price_per_kg_incl_taxes"] * product["bread_baked_weight"]
                products[order_product]["selling_price_per_piece_incl_taxes"] = selling_price_per_piece_incl_taxes

                selling_price_per_piece_excl_taxes = selling_price_per_piece_incl_taxes / general["vat"]
                cost_price_per_piece_excl_taxes = price / order_quantity
                products[order_product]["cost_price_per_piece_excl_taxes"] = cost_price_per_piece_excl_taxes
                gross_margin_rate = (selling_price_per_piece_excl_taxes - cost_price_per_piece_excl_taxes) / selling_price_per_piece_excl_taxes
                products[order_product]["gross_margin_rate"] = gross_margin_rate * 100

    text_report(products, recipes)
    if html_file is not None:
        html_report(products, recipes, html_file)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-o", "--orders", nargs='*', default=["orders"])
    parser.add_argument("-i", "--ingredients", default="ingredients")
    parser.add_argument("-t", "--html")
    args = parser.parse_args()

    main(args.ingredients, args.orders, args.html)
