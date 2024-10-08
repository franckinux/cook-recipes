#! /usr/bin/env python3

import argparse
from datetime import datetime
from functools import cache
from pathlib import Path
import sys
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

from babel.dates import format_datetime
from babel.support import Translations
from jinja2 import Environment, FileSystemLoader, select_autoescape
import yaml

base_ingredients = {}
recipes = {}


@cache
def load_yaml(directory: str, basename: str) -> Any:
    file_path = Path("data", directory, basename).with_suffix(".yaml")
    try:
        with open(file_path, 'r') as stream:
            return yaml.safe_load(stream)
    except FileNotFoundError:
        print(f"{file_path} not found", file=sys.stderr)
        sys.exit(1)


def follow_recipe(recipe_name: str, recipe_quantity: float) -> float:
    global recipes

    if recipe_name in base_ingredients:
        return base_ingredients[recipe_name]["price"] * recipe_quantity
    else:
        recipe = load_yaml("recipes", recipe_name)
        denominator = sum(recipe.values())
        if recipe_name not in recipes:
            recipes[recipe_name] = {"recipe": {}}
            if "selling_price_per_kg_incl_taxes" in recipe:
                recipes[recipe_name]["quantity"] = 0
        recipe_price = 0.0
        for ingredient, ingredient_quantity in recipe.items():
            try:
                ingredient_name, ingredient_alternate_name = ingredient.split('|')
            except ValueError:
                ingredient_name, ingredient_alternate_name = (ingredient,) * 2
            quantity = (recipe_quantity * ingredient_quantity) / denominator
            if ingredient_alternate_name in recipes[recipe_name]["recipe"]:
                recipes[recipe_name]["recipe"][ingredient_alternate_name] += quantity
            else:
                recipes[recipe_name]["recipe"][ingredient_alternate_name] = quantity
            recipe_price += follow_recipe(ingredient_name, quantity)

        recipes[recipe_name]["total_weight"] = sum(recipes[recipe_name]["recipe"].values())
        return recipe_price


def text_report(products: dict, recipes: dict):
    print(yaml.dump(products, default_flow_style=False))
    print(yaml.dump(recipes, default_flow_style=False))


def html_report(
    products: dict, recipes: dict, colors: dict, html_file: str, locale: str,
    title: str
):
    env = Environment(
        extensions=["jinja2.ext.i18n"],
        loader=FileSystemLoader("./templates"),
        autoescape=select_autoescape()
    )
    translations = Translations.load("locales/translations", [locale])
    env.install_gettext_translations(translations)
    template = env.get_template("template.html")
    html_path = Path(html_file).with_suffix(".html")
    with open(html_path, "w") as f:
        f.write(template.render(
            recipes=recipes, products=products, colors=colors, title=title
        ))


def float_representer(dumper, value):
    text = '{0:.3f}'.format(value)
    return dumper.represent_scalar(u'tag:yaml.org,2002:float', text)


def main(
    base_ingredients_file: str, order_files: List[str], html_file: Optional[str],
    locale: str, title: str
):
    global base_ingredients

    yaml.add_representer(float, float_representer)

    products: Dict = {}

    general = load_yaml(".", "general")
    colors = load_yaml(".", "colors")
    base_ingredients = load_yaml("ingredients", base_ingredients_file)
    for order_file in order_files:
        orders = load_yaml("orders", order_file)

        for order_product, order_quantity in orders.items():
            if order_quantity == 0:
                continue

            product = load_yaml("products", order_product)
            products[order_product] = {}

            dough_weight = product["dough_weight"]
            loss_rate = product.get("loss_rate", 1)
            weight = order_quantity * dough_weight * loss_rate
            price = follow_recipe(product["recipe"], weight)

            products[order_product]["recipe"] = {product["recipe"]: weight}
            products[order_product]["quantity"] = order_quantity
            products[order_product]["dough_weight"] = dough_weight

            if "selling_price_per_kg_incl_taxes" in product:
                selling_price_per_kg_incl_taxes = product["selling_price_per_kg_incl_taxes"]
                products[order_product]["selling_price_per_kg_incl_taxes"] = selling_price_per_kg_incl_taxes
                selling_price_per_piece_incl_taxes = selling_price_per_kg_incl_taxes * product["bread_baked_weight"]
                products[order_product]["selling_price_per_piece_incl_taxes"] = selling_price_per_piece_incl_taxes

                selling_price_per_piece_excl_taxes = selling_price_per_piece_incl_taxes / general["vat"]
                products[order_product]["selling_price_per_piece_excl_taxes"] = selling_price_per_piece_excl_taxes
                cost_price_per_piece_excl_taxes = price / order_quantity
                products[order_product]["cost_price_per_piece_excl_taxes"] = cost_price_per_piece_excl_taxes
                gross_margin_rate = (selling_price_per_piece_excl_taxes - cost_price_per_piece_excl_taxes) \
                    / selling_price_per_piece_excl_taxes
                products[order_product]["gross_margin_rate"] = gross_margin_rate * 100

    text_report(products, recipes)
    if html_file is not None:
        html_report(products, recipes, colors, html_file, locale, title)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-o", "--orders", nargs='*', default=["orders"])
    parser.add_argument("-i", "--ingredients", default="ingredients")
    parser.add_argument("-m", "--html")
    parser.add_argument("-l", "--locale", default="en")
    parser.add_argument("-t", "--title")
    args = parser.parse_args()

    title = args.title if args.title is not None else format_datetime(datetime.now(), locale=args.locale)

    main(args.ingredients, args.orders, args.html, args.locale, title)
