"""
generate_sample_pdfs.py
------------------------
Generates realistic-looking synthetic cosmetics feedback PDFs for testing
and demo work without using any real customer data.

Usage:
    python scripts/generate_sample_pdfs.py

These are SYNTHETIC PDFs built from a small pool of template sentences
per category. The layout keeps the structure of a real retail feedback form,
but the content is intentionally fictional and cosmetic-only.

Naming: each output file is named with its expected category label, for
example feedback_Excellent_001.pdf. The generated order is mixed so no two
adjacent PDFs share the same category label.
"""

import os
import random
import sys
from datetime import date, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from app import settings

CATEGORIES = ["Excellent", "Good", "Need Improvements", "Poor"]

BRANDS = [
    "Luma Glow",
    "Velvet Bloom",
    "Aurora Skin",
    "Petal & Pearl",
    "Glow Atelier",
]

PRODUCTS = [
    "Glow Renewal Serum",
    "Hydra Dew Cream",
    "Radiance Lift Essence",
    "Silk Veil Moisturizer",
    "Velvet Renewal Mask",
    "Pure Dew Cleanser",
    "Soft Radiance Toner",
    "Daily Dew Lotion",
]

FIRST_NAMES = [
    "Aarav", "Vivaan", "Aditya", "Ishaan", "Kabir",
    "Ananya", "Diya", "Saanvi", "Myra", "Priya",
    "Rohan", "Neha", "Karan", "Simran", "Alina",
]

LAST_NAMES = [
    "Sharma", "Verma", "Gupta", "Iyer", "Nair",
    "Reddy", "Singh", "Mehta", "Kapoor", "Chatterjee",
    "Das", "Bose", "Joshi", "Patel", "Nanda",
]

CRITERIA = [
    "Skin texture felt smooth",
    "Product absorbed quickly",
    "Moisture level was effective",
    "Fragrance was pleasant",
    "Packaging felt premium",
    "Overall satisfaction with the product",
]

RATING_RANGE = {
    "Excellent": (5, 5),
    "Good": (4, 5),
    "Need Improvements": (2, 3),
    "Poor": (1, 2),
}

COMMENT_POOL = {
    "Excellent": [
        "The serum absorbed quickly, left my skin comfortable and glowing, and the results exceeded what I expected.",
        "I am thrilled with this product - my skin looks brighter and feels healthier within days.",
        "Fantastic results, I would recommend this to everyone I know.",
        "This exceeded every expectation I had and the texture feels lovely on my skin.",
        "My skin feels smoother and healthier than ever; I am completely delighted.",
        "Outstanding product with a light texture and beautifully visible results.",
        "I repurchased immediately because the results were so impressive.",
        "Perfect for my skin type, no irritation, and only glowing results.",
        "This is now a permanent part of my routine and I absolutely love it.",
        "The hydration boost was instant and my complexion looks radiant.",
    ],
    "Good": [
        "The product works well and keeps my skin hydrated. The fragrance is slightly strong, but overall I am happy.",
        "Overall a pleasant experience, though the packaging could be improved.",
        "I like the results so far; the product feels soft and fresh on my skin.",
        "Good value for money, my skin feels noticeably smoother.",
        "Satisfied with the results, though it took a little longer to notice a difference than expected.",
        "Works as advertised, nothing extraordinary but entirely reliable.",
        "Happy with my purchase and I would consider buying again.",
        "Decent product, the texture is nice although the scent is a bit strong.",
        "My skin feels better overall and the formula is easy to use.",
        "Positive experience with minor reservations about the bottle design.",
    ],
    "Need Improvements": [
        "The serum takes too long to absorb and leaves a sticky feeling. The product has potential but needs refinement.",
        "The results were modest; I expected more for the price.",
        "A specific issue: the pump dispenser is awkward and sometimes gets stuck.",
        "Good idea but the formula needs better consistency and more balance.",
        "The packaging feels a little flimsy and the scent could be lighter.",
        "It works, but slower than I would like and the finish feels a little heavy.",
        "The texture is a bit rich for my daily routine, which needs improvement.",
        "I like the concept, but the applicator could be more convenient.",
        "Mild results so far and I would like clearer guidance on use.",
        "The product is okay, but I would prefer a lighter feel and better fragrance.",
    ],
    "Poor": [
        "The serum caused irritation and I had to stop using it. I am very disappointed and would not recommend this product.",
        "Absolutely furious; this caused a reaction and no one responded to my concern.",
        "Waste of money, the product did nothing for my skin and made it worse.",
        "Terrible experience, I wanted a refund immediately.",
        "This broke me out badly and I will not purchase it again.",
        "Very disappointed, the product arrived damaged and support was unhelpful.",
        "I regret this purchase entirely; the formula irritated my skin.",
        "Awful smell and no visible results after weeks of use.",
        "This product caused a painful reaction and I am extremely upset.",
        "I will not buy this again and I would discourage others from trying it.",
    ],
}

RECOMMEND_BY_CATEGORY = {
    "Excellent": lambda: "Yes",
    "Good": lambda: "Yes",
    "Need Improvements": lambda: random.choice(["Yes", "No"]),
    "Poor": lambda: "No",
}


def build_category_sequence(per_category=25):
    """Builds a balanced category sequence with no repeated category next to itself."""
    remaining = {category: per_category for category in CATEGORIES}
    sequence = []

    while sum(remaining.values()) > 0:
        if sequence:
            candidates = [
                category for category, count in remaining.items()
                if count > 0 and category != sequence[-1]
            ]
        else:
            candidates = [category for category, count in remaining.items() if count > 0]

        if not candidates:
            candidates = [category for category, count in remaining.items() if count > 0]

        next_category = random.choice(candidates)
        sequence.append(next_category)
        remaining[next_category] -= 1

    return sequence


def random_date():
    start = date(2026, 1, 1)
    offset = random.randint(0, 300)
    return (start + timedelta(days=offset)).isoformat()


def wrap_text(text, width=90):
    """Splits a long sentence into lines no wider than `width` characters."""
    words = text.split()
    lines, current_line = [], ""
    for word in words:
        if len(current_line) + len(word) + 1 <= width:
            current_line = (current_line + " " + word).strip()
        else:
            lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)
    return lines


def draw_table(pdf, x, y, col_widths, rows, header=True):
    """Draws a simple table starting at (x, y) and returns the new y position."""
    row_height = 22
    total_width = sum(col_widths)

    for i, row in enumerate(rows):
        row_y = y - i * row_height
        is_header = header and i == 0
        if is_header:
            pdf.setFillColorRGB(0.85, 0.85, 0.85)
        else:
            pdf.setFillColorRGB(1, 1, 1)
        pdf.rect(x, row_y - row_height, total_width, row_height, fill=1, stroke=1)
        pdf.setFillColorRGB(0, 0, 0)

        pdf.setFont("Helvetica-Bold" if is_header else "Helvetica", 10.5)
        cx = x + 8
        for value, w in zip(row, col_widths):
            pdf.drawString(cx, row_y - row_height + 7, str(value))
            cx += w

    return y - len(rows) * row_height


def generate_one_pdf(index, category):
    criteria_low, criteria_high = RATING_RANGE[category]
    criteria_ratings = [random.randint(criteria_low, criteria_high) for _ in CRITERIA]

    comment = random.choice(COMMENT_POOL[category])
    recommend = RECOMMEND_BY_CATEGORY[category]()
    brand = random.choice(BRANDS)
    product = random.choice(PRODUCTS)
    customer_name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
    customer_id = f"COS-{index:04d}"
    visit_date = random_date()

    os.makedirs(settings.SAMPLE_PDFS_DIR, exist_ok=True)
    safe_category = category.replace(" ", "_")
    filename = os.path.join(settings.SAMPLE_PDFS_DIR, f"feedback_{safe_category}_{index:03d}.pdf")

    pdf = canvas.Canvas(filename, pagesize=A4)
    width, height = A4

    pdf.setFont("Helvetica-Bold", 20)
    pdf.drawCentredString(width / 2, height - 60, "Customer Feedback Form")

    header_rows = [
        ["Brand", brand],
        ["Product", product],
        ["Date", visit_date],
        ["Customer Name", customer_name],
        ["Customer ID", customer_id],
    ]
    x = 60
    y = height - 110
    y = draw_table(pdf, x, y, [180, 340], header_rows, header=False)

    y -= 30
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(x, y, "Product Experience Feedback")

    y -= 15
    criteria_rows = [["Feedback Criteria", "Rating"]]
    for criterion, rating in zip(CRITERIA, criteria_ratings):
        criteria_rows.append([criterion, str(rating)])
    y = draw_table(pdf, x, y, [420, 100], criteria_rows, header=True)

    y -= 30
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(x, y, "Additional Comments")
    y -= 22
    pdf.setFont("Helvetica", 11)
    for line in wrap_text(comment):
        pdf.drawString(x, y, line)
        y -= 16

    y -= 20
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(x, y, "Would you recommend this product to others?")
    y -= 22
    pdf.setFont("Helvetica", 11)
    pdf.drawString(x, y, f"Recommendation: {recommend}")

    pdf.save()
    print(f"[expected: {category}] wrote {filename}")


def main(per_category=25):
    sequence = build_category_sequence(per_category=per_category)
    for i, category in enumerate(sequence, start=1):
        generate_one_pdf(i, category)


if __name__ == "__main__":
    main()
