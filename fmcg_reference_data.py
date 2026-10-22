"""
Static FMCG reference data used by the seed script.

WHY HARDCODE REAL-SOUNDING PRODUCTS INSTEAD OF FULLY RANDOM DATA:
Dashboard analytics (Phase 10) are only convincing in a demo/interview if
the data looks like a real FMCG catalog — "Amul Milk" and "Parle-G
Biscuits" mean something to a reviewer; "Product 47" does not. Category
and brand groupings here are also what makes "revenue by category" and
"top products" charts meaningful later.
"""

# (name, category, brand) — 50 total across 6 realistic FMCG categories
PRODUCT_CATALOG = [
    # Beverages
    ("Frooti Mango Drink 200ml", "Beverages", "Parle Agro"),
    ("Real Fruit Juice Orange 1L", "Beverages", "Dabur"),
    ("Coca-Cola 500ml", "Beverages", "Coca-Cola"),
    ("Sprite 750ml", "Beverages", "Coca-Cola"),
    ("Bisleri Mineral Water 1L", "Beverages", "Bisleri"),
    ("Red Bull Energy Drink 250ml", "Beverages", "Red Bull"),
    ("Tropicana Mixed Fruit 1L", "Beverages", "Tropicana"),
    ("Thums Up 750ml", "Beverages", "Coca-Cola"),
    ("Tata Tea Gold 500g", "Beverages", "Tata Consumer"),
    # Snacks
    ("Lays Classic Salted 52g", "Snacks", "PepsiCo"),
    ("Kurkure Masala Munch 90g", "Snacks", "PepsiCo"),
    ("Haldiram's Bhujia Sev 200g", "Snacks", "Haldiram's"),
    ("Bingo Mad Angles 72g", "Snacks", "ITC"),
    ("Parle-G Biscuits 200g", "Snacks", "Parle"),
    ("Oreo Original Cookies 120g", "Snacks", "Mondelez"),
    ("Britannia Good Day Cashew 100g", "Snacks", "Britannia"),
    ("Cadbury Dairy Milk 55g", "Snacks", "Mondelez"),
    ("Sunfeast Dark Fantasy 100g", "Snacks", "ITC"),
    # Dairy
    ("Amul Full Cream Milk 1L", "Dairy", "Amul"),
    ("Amul Butter 500g", "Dairy", "Amul"),
    ("Mother Dairy Curd 400g", "Dairy", "Mother Dairy"),
    ("Amul Cheese Slices 200g", "Dairy", "Amul"),
    ("Nestle A+ Toned Milk 1L", "Dairy", "Nestle"),
    ("Amul Paneer 200g", "Dairy", "Amul"),
    ("Britannia Cheese Cubes 200g", "Dairy", "Britannia"),
    ("Mother Dairy Ghee 1L", "Dairy", "Mother Dairy"),
    # Personal Care
    ("Dove Beauty Soap 100g", "Personal Care", "Unilever"),
    ("Colgate MaxFresh Toothpaste 150g", "Personal Care", "Colgate-Palmolive"),
    ("Head & Shoulders Shampoo 340ml", "Personal Care", "P&G"),
    ("Nivea Body Lotion 400ml", "Personal Care", "Nivea"),
    ("Gillette Mach3 Razor", "Personal Care", "P&G"),
    ("Pantene Conditioner 340ml", "Personal Care", "P&G"),
    ("Lifebuoy Handwash 200ml", "Personal Care", "Unilever"),
    ("Patanjali Aloe Vera Gel 150g", "Personal Care", "Patanjali"),
    # Household
    ("Surf Excel Detergent Powder 1kg", "Household", "Unilever"),
    ("Vim Dishwash Bar 200g", "Household", "Unilever"),
    ("Harpic Toilet Cleaner 500ml", "Household", "Reckitt"),
    ("Lizol Floor Cleaner 975ml", "Household", "Reckitt"),
    ("Ariel Matic Detergent 1kg", "Household", "P&G"),
    ("Good Knight Mosquito Repellent", "Household", "Godrej"),
    ("Colin Glass Cleaner 500ml", "Household", "Reckitt"),
    ("Odonil Air Freshener", "Household", "Dabur"),
    # Packaged Foods
    ("Maggi 2-Minute Noodles 70g", "Packaged Foods", "Nestle"),
    ("Aashirvaad Atta 5kg", "Packaged Foods", "ITC"),
    ("Fortune Sunflower Oil 1L", "Packaged Foods", "Adani Wilmar"),
    ("Tata Salt 1kg", "Packaged Foods", "Tata Consumer"),
    ("MTR Ready to Eat Poha 180g", "Packaged Foods", "MTR"),
    ("Kissan Mixed Fruit Jam 500g", "Packaged Foods", "HUL"),
    ("Everest Garam Masala 100g", "Packaged Foods", "Everest"),
    ("Daawat Basmati Rice 1kg", "Packaged Foods", "LT Foods"),
]

assert len(PRODUCT_CATALOG) == 50, "Expected exactly 50 products in catalog"

DISTRIBUTOR_CITIES = [
    ("Bengaluru", "Karnataka"),
    ("Mumbai", "Maharashtra"),
    ("Delhi", "Delhi"),
    ("Chennai", "Tamil Nadu"),
    ("Hyderabad", "Telangana"),
    ("Pune", "Maharashtra"),
    ("Kolkata", "West Bengal"),
    ("Ahmedabad", "Gujarat"),
    ("Jaipur", "Rajasthan"),
    ("Lucknow", "Uttar Pradesh"),
]

RETAILER_TYPES = [
    "General Store", "Supermarket", "Kirana Store", "Mini Mart",
    "Provision Store", "Departmental Store",
]
