"""
text_cleaner.py
----------------
The raw text pulled out of a PDF is messy - it has the form title, the
customer's name, the date, rating labels, and so on. This file strips
all of that out and keeps only the meaningful content the AI should
actually read.

It understands two shapes of form:
  1. A simple form with one "Feedback:" block.
  2. A structured rating form with several labelled questions
     (overall rating, criteria, recommendation, comments, etc).
"""

import re

METADATA_LABELS = {
    "customer name", "name", "date", "email", "phone", "order id",
    "reference number", "form title", "customer feedback form",
    "product", "category",
}

STRUCTURED_FORM_MARKERS = {
    "feedback criteria", "additional comments", "overall rating",
    "would you recommend this product to others?",
}

STRUCTURED_FORM_HEADINGS = {
    "cosmetics product feedback form", "customer feedback form",
    "customer information", "product feedback", "feedback criteria",
    "rating", "additional comments",
}

STRUCTURED_FORM_METADATA = {
    "brand", "product", "category", "date", "customer name", "contact number",
}

REVIEW_BOUNDARY_PATTERNS = (
    re.compile(r"^\s*review\s+id\s*[:#-]?\s*[A-Z0-9]+(?:-[A-Z0-9]+)*\s*$", re.IGNORECASE),
    re.compile(r"^\s*(?:customer\s+)?review\s+(?:#|no\.?|number)?\s*[A-Z0-9]+(?:-[A-Z0-9]+)*\s*:?.*$", re.IGNORECASE),
    re.compile(r"^\s*(?:feedback|response|record|entry)\s+(?:#|no\.?|number)?\s*\d+\s*:?.*$", re.IGNORECASE),
    re.compile(r"^\s*customer\s+feedback\s+form\b.*\brecord\s+\d+\s*$", re.IGNORECASE),
    re.compile(r"^\s*card\s*#\s*\d+\s*:?.*$", re.IGNORECASE),
)
REVIEW_SECTION_HEADER_PATTERN = re.compile(r"^\s*reviews?\s*:?\s*$", re.IGNORECASE)
PAGE_HEADER_PATTERN = re.compile(r"^\s*page\s+\d+\s*$", re.IGNORECASE)
CUSTOMER_ID_PATTERN = re.compile(r"^\s*CUST-\d+\b", re.IGNORECASE)


def clean_single_comment(raw_text):
    """
    Simple-form behaviour: capture everything after a 'Feedback:' label.
    Kept as a fallback for basic forms and as a last resort elsewhere.
    """
    lines = raw_text.split("\n")
    feedback_lines = []
    capturing = False

    for line in lines:
        stripped_line = line.strip()
        if stripped_line == "":
            continue
        if stripped_line.lower().startswith("feedback:"):
            capturing = True
            remainder = stripped_line.split(":", 1)[1].strip()
            if remainder:
                feedback_lines.append(remainder)
            continue
        if capturing:
            feedback_lines.append(stripped_line)

    if len(feedback_lines) == 0:
        feedback_lines = [line.strip() for line in lines if line.strip() != ""]

    cleaned_text = " ".join(feedback_lines)
    cleaned_text = re.sub(r"\s+", " ", cleaned_text)
    return cleaned_text.strip()


def extract_feedback_sections(raw_text):
    """
    Handles forms with several labelled questions/ratings. Detects a full
    structured rating form first; otherwise walks line by line, treating
    any short 'Label:' line as a new section and skipping known metadata
    labels. Falls back to clean_single_comment() if nothing usable was found.
    """
    multiple_reviews = _extract_multiple_reviews(raw_text)
    if multiple_reviews:
        return multiple_reviews

    table_reviews = _extract_repeated_feedback_rows(raw_text)
    if table_reviews:
        return table_reviews

    customer_records = _extract_customer_records(raw_text)
    if customer_records:
        return customer_records

    repeated_forms = _extract_repeated_forms(raw_text)
    if repeated_forms:
        return repeated_forms

    if _looks_like_structured_form(raw_text):
        combined_feedback = _combine_structured_form(raw_text)
        return [combined_feedback] if combined_feedback else []

    combined_feedback = _combine_structured_form(raw_text)
    if combined_feedback:
        return [combined_feedback]

    single_comment = clean_single_comment(raw_text)
    return [single_comment] if single_comment else []


def _extract_multiple_reviews(raw_text):
    """Splits a document when it contains recognizable review boundaries."""
    lines = raw_text.split("\n")
    starts = []
    for index, line in enumerate(lines):
        match = _review_boundary_match(line)
        if match:
            identifier = _normalise_identifier(match.group(0))
            if not starts or identifier != starts[-1][1]:
                starts.append((index, identifier))

    if len(starts) >= 2:
        sections = []
        for start_position, (start_index, _) in enumerate(starts):
            end_index = starts[start_position + 1][0] if start_position + 1 < len(starts) else len(lines)
            review_text = "\n".join(line.strip() for line in lines[start_index:end_index] if line.strip())
            if review_text:
                sections.append(_combine_structured_form(review_text))
        return sections
    return []


def _review_boundary_match(line):
    stripped_line = line.strip()
    return next(
        (pattern.match(stripped_line) for pattern in REVIEW_BOUNDARY_PATTERNS if pattern.match(stripped_line)),
        None,
    )


def _normalise_identifier(boundary_line):
    return re.sub(r"\s+", " ", boundary_line.strip().lower())


def _extract_repeated_feedback_rows(raw_text):
    """Extracts feedback from repeated ID/respondent/rating table rows."""
    reviews = []
    for page in raw_text.split("\f"):
        lines = [line.strip() for line in page.split("\n") if line.strip()]
        index = 0
        while index + 4 < len(lines):
            if (
                re.fullmatch(r"\d+", lines[index])
                and re.fullmatch(r"respondent\s+\d+", lines[index + 1], re.IGNORECASE)
                and re.fullmatch(r"\d+(?:\.\d+)?", lines[index + 2])
                and lines[index + 3].lower() in {"yes", "no"}
            ):
                feedback = lines[index + 4]
                if _looks_like_review_text(feedback):
                    reviews.append(feedback)
                index += 5
                continue
            index += 1

    return reviews if len(reviews) >= 2 else []


def _extract_customer_records(raw_text):
    """Extracts explicit customer-ID records from row and vertical-table layouts."""
    lines = [line.strip() for line in raw_text.split("\n") if line.strip()]
    starts = [index for index, line in enumerate(lines) if CUSTOMER_ID_PATTERN.match(line)]
    if len(starts) < 2:
        return []

    records = []
    for position, start_index in enumerate(starts):
        end_index = starts[position + 1] if position + 1 < len(starts) else len(lines)
        record_lines = [
            line for line in lines[start_index:end_index]
            if not PAGE_HEADER_PATTERN.match(line)
            and not line.lower().startswith(("feedy_", "customer_id"))
        ]
        if record_lines:
            records.append(re.sub(r"\s+", " ", " ".join(record_lines)).strip())
    return records


def _extract_repeated_forms(raw_text):
    """Splits repeated forms only when repeated record fields corroborate them."""
    lines = raw_text.split("\n")
    heading_indexes = [
        index for index, line in enumerate(lines)
        if _looks_like_form_heading(line)
    ]
    if len(heading_indexes) < 2:
        return []

    field_occurrences = sum(
        1 for line in lines
        if re.match(r"^\s*(?:customer\s+name|customer|respondent|member|user)\s*:", line, re.IGNORECASE)
    )
    if field_occurrences < 2:
        return []

    sections = []
    for position, start_index in enumerate(heading_indexes):
        end_index = heading_indexes[position + 1] if position + 1 < len(heading_indexes) else len(lines)
        section = "\n".join(line.strip() for line in lines[start_index:end_index] if line.strip())
        if section:
            sections.append(_combine_structured_form(section))
    return sections if len(sections) >= 2 else []


def _looks_like_form_heading(line):
    lowered_line = line.strip().lower()
    return (
        "feedback form" in lowered_line
        or "comment card" in lowered_line
        or "member feedback log" in lowered_line
    )


def _extract_page_reviews(raw_text):
    """Uses preserved PDF page and paragraph boundaries as a generic fallback."""
    if "\f" not in raw_text:
        return []

    reviews = []
    for page in raw_text.split("\f"):
        paragraphs = [paragraph.strip() for paragraph in re.split(r"\n\s*\n", page) if paragraph.strip()]
        prose_paragraphs = [paragraph for paragraph in paragraphs if _looks_like_review_text(paragraph)]
        if len(prose_paragraphs) == 1:
            reviews.append(clean_single_comment(prose_paragraphs[0]))

    return reviews if len(reviews) >= 2 else []


def _find_repeated_headers(lines):
    """Finds repeated short document headers without knowing the PDF title."""
    counts = {}
    for line in lines:
        stripped_line = line.strip()
        if stripped_line:
            counts[stripped_line] = counts.get(stripped_line, 0) + 1

    return {
        line for line, count in counts.items()
        if (
            len(line) < 100
            and not _looks_like_review_text(line)
            and (count > 1 or _looks_like_document_header(line))
        )
    }


def _extract_record_comment(raw_text):
    """Keeps only the comment from one structured feedback record."""
    lines = raw_text.split("\n")
    comment_start = next(
        (index for index, line in enumerate(lines)
         if line.strip().lower().startswith("additional comments")),
        None,
    )
    if comment_start is None:
        return ""

    comment_lines = []
    for line in lines[comment_start + 1:]:
        stripped_line = line.strip()
        lowered_line = stripped_line.lower()
        if lowered_line.startswith("would you recommend") or lowered_line.startswith("recommendation:"):
            break
        if stripped_line:
            comment_lines.append(stripped_line)

    return re.sub(r"\s+", " ", " ".join(comment_lines)).strip()


def _looks_like_review_text(line):
    """Keeps repeated complete sentences from being mistaken for headers."""
    return len(line.split()) >= 8 or line.endswith((".", "!", "?"))


def _looks_like_document_header(line):
    """Recognizes short title lines without depending on a filename."""
    lowered_line = line.lower()
    return any(word in lowered_line.split() for word in {"page", "feedback", "export", "report"})


def _looks_like_structured_form(raw_text):
    """Detect forms that contain several labelled rating and answer fields."""
    lowered_text = raw_text.lower()
    marker_count = sum(marker in lowered_text for marker in STRUCTURED_FORM_MARKERS)
    return marker_count >= 2


def _combine_structured_form(raw_text):
    """Keep one form's useful answers together for one overall classification."""
    lines = [
        line.strip() for line in raw_text.split("\n")
        if line.strip() and not PAGE_HEADER_PATTERN.match(line.strip())
    ]
    combined_lines = []
    skip_next_value = False

    for line in lines:
        lowered_line = line.lower().rstrip(":")
        label, separator, value = line.partition(":")
        lowered_label = label.strip().lower()

        if lowered_line in STRUCTURED_FORM_HEADINGS or _looks_like_form_heading(line):
            continue
        if separator and lowered_label in STRUCTURED_FORM_METADATA:
            continue
        if lowered_line in STRUCTURED_FORM_METADATA:
            skip_next_value = True
            continue
        if skip_next_value:
            skip_next_value = False
            continue
        if lowered_line in {"feedback criteria", "feedback criterion", "rating"}:
            continue

        combined_lines.append(line)

    combined_text = " ".join(combined_lines)
    combined_text = re.sub(r"\s+", " ", combined_text).strip()
    return combined_text


def _line_as_label(stripped_line):
    """
    Returns the lower-cased label text if this line looks like "Something:"
    - short, ends in a colon fairly early in the line.
    """
    colon_index = stripped_line.find(":")
    if colon_index == -1:
        return None
    if colon_index > 40:
        return None
    return stripped_line[:colon_index].strip().lower()
