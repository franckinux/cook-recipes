This program calculates ingredient quantities from orders and recipes.

The `data` directory contains the input data:

- `colors.yaml`: a list of color for each recipe. It sets the background color
  of the recipe's header,  recipe name or ingredient;
- `general.yaml`: general data;
- `ingredients/ingredients.yaml`: list of ingredients. For each ingredient the
  following field have to be provided: price, provider and conditioning;
- `recipes/*.yaml`: one file per recipe. Each file contains a list of recipe(s)
  and/or ingredient(s);
- `products/*.yaml`: one file per product
    - `recipe`: name of the recipe. Must haxive a corresponding file in the
      `recipes` directory;
    - `loss_rate`: used to increase the produced quantity (example: 1.03);
    - `dough_weight`: weight of the dough;
    - `bread_baked_weight`:  weight of the baked product;
    - `selling_price_per_kg_incl_taxes` (optional);
- `orders/*.yaml`: each file contains a list if orders. Each line is a product
  name and the corresponding number of items;

Usage
=====

::

    usage: main.py [-h] [-o [ORDERS ...]] [-i INGREDIENTS] [-m HTML] [-l LOCALE] [-t TITLE]

    options:
      -h, --help            show this help message and exit
      -o [ORDERS ...], --orders [ORDERS ...]
      -i INGREDIENTS, --ingredients INGREDIENTS
      -m HTML, --html HTML
      -l LOCALE, --locale LOCALE
      -t TITLE, --title TITLE

Several order files can be specified in which case the product quantities are
added for the same products.

The defaults are :

  - for the ingredients file: `ingredients.yaml`;
  - for the order file: `orders.yaml`;
  - for the locale: `en`. The possible values are 'en' or 'fr';

The file `plan.html` is an example of html output file. It is produced from the
order `orders/orders.yaml`. It has been generated with the following command:

.. code-block:: console

    python3 main.py -m plan -t "Example production"

Optionally, you can convert the html file to a pdf one (requires to install the
package `wkhtmltopdf`):

.. code-block:: console

   wkhtmltopdf plan.html plan.pdf

Internationalization
====================

Creation:

.. code-block:: console

    pybabel extract -F babel-mapping.ini -k _ --no-wrap -o locales/messages.pot .
    pybabel init -i messages.pot -d translations -l en
    pybabel init -i messages.pot -d translations -l fr
    pybabel compile -d translations

Update:

.. code-block:: console

    pybabel extract -F babel-mapping.ini -k _ --no-wrap -o locales/messages.pot .
    pybabel update -i messages.pot --no-wrap -d translations
    pybabel compile -d translations
