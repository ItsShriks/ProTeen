import argparse
import csv
import json
import os
import random
import re
import ssl
import sys
import urllib.parse
import urllib.request
import uuid
from datetime import datetime

# ------------------------------------------------------------------
# Configuration
# ------------------------------------------------------------------

MARKET_SEARCH_URL = "https://www.rewe.de/api/marketselection/zipcodes/{plz}/services/pickup"
OFFERS_URL = "https://mobile-clients-api.rewe.de/api/stationary-offers/{market_id}"

OUTPUT_FILE = "discounts.json"
MEALS_FILE = "Meals.csv"

BROWSER_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/130.0 Safari/537.36"
)
APP_DEVICES = [
    "Phone/Google_Pixel_8", "Phone/Google_Pixel_7a", "Phone/Samsung_SM-S911B",
    "Phone/Samsung_SM-G975U", "Phone/OnePlus_HD1925",
]

# Offer categories that never contain cooking ingredients
NON_FOOD_CATEGORY_WORDS = [
    "drogerie", "haushalt", "tier", "baby", "kosmetik", "pflege",
    "wein", "bier", "spirituosen", "sekt", "non-food", "blumen",
]

# English ingredient (as written in Meals.csv, lowercased) ->
#   (German keywords that must appear in the offer title,
#    words that disqualify a match)
INGREDIENT_KEYWORDS = {
    "onion": (["zwiebel"], ["ring", "chips", "schmalz"]),
    "tomato": (["tomate"], ["ketchup", "mark", "suppe", "chips", "passiert", "sauce", "soße"]),
    "tomatoes": (["tomate"], ["ketchup", "mark", "suppe", "chips", "passiert", "sauce", "soße"]),
    "cherry tomatoes": (["cherrytomate", "cocktailtomate", "rispentomate", "snacktomate"], []),
    "tomato passata": (["passata", "passierte tomate"], []),
    "potato": (["kartoffel"], ["chips", "püree", "salat", "kloß", "klöße", "puffer", "rösti"]),
    "garlic": (["knoblauch"], ["baguette", "brot", "dip"]),
    "garlic paste": (["knoblauch"], ["baguette", "brot", "dip"]),
    "ginger": (["ingwer"], ["shot", "tee", "bier", "ale"]),
    "ginger paste": (["ingwer"], ["shot", "tee", "bier", "ale"]),
    "paneer": (["paneer"], []),
    "milk": (["milch", "h-milch", "vollmilch"],
             ["schoko", "reis", "brötchen", "kaffee", "eis", "kondens", "mix", "shake", "creme"]),
    "soy milk": (["sojadrink", "soja drink", "soja-drink"], []),
    "butter": (["butter"], ["keks", "gebäck", "brezel", "croissant", "erdnuss", "milch", "schmalz", "kuchen"]),
    "ghee": (["ghee", "butterschmalz"], []),
    "oil or ghee": (["ghee", "butterschmalz", "sonnenblumenöl", "rapsöl"], []),
    "cream": (["schlagsahne", "kochsahne", "sahne"], ["saure", "eis", "torte", "joghurt", "pudding", "likör"]),
    "sour cream": (["saure sahne", "sauerrahm", "schmand", "crème fraîche", "creme fraiche"], []),
    "white sauce": (["béchamel", "bechamel", "helle sauce"], []),
    "yogurt": (["joghurt"], ["drink", "riegel", "gums", "dressing"]),
    "cheese": (["käse", "gouda", "emmentaler", "cheddar"], ["kuchen", "sahne", "brötchen", "frisch", "spätzle"]),
    "gouda cheese": (["gouda"], []),
    "feta cheese": (["feta", "hirtenkäse", "schafskäse"], []),
    "mozzarella": (["mozzarella"], ["pizza"]),
    "frischkäse": (["frischkäse"], ["körnig"]),
    "körniger frischkäse": (["körniger frischkäse", "hüttenkäse"], []),
    "magerquark": (["magerquark", "quark"], ["kuchen", "dessert"]),
    "rice": (["reis", "basmati", "jasmin"], ["waffel", "milchreis", "essig", "drink", "nudel", "riegel"]),
    "pasta": (["pasta", "spaghetti", "penne", "fusilli", "farfalle", "rigatoni", "nudeln"],
              ["sauce", "soße", "salat", "fertig", "mie", "instant"]),
    "noodles": (["mie-nudeln", "mie nudeln", "mienudeln", "udon", "ramen", "eiernudeln"], []),
    "instant noodles": (["instant", "nudelsnack", "yum yum"], []),
    "lasagna sheets": (["lasagne"], ["fertig", "tiefkühl"]),
    "fresh cheese tortellini": (["tortellini"], []),
    "fresh gnocchi": (["gnocchi"], []),
    "vegane maultaschen": (["maultaschen"], []),
    "quinoa": (["quinoa"], []),
    "instant couscous": (["couscous"], []),
    "rolled oats": (["haferflocken"], ["riegel", "keks"]),
    "müsli": (["müsli", "granola", "crunchy"], ["riegel"]),
    "bread": (["brot", "toast"], ["aufstrich", "chips", "knoblauch", "brötchen"]),
    "whole grain bread": (["vollkorn"], ["nudel", "keks", "reis"]),
    "pav": (["brötchen", "burger bun", "burger-bun"], []),
    "tortilla wraps": (["wraps", "tortilla"], ["chips"]),
    "taco shells": (["taco"], []),
    "salsa": (["salsa"], []),
    "hummus": (["hummus"], []),
    "falafel": (["falafel"], []),
    "banana": (["banane"], ["chips"]),
    "lemon": (["zitrone"], ["limonade", "tee", "eis", "saft"]),
    "avocado": (["avocado"], []),
    "avacado": (["avocado"], []),
    "spinach": (["spinat"], ["tortellini", "pizza"]),
    "cabbage": (["weißkohl", "spitzkohl", "rotkohl", "chinakohl"], []),
    "cauliflower": (["blumenkohl"], []),
    "borocolli": (["brokkoli", "broccoli"], []),
    "carrot": (["karotte", "möhre"], ["saft"]),
    "capsicum": (["paprika"], ["chips", "pulver", "gewürz", "edelsüß", "salami", "wurst", "paste"]),
    "red paprika chilli": (["paprikapulver", "paprika edelsüß", "paprika rosenscharf"], []),
    "cucumber": (["gurke"], ["gewürz", "essig", "glas"]),
    "green peas": (["erbsen"], ["kicher", "suppe"]),
    "corn": (["mais"], ["chips", "waffel", "stärke", "flakes"]),
    "canned corn": (["mais"], ["chips", "waffel", "stärke", "flakes"]),
    "salad mix": (["salatmix", "salatmischung", "eisbergsalat", "rucola", "feldsalat", "kopfsalat"], []),
    "green chilies": (["chili", "peperoni"], ["sauce", "soße", "chips", "con carne", "pulver"]),
    "red chillies": (["chili", "peperoni"], ["sauce", "soße", "chips", "con carne", "pulver"]),
    "mint": (["minze"], ["tee", "kaugummi", "bonbon"]),
    "coriander": (["koriander"], []),
    "coriander leaves": (["koriander"], []),
    "frozen berries": (["beerenmischung", "himbeeren", "heidelbeeren", "beeren"], ["joghurt", "saft", "tee", "konfitüre"]),
    "frozen pizza": (["pizza"], ["teig"]),
    "frozen spring rolls": (["frühlingsrolle"], []),
    "frozen wok vegetables": (["wokgemüse", "wok-gemüse", "gemüsepfanne"], []),
    "vegetables": (["gemüse"], ["brühe", "chips", "saft"]),
    "chickpeas": (["kichererbsen"], []),
    "canned chickpeas": (["kichererbsen"], []),
    "kidney beans": (["kidneybohnen", "kidney-bohnen", "kidney bohnen"], []),
    "rajma": (["kidneybohnen", "kidney-bohnen", "kidney bohnen"], []),
    "canned baked beans": (["baked beans", "weiße bohnen"], []),
    "canned lentil soup": (["linsensuppe", "linseneintopf"], []),
    "red dal": (["rote linsen"], []),
    "yellow moong dal": (["gelbe linsen", "mungbohnen"], []),
    "soya": (["soja schnetzel", "sojaschnetzel", "soja-schnetzel"], []),
    "smoked tofu": (["tofu"], []),
    "peanuts": (["erdnüsse", "erdnusskerne"], ["butter", "creme", "flips", "schoko"]),
    "peanut butter": (["erdnussbutter", "erdnusscreme", "erdnussmus"], []),
    "cashew": (["cashew"], ["schoko", "mus"]),
    "nuts": (["nüsse", "nusskerne", "mandeln", "walnuss", "studentenfutter"], ["schoko", "nougat", "creme"]),
    "chia seeds": (["chia"], []),
    "honey": (["honig"], ["melone", "pops", "senf"]),
    "fruit jam": (["konfitüre", "marmelade", "fruchtaufstrich"], []),
    "chocolate chips": (["schokotropfen", "backschokolade", "kuvertüre"], []),
    "chocolate powder": (["kakao", "trinkschokolade", "kaba", "nesquik"], []),
    "sugar": (["zucker"], ["zuckerfrei", "ohne zucker", "puder", "watte", "erbsen", "mais", "rübe"]),
    "flour 405": (["mehl"], ["mehlwurm"]),
    "semolina": (["grieß"], ["brei", "pudding"]),
    "oil": (["sonnenblumenöl", "rapsöl", "speiseöl", "pflanzenöl"], []),
    "olive oil": (["olivenöl"], []),
    "vinegar": (["essig"], ["gurke"]),
    "soy sauce": (["sojasauce", "sojasoße", "soja sauce", "soja soße"], []),
    "pesto verde": (["pesto"], []),
    "vegetable broth": (["gemüsebrühe"], []),
    "salt": (["speisesalz", "meersalz", "jodsalz"], []),
    "black pepper": (["pfeffer"], ["minze", "salami", "beißer"]),
    "italian herbs": (["kräuter der provence", "italienische kräuter", "kräutermischung"], []),
    "baking powder": (["backpulver"], []),
    "ei ersatz": (["ei ersatz", "ei-ersatz", "eiersatz", "vegg"], []),
}


# ------------------------------------------------------------------
# HTTP Helpers
# ------------------------------------------------------------------


def http_get_json(url, headers=None, ssl_context=None, timeout=30):
    req = urllib.request.Request(url, headers=headers or {})
    with urllib.request.urlopen(req, timeout=timeout, context=ssl_context) as resp:
        body = resp.read().decode("utf-8")

    if body.lstrip().startswith("<!DOCTYPE html>"):
        raise RuntimeError("Got an HTML page instead of JSON (blocked by Cloudflare).")

    return json.loads(body)


def search_markets(postcode):
    url = MARKET_SEARCH_URL.format(plz=urllib.parse.quote(postcode))
    headers = {"User-Agent": BROWSER_UA, "Accept": "application/json"}
    return http_get_json(url, headers=headers)


def fetch_rewe_offers(market_id, cert_file, key_file):
    """
    Fetch the weekly offers of one REWE market from the REWE app backend.
    Requires the mTLS client certificate shipped inside the REWE Android app.
    """
    context = ssl.create_default_context()
    context.load_cert_chain(certfile=cert_file, keyfile=key_file)

    headers = {
        "User-Agent": f"REWE-Mobile-Client/5.18.1.54501 Android/14 {random.choice(APP_DEVICES)}",
        "x-instana-android": str(uuid.uuid4()),
        "Accept": "application/json",
    }
    raw = http_get_json(OFFERS_URL.format(market_id=market_id), headers=headers, ssl_context=context)
    return parse_rewe_offers(raw)


def parse_price(text):
    if not text:
        return None
    match = re.search(r"(\d{1,3}(?:\.\d{3})*),(\d{2})", text)
    if not match:
        return None
    return float(match.group(1).replace(".", "") + "." + match.group(2))


def parse_rewe_offers(raw):
    offers_root = raw.get("data", {}).get("offers", {})
    week = offers_root.get("current", {})
    next_week = offers_root.get("next", {})
    if offers_root.get("defaultWeek") == "next" and next_week.get("available"):
        week = next_week

    offers = []
    for category in week.get("categories", []):
        for offer in category.get("offers", []):
            if offer.get("cellType") != "DEFAULT":
                continue

            price_data = offer.get("priceData") or {}
            images = offer.get("images") or []
            offers.append({
                "store": "REWE",
                "title": offer.get("title", "").strip(),
                "subtitle": offer.get("subtitle", "").strip(),
                "price": parse_price(price_data.get("price")),
                "regularPrice": parse_price(price_data.get("regularPrice")),
                "category": category.get("title", ""),
                "categoryId": category.get("id", ""),
                "image": images[0] if images else "",
            })

    return {
        "validFrom": week.get("fromDate", ""),
        "validUntil": week.get("untilDate", ""),
        "offers": offers,
    }


# ------------------------------------------------------------------
# Manual Offers (any store, e.g. typed in from a Lidl/Aldi flyer)
# ------------------------------------------------------------------


def load_manual_offers(filename):
    """
    CSV with headers: store,title,price,regularPrice,subtitle
    Only store, title and price are required.
    """
    offers = []
    with open(filename, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            title = (row.get("title") or "").strip()
            if not title:
                continue
            offers.append({
                "store": (row.get("store") or "Manual").strip(),
                "title": title,
                "subtitle": (row.get("subtitle") or "").strip(),
                "price": to_float(row.get("price")),
                "regularPrice": to_float(row.get("regularPrice")),
                "category": "",
                "categoryId": "",
                "image": "",
            })
    return offers


def to_float(value):
    if value is None or not str(value).strip():
        return None
    try:
        return float(str(value).replace("€", "").replace(",", ".").strip())
    except ValueError:
        return None


# ------------------------------------------------------------------
# Ingredient Matching
# ------------------------------------------------------------------


def load_ingredients(filename):
    ingredients = set()
    with open(filename, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            for item in row.get("Ingredients", "").split(","):
                if item.strip():
                    ingredients.add(item.strip())
    return sorted(ingredients, key=str.lower)


def is_food_offer(offer):
    category = (offer.get("category", "") + " " + offer.get("categoryId", "")).lower()
    return not any(word in category for word in NON_FOOD_CATEGORY_WORDS)


def offer_matches(offer, keywords, excludes):
    text = offer["title"].lower()
    if not any(k in text for k in keywords):
        return False
    return not any(x in text for x in excludes)


def match_offers_to_ingredients(offers, ingredients):
    """
    Returns {ingredient: [offer indices]} and adds an "ingredients" list to each offer.
    """
    by_ingredient = {}
    for offer in offers:
        offer["ingredients"] = []

    for ingredient in ingredients:
        rule = INGREDIENT_KEYWORDS.get(ingredient.lower())
        if not rule:
            continue
        keywords, excludes = rule

        for index, offer in enumerate(offers):
            if is_food_offer(offer) and offer_matches(offer, keywords, excludes):
                by_ingredient.setdefault(ingredient, []).append(index)
                offer["ingredients"].append(ingredient)

    return by_ingredient


# ------------------------------------------------------------------
# Main
# ------------------------------------------------------------------


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Fetch current REWE offers and match them to the ingredients in Meals.csv."
    )
    parser.add_argument("--postcode", "-p", help="List REWE markets near this postcode and exit.")
    parser.add_argument("--market", "-m", help="REWE market ID (wwIdent) to fetch offers for.")
    parser.add_argument("--market-name", default="", help="Display name for the market (optional).")
    parser.add_argument("--cert", default="certificate.pem", help="REWE app client certificate (PEM).")
    parser.add_argument("--key", default="private.key", help="REWE app client private key.")
    parser.add_argument("--manual", help="CSV of extra offers (store,title,price,regularPrice,subtitle).")
    parser.add_argument("--meals", default=MEALS_FILE, help="Meals CSV used for ingredient matching.")
    parser.add_argument("--output", "-o", default=OUTPUT_FILE, help="Output JSON file.")
    return parser.parse_args()


def main():
    args = parse_arguments()

    if args.postcode:
        markets = search_markets(args.postcode)
        print(f"REWE markets near {args.postcode}:\n")
        for market in markets:
            km = market.get("distance", 0) / 1000
            print(
                f"  {market['wwIdent']:>8}  {market.get('displayName', '')}, "
                f"{market.get('street', '')}, {market.get('zipCode', '')} {market.get('city', '')}  "
                f"({km:.1f} km)"
            )
        print("\nRun again with --market <ID> to fetch that market's offers.")
        return

    if not args.market and not args.manual:
        print("Nothing to do: pass --postcode, --market and/or --manual. See --help.")
        sys.exit(1)

    result = {
        "fetchedAt": datetime.now().isoformat(timespec="seconds"),
        "market": None,
        "validFrom": "",
        "validUntil": "",
        "offers": [],
    }

    if args.market:
        if not (os.path.exists(args.cert) and os.path.exists(args.key)):
            print(
                f"Missing REWE client certificate ('{args.cert}' / '{args.key}').\n"
                "See README section 'REWE Discounts' for how to get them."
            )
            sys.exit(1)

        print(f"Fetching offers for REWE market {args.market}...")
        rewe = fetch_rewe_offers(args.market, args.cert, args.key)
        result["market"] = {"id": args.market, "name": args.market_name or f"REWE {args.market}"}
        result["validFrom"] = rewe["validFrom"]
        result["validUntil"] = rewe["validUntil"]
        result["offers"].extend(rewe["offers"])
        print(f"  {len(rewe['offers'])} offers, valid until {rewe['validUntil']}")

    if args.manual:
        manual = load_manual_offers(args.manual)
        result["offers"].extend(manual)
        print(f"Loaded {len(manual)} manual offers from {args.manual}")

    ingredients = load_ingredients(args.meals)
    by_ingredient = match_offers_to_ingredients(result["offers"], ingredients)
    result["byIngredient"] = by_ingredient

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=1)

    print(f"\n{len(by_ingredient)} of your ingredients are on offer:")
    for ingredient, indices in sorted(by_ingredient.items()):
        cheapest = min(
            (result["offers"][i] for i in indices),
            key=lambda o: o["price"] if o["price"] is not None else float("inf"),
        )
        price = f"{cheapest['price']:.2f} €" if cheapest["price"] is not None else "?"
        print(f"  {ingredient:<25} {cheapest['title']} ({cheapest['store']}, {price})")

    print(f"\nSaved to {args.output}")


if __name__ == "__main__":
    main()
