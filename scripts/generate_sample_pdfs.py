"""
generate_sample_pdfs.py
------------------------
Generates realistic-looking synthetic feedback PDFs, useful for testing
the pipeline end-to-end when you don't have real customer PDFs yet.

Usage:
    python scripts/generate_sample_pdfs.py

These are SYNTHETIC PDFs built from a small pool of template sentences
per category - great for proving the pipeline works, but they should
never be presented as real-world accuracy evidence.
"""

import sys
import os
import random

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from app import settings

FEEDBACK_POOL = {
    "Excellent": [
        "The serum absorbed quickly, left my skin comfortable and glowing, and the results exceeded what I expected.",
        "I am thrilled with this product - my skin looks brighter and feels healthier within days.",
        "Fantastic results, I would recommend this to everyone I know.",
        "This exceeded every expectation I had, truly excellent quality.",
        "My skin has never felt this good, I am absolutely delighted.",
        "Outstanding product, fast results, and a lovely texture on the skin.",
        "I repurchased immediately because the results were so impressive.",
        "Perfect for my skin type, no irritation, only glowing results.",
        "This is now a permanent part of my routine - amazing product.",
        "Everyone has commented on how great my skin looks since I started using this.",
        "Five stars without hesitation, this product works wonders.",
        "I was skeptical at first but now I am a loyal customer for life.",
        "The improvement in my skin texture was noticeable within a week.",
        "Incredible value for the quality - highly recommended.",
        "This is the best skincare purchase I have made in years.",
    ],
    "Good": [
        "The serum works well and keeps my skin hydrated. The fragrance is slightly strong, but overall I am happy.",
        "Overall a pleasant experience, though the packaging could be improved.",
        "I like the results so far, a solid product with minor room to grow.",
        "Good value for money, my skin feels noticeably softer.",
        "Satisfied with the results, though it took a little longer to notice a difference than expected.",
        "Works as advertised, nothing extraordinary but reliable.",
        "Happy with my purchase, would consider buying again.",
        "Decent product, the texture is nice even if the scent is a bit much.",
        "My skin feels better overall, a good addition to my routine.",
        "Positive experience, minor reservations about the price point.",
        "Good quality product, does what it says on the label.",
        "I would recommend this with a small caveat about the packaging.",
        "Pleasantly surprised by the results, mostly satisfied.",
        "Solid product overall, a few small things could be better.",
        "Would buy again, generally satisfied with the outcome.",
    ],
    "Need Improvements": [
        "The serum takes too long to absorb and leaves a sticky feeling. The product has potential, but the application needs improvement.",
        "The results were modest, I expected more given the price.",
        "A specific issue: the pump dispenser often gets stuck.",
        "Good idea but the execution needs some refinement, especially the scent.",
        "The packaging leaks slightly, otherwise the product is fine.",
        "It works, but slower than I would like for the price I paid.",
        "The texture is a bit heavy, could be lighter for daily use.",
        "Needs a better applicator, the rest of the product is acceptable.",
        "Mild results so far, would like to see clearer instructions.",
        "The bottle design makes it hard to get the last bit of product out.",
        "Reasonable product but the fragrance needs to be toned down.",
        "The formula is fine, but delivery took longer than expected.",
        "Some improvement needed in consistency between batches.",
        "It's an okay product, but the value for money could be better.",
        "Works fine but I wish the ingredients list was clearer on the box.",
    ],
    "Poor": [
        "The serum caused irritation and I had to stop using it. I am very disappointed and would not recommend this product.",
        "Absolutely furious, this caused a reaction and no one responded to my complaint.",
        "Waste of money, the product did nothing for my skin.",
        "Terrible experience, I want a refund immediately.",
        "This broke me out badly, I will not be purchasing again.",
        "Very disappointed, the product arrived damaged and support was unhelpful.",
        "I regret this purchase entirely, it made my skin worse.",
        "Awful smell and no visible results after weeks of use.",
        "Customer service ignored my complaint for over a week, unacceptable.",
        "This product caused a painful reaction, extremely upset about this.",
        "Do not buy this, it is not worth the money or the risk.",
        "I am switching brands after this frustrating experience.",
        "The product leaked all over my bag and ruined other items.",
        "Completely dissatisfied, this does not work as advertised at all.",
        "I want to stop using this brand altogether after this experience.",
    ],
}

CATEGORIES = ["Excellent", "Good", "Need Improvements", "Poor"]


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


def generate_one_pdf(index, category):
    feedback = random.choice(FEEDBACK_POOL[category])

    if category == "Excellent":
        rating, recommend = "5", "Yes"
    elif category == "Good":
        rating, recommend = "4", "Yes"
    elif category == "Need Improvements":
        rating, recommend = "3", random.choice(["Yes", "No"])
    else:
        rating, recommend = random.choice(["1", "2"]), "No"

    os.makedirs(settings.SAMPLE_PDFS_DIR, exist_ok=True)
    filename = os.path.join(settings.SAMPLE_PDFS_DIR, f"feedback_{index:03d}.pdf")

    pdf = canvas.Canvas(filename, pagesize=A4)
    width, height = A4

    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(60, height - 70, "Customer Feedback Form")

    pdf.setFont("Helvetica", 11)
    y = height - 110
    pdf.drawString(60, y, "Product: Glow Renewal Face Serum")
    y -= 20
    pdf.drawString(60, y, f"Overall Rating: {rating} / 5")
    y -= 20
    pdf.drawString(60, y, f"Would you recommend this product to others? {recommend}")
    y -= 30
    pdf.drawString(60, y, "Additional Comments:")
    y -= 20

    for line in wrap_text(feedback):
        pdf.drawString(70, y, line)
        y -= 16

    pdf.save()
    print(f"[expected: {category}] wrote {filename}")


def main():
    for i in range(1, 401):
        category = CATEGORIES[(i - 1) % len(CATEGORIES)]
        generate_one_pdf(i, category)


if __name__ == "__main__":
    main()
