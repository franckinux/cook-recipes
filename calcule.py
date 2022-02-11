#! /usr/bin/env python3
import argparse
from jinja2 import Environment, PackageLoader
from pathlib import Path
import sys
from typing import List
from typing import Optional
import yaml


def load_yaml(directory: str, basename: str):
    file_path = Path("data", directory, basename).with_suffix(".yaml")
    try:
        stream = open(file_path, 'r')
    except FileNotFoundError:
        print(f"{file_path} not found")
        sys.exit(1)
    return yaml.safe_load(stream)


def follow_recipe(
    base_ingredients: dict, sub_recipes: dict, recipe_name: str, recipe_quantity: float
):
    if recipe_name in base_ingredients:
        return base_ingredients[recipe_name]["price"] * recipe_quantity, {}
    else:
        recipe = load_yaml("recipes", recipe_name)
        denominator = sum(recipe.values())
        if recipe_name not in sub_recipes:
            sub_recipes[recipe_name] = {"recipe": {}}
            if "selling_price_per_kg_tax_inclusive" in recipe:
                sub_recipes[recipe_name]["quantity"] = 0
        recipe_price = 0
        recipe_ingredients = {}
        for ingredient, ingredient_quantity in recipe.items():
            ingredient_names = ingredient.split('|')
            if len(ingredient_names) == 1:
                ingredient_name, ingredient_alternate_name = (ingredient,) * 2
            else:
                ingredient_name, ingredient_alternate_name = ingredient_names
            quantity = (recipe_quantity * ingredient_quantity) / denominator
            if ingredient_alternate_name in sub_recipes[recipe_name]["recipe"]:
                sub_recipes[recipe_name]["recipe"][ingredient_alternate_name] += quantity
            else:
                sub_recipes[recipe_name]["recipe"][ingredient_alternate_name] = quantity
            recipe_ingredients[ingredient_alternate_name] = quantity
            ingredient_price, _ = follow_recipe(base_ingredients, sub_recipes, ingredient_name, quantity)
            recipe_price += ingredient_price

        sub_recipes[recipe_name]["total_weight"] = sum(sub_recipes[recipe_name]["recipe"].values())
        return recipe_price, recipe_ingredients


def text_report(products: dict, sub_recipes: dict):
    print(yaml.dump(products, default_flow_style=False))
    print(yaml.dump(sub_recipes, default_flow_style=False))


def html_report(products: dict, sub_recipes: dict, html_file: str):
    env = Environment(loader=PackageLoader("calcule", "templates"))
    template = env.get_template("template.html")
    html_path = Path(html_file).with_suffix(".html")
    with open(html_path, "w") as f:
        f.write(template.render(sub_recipes=sub_recipes, products=products))


def float_representer(dumper, value):
    text = '{0:.3f}'.format(value)
    return dumper.represent_scalar(u'tag:yaml.org,2002:float', text)


def main(
    base_ingredients_file: str, order_files: List[str], html_file: Optional[str]
):
    yaml.add_representer(float, float_representer)

    sub_recipes = {}
    products_end = {}

    general = load_yaml(".", "general")
    base_ingredients = load_yaml("ingredients", base_ingredients_file)
    for order_file in order_files:
        orders = load_yaml("orders", order_file)

        for order_product, order_quantity in orders.items():
            if order_quantity == 0:
                continue

            product = load_yaml("products", order_product)
            products_end[order_product] = {}

            dough_weight = product["dough_weight"]
            weight = order_quantity * dough_weight
            loss_rate = product.get("loss_rate", 1)
            price, recipe = follow_recipe(
                base_ingredients, sub_recipes, product["recipe"], weight * loss_rate
            )

            products_end[order_product]["recipe"] = recipe
            products_end[order_product]["quantity"] = order_quantity
            products_end[order_product]["dough_weight"] = dough_weight

            if "selling_price_per_kg_tax_inclusive" in product:
                selling_price_per_piece_tax_inclusive = product["selling_price_per_kg_tax_inclusive"] * product["bread_baked_weight"]
                products_end[order_product]["selling_price_per_piece_tax_inclusive"] = selling_price_per_piece_tax_inclusive

                selling_price_per_piece_tax_exclusive = selling_price_per_piece_tax_inclusive / general["vat"]
                cost_price_per_piece_tax_exclusive = price / order_quantity
                products_end[order_product]["cost_price_per_piece_tax_exclusive"] = cost_price_per_piece_tax_exclusive
                gross_margin_rate = (selling_price_per_piece_tax_exclusive - cost_price_per_piece_tax_exclusive) / selling_price_per_piece_tax_exclusive
                products_end[order_product]["gross_margin_rate"] = gross_margin_rate * 100

    text_report(products_end, sub_recipes)
    if html_file is not None:
        html_report(products_end, sub_recipes, html_file)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-o", "--orders", nargs='*', default=["orders"])
    parser.add_argument("-i", "--ingredients", default="ingredients")
    parser.add_argument("-t", "--html")
    args = parser.parse_args()

    main(args.ingredients, args.orders, args.html)
