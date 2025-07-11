from flask import Flask, render_template, request
import pandas as pd
from datetime import date
import os

app = Flask(__name__)
OUTPUT_FILE = "campaign_output3.xlsx"

# Column schema as required
FINAL_COLUMNS = [
    "Product", "Entity", "Operation", "Campaign ID", "Ad Group ID", "Portfolio ID", "Ad ID", "Keyword ID",
    "Product Targeting ID", "Campaign Name", "Ad Group Name", "Start Date", "End Date", "Targeting Type",
    "State", "Daily Budget", "SKU", "Ad Group Default Bid", "Bid", "Keyword Text", "Native Language Keyword",
    "Native Language Locale", "Match Type", "Bidding Strategy", "Placement", "Percentage", "Product Targeting Expression"
]

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        rows = []
        campaign_name = request.form["campaign_name"]
        strategy = request.form["strategy"]
        budget = request.form["budget"]
        campaign_type = request.form["campaign_type"]
        today = date.today().strftime("%Y%m%d")

        # Placement Bid Adjustments
        placement_rows = []
        for placement, label in {
            "product_page": "Placement Product Page",
            "amazon_business": "Placement Amazon Business",
            "rest_search": "Placement Rest Of Search",
            "top_search": "Placement Top"
        }.items():
            placement_rows.append({
                "Product": "Sponsored Products", "Entity": "Bidding Adjustment", "Operation": "Create",
                "Campaign ID": campaign_name,
                "Bidding Strategy": strategy,
                "Placement": label,
                "Percentage": request.form.get(placement, 0)
            })

        adgroup_names = request.form.getlist("adgroup_names")

        for idx, adgroup in enumerate(adgroup_names):
            ag_id = f"AG{idx + 1}"
            products = request.form.getlist(f"{ag_id}_products")
            if idx == 0:
                campaign_name = campaign_name
            else:
                campaign_name = f"{campaign_name}{idx + 1}"
                    # Campaign Row
            rows.append({
                "Product": "Sponsored Products", "Entity": "Campaign", "Operation": "Create",
                "Campaign ID": campaign_name,
                "Campaign Name": campaign_name,
                "Start Date": today,
                "Targeting Type": "Auto" if campaign_type == "auto" else "Manual",

                "State": "enabled",
                "Daily Budget": budget,
                "Bidding Strategy": strategy
            })

            rows.extend(placement_rows)

            # Ad Group Row
            rows.append({
                "Product": "Sponsored Products", "Entity": "Ad Group", "Operation": "Create",
                "Campaign ID": campaign_name,
                "Ad Group ID": adgroup,
                "Ad Group Name": adgroup,
                "Ad Group Default Bid": 5,
                "State": "enabled"
            })

            # Product Ads
            for sku in products:
                if sku:
                    rows.append({
                        "Product": "Sponsored Products", "Entity": "Product Ad", "Operation": "Create",
                        "Campaign ID": campaign_name,
                        "Ad Group ID": adgroup,
                        "State": "enabled",
                        "SKU": sku
                    })

            # Auto Targeting
            if campaign_type == "auto":
                for target in ["close", "loose", "substitutes", "complements"]:
                    bid = request.form.get(f"{ag_id}_{target}_bid")
                    if target == "close" or target == "loose":
                        target = f"{target}-match"
                    if bid:
                        rows.append({
                            "Product": "Sponsored Products", "Entity": "Product targeting", "Operation": "Create",
                            "Campaign ID": campaign_name,
                            "Ad Group ID": adgroup,
                            "State": "enabled",
                            "Bid": bid,
                            "Ad Group Default Bid": 1,
                            "Product Targeting Expression": f"{target}"
                        })

            # Manual Keyword Targeting
            elif campaign_type == "manual_kw":
                k = 0
                while True:
                    kw = request.form.get(f"{ag_id}_kw_{k}")
                    if not kw:
                        break
                    match = request.form.get(f"{ag_id}_kw_match_{k}")
                    bid = request.form.get(f"{ag_id}_kw_bid_{k}")
                    if bid:
                        rows.append({
                            "Product": "Sponsored Products", "Entity": "Keyword", "Operation": "Create",
                            "Campaign ID": campaign_name,
                            "Ad Group ID": adgroup,
                            "State": "enabled",
                            "Bid": bid,
                            "Keyword Text": kw,
                            "Match Type": match,
                            "Ad Group Default Bid": 5
                        })
                    k += 1

            # Manual Product Targeting
            elif campaign_type == "manual_pt":
                for p in range(30):
                    asin = request.form.get(f"{ag_id}_pt_asin_{p}")
                    pt_type = request.form.get(f"{ag_id}_pt_type_{p}")
                    bid = request.form.get(f"{ag_id}_pt_bid_{p}")
                    if asin and bid:
                        rows.append({
                            "Product": "Sponsored Products", "Entity": "Product targeting", "Operation": "Create",
                            "Campaign ID": campaign_name,
                            "Ad Group ID": adgroup,
                            "State": "enabled",
                            "Bid": bid,
                            "Ad Group Default Bid": 1,
                            "Product Targeting Expression": f'asin="{asin}"'
                        })

        # Create DataFrame and enforce final column order
        df = pd.DataFrame(rows)
        for col in FINAL_COLUMNS:
            if col not in df.columns:
                df[col] = ""
        df = df[FINAL_COLUMNS]

        if os.path.exists(OUTPUT_FILE):
            df_existing = pd.read_excel(OUTPUT_FILE)
            df_final = pd.concat([df_existing, df], ignore_index=True)
        else:
            df_final = df

        df_final.to_excel(OUTPUT_FILE, index=False)

    return render_template("form.html")

if __name__ == "__main__":
    app.run(debug=True)
