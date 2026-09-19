"""
main.py
-------
The Streamlit web app itself. Run it with:

    streamlit run app/main.py

Two pages:
  1. Upload & Classify - upload a feedback PDF, see the AI's verdict.
  2. Dashboard          - charts and trends over every past result.

This file just wires together every other module in app/ - it does not
contain any PDF, AI, or maths logic itself.
"""

import hashlib
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from app import settings
from app.pdf_reader import extract_text
from app.text_cleaner import extract_feedback_sections
from app.similarity_search import load_index
from app.ai_classifier import classify_feedback
from app.confidence_score import fuse_confidence
from app.database import save_record, load_records

st.set_page_config(page_title="Feedy - Feedback Classifier", layout="wide")

CATEGORY_ORDER = ["Excellent", "Good", "Need Improvements", "Poor"]
CATEGORY_COLORS = {
    "Excellent": "#2E7D32",
    "Good": "#1976D2",
    "Need Improvements": "#B58900",
    "Poor": "#C62828",
}


@st.cache_resource
def get_vector_store():
    # Cached so the FAISS index only loads from disk once per session,
    # not on every single button click.
    return load_index()


# ----------------------------------------------------------------------
# Sidebar navigation
# ----------------------------------------------------------------------
st.sidebar.title("📋 Feedy")
st.sidebar.caption("AI-powered satisfaction analysis from PDF feedback forms")
page = st.sidebar.radio("Go to", ["Upload & Classify", "Dashboard"])
analysis_state = st.session_state.setdefault(
    "analysis_state",
    {
        "status": "idle",
        "upload_signature": None,
        "uploader_key": 0,
        "file_count": 0,
        "review_count": 0,
        "processed_results": [],
        "failed_files": [],
        "category_counts": {category: 0 for category in CATEGORY_ORDER},
        "started_at": None,
        "finished_at": None,
    },
)


def render_analysis_state(state):
    """Render combined results retained across Streamlit reruns."""
    if state["status"] == "processing":
        st.info(
            f"Processing {state['file_count']} PDF(s) and "
            f"{state['review_count']} review(s)..."
        )
        return

    if state["status"] != "completed":
        return

    processed_results = state["processed_results"]
    category_counts = state["category_counts"]
    failed_files = state["failed_files"]

    if processed_results:
        overall_category = max(
            CATEGORY_ORDER, key=lambda category: category_counts[category]
        )
        st.subheader("Overall Product Classification")
        st.metric("Overall Product Band", overall_category)

    st.subheader(
        f"Analysis Summary · {state['file_count']} PDF(s) · "
        f"{state['review_count']} review(s)"
    )
    summary_col1, summary_col2, summary_col3 = st.columns(3)
    summary_col1.metric("Successful", len(processed_results))
    summary_col2.metric("Failed files", len(failed_files))
    summary_col3.metric("Processed reviews", state["review_count"])
    st.write(
        f"Started: {state['started_at']:%H:%M:%S} | "
        f"Finished: {state['finished_at']:%H:%M:%S}"
    )
    st.write("  ".join(f"{category}: {count}" for category, count in category_counts.items()))
    for failed_file, error in failed_files:
        st.warning(f"{failed_file}: {error}")

    for section_index, (
        source_file,
        feedback_text,
        result,
        neighbours,
        final_confidence,
        needs_review,
    ) in enumerate(processed_results, start=1):
        st.divider()
        st.subheader(f"Result {section_index} · {source_file}")

        with st.expander("Review", expanded=False):
            st.write(feedback_text)

        col1, col2, col3 = st.columns(3)
        col1.metric("Category", result.category)
        col2.metric("Estimated Confidence", f"{final_confidence:.0%}")
        col3.metric("Needs Human Review", "Yes" if needs_review else "No")

        st.write("**Rationale:**", result.rationale)

        if result.flagged_keywords:
            st.write("**Flagged Keywords:**", ", ".join(result.flagged_keywords))

        with st.expander("Similar Historical Feedback"):
            for neighbour in neighbours:
                st.write(f"- \"{neighbour['text']}\" → **{neighbour['label']}**")

        if result.category == "Poor" and final_confidence > settings.ALERT_THRESHOLD:
            st.error(
                f"⚠️ High Estimated Confidence Poor result ({final_confidence:.0%}) - "
                "this customer may be at risk of churn."
            )


# ----------------------------------------------------------------------
# Page 1: Upload & Classify
# ----------------------------------------------------------------------
if page == "Upload & Classify":
    st.title("Upload & Classify")
    st.write("Upload one or more customer feedback PDFs for analysis.")

    uploaded_files = st.file_uploader(
        "Choose feedback PDFs",
        type=["pdf"],
        accept_multiple_files=True,
        key=f"pdf_uploader_{analysis_state['uploader_key']}",
    )

    if uploaded_files:
        analyse_col, clear_col = st.columns([3, 1])
        with analyse_col:
            analyse_clicked = st.button("Analyse this form", type="primary")
        with clear_col:
            clear_clicked = (
                analysis_state["status"] == "completed"
                and st.button("Clear uploaded files")
            )

        if clear_clicked:
            analysis_state["upload_signature"] = None
            analysis_state["uploader_key"] += 1
            st.rerun()

        if analyse_clicked:
            upload_signature = tuple(
                (uploaded_file.name, len(uploaded_file.getvalue()), hashlib.sha256(uploaded_file.getvalue()).hexdigest())
                for uploaded_file in uploaded_files
            )
            if upload_signature == analysis_state["upload_signature"]:
                pass
            else:
                started_at = datetime.now()
                processed_results = []
                failed_files = []
                classification_cache = {}
                total_reviews = 0
                category_counts = {category: 0 for category in CATEGORY_ORDER}
                analysis_state.update(
                    status="processing",
                    upload_signature=upload_signature,
                    file_count=len(uploaded_files),
                    review_count=0,
                    processed_results=[],
                    failed_files=[],
                    category_counts=category_counts,
                    started_at=started_at,
                    finished_at=None,
                )

                with st.spinner(f"Processing {len(uploaded_files)} PDF(s)..."):
                    vector_store = None
                    for file_index, uploaded_file in enumerate(uploaded_files, start=1):
                        st.write(f"Processing {file_index}/{len(uploaded_files)}: {uploaded_file.name}")
                        try:
                            raw_text, used_ocr = extract_text(uploaded_file)
                            sections = extract_feedback_sections(raw_text)

                            if not sections:
                                raise ValueError("Could not find any readable feedback text")
                            if len(sections) == 1 and len(raw_text) > 10000:
                                raise ValueError(
                                    "This PDF is unusually large but only one review was detected"
                                )

                            if used_ocr:
                                st.info(f"OCR was used for {uploaded_file.name}.")
                            if vector_store is None:
                                with st.spinner("Loading the similarity index..."):
                                    vector_store = get_vector_store()

                            extraction_quality = (
                                settings.OCR_EXTRACTION_QUALITY if used_ocr
                                else settings.DIGITAL_EXTRACTION_QUALITY
                            )
                            total_reviews += len(sections)
                            analysis_state["review_count"] = total_reviews

                            unique_feedback = list(dict.fromkeys(section.strip() for section in sections))
                            with ThreadPoolExecutor(max_workers=4) as executor:
                                pending = {
                                    executor.submit(classify_feedback, vector_store, feedback_text): feedback_text
                                    for feedback_text in unique_feedback
                                    if feedback_text not in classification_cache
                                }
                                for future in as_completed(pending):
                                    feedback_text = pending[future]
                                    try:
                                        classification_cache[feedback_text] = future.result()
                                    except Exception as error:
                                        classification_cache[feedback_text] = error

                            for feedback_text in sections:
                                try:
                                    cached_result = classification_cache[feedback_text.strip()]
                                    if isinstance(cached_result, Exception):
                                        raise cached_result
                                    result, neighbours, agreement = cached_result
                                    final_confidence = fuse_confidence(
                                        result.confidence, agreement, extraction_quality
                                    )
                                    needs_review = final_confidence < settings.REVIEW_THRESHOLD

                                    save_record(
                                        source_file=uploaded_file.name,
                                        feedback_text=feedback_text,
                                        category=result.category,
                                        llm_confidence=result.confidence,
                                        neighbour_agreement=agreement,
                                        final_confidence=final_confidence,
                                        rationale=result.rationale,
                                        flagged_keywords=result.flagged_keywords,
                                    )
                                    processed_results.append(
                                        (
                                            uploaded_file.name,
                                            feedback_text,
                                            result,
                                            neighbours,
                                            final_confidence,
                                            needs_review,
                                        )
                                    )
                                    category_counts[result.category] += 1
                                except Exception as error:
                                    failed_files.append((uploaded_file.name, str(error)))
                        except Exception as error:
                            failed_files.append((uploaded_file.name, str(error)))

                finished_at = datetime.now()
                analysis_state.update(
                    status="completed",
                    review_count=total_reviews,
                    processed_results=processed_results,
                    failed_files=failed_files,
                    category_counts=category_counts,
                    finished_at=finished_at,
                )

    if analysis_state["status"] in {"processing", "completed"}:
        render_analysis_state(analysis_state)


# ----------------------------------------------------------------------
# Page 2: Dashboard
# ----------------------------------------------------------------------
else:
    st.title("Dashboard")

    records = load_records()

    if records.empty:
        st.info("No classified feedback yet. Go to 'Upload & Classify' to analyse your first PDF.")
    else:
        records["timestamp"] = pd.to_datetime(records["timestamp"])

        # --- Sidebar filters ---
        st.sidebar.divider()
        st.sidebar.subheader("Filters")
        selected_categories = st.sidebar.multiselect(
            "Category", CATEGORY_ORDER, default=CATEGORY_ORDER
        )
        review_filter = st.sidebar.selectbox(
            "Review status", ["All", "Needs review", "No review needed"]
        )

        filtered = records[records["category"].isin(selected_categories)]
        if review_filter == "Needs review":
            filtered = filtered[filtered["needs_review"] == True]  # noqa: E712
        elif review_filter == "No review needed":
            filtered = filtered[filtered["needs_review"] == False]  # noqa: E712

        # --- KPI metrics ---
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total responses", len(filtered))
        col2.metric(
            "Average Estimated Confidence",
            f"{filtered['final_confidence'].mean():.0%}" if len(filtered) else "N/A",
        )
        col3.metric("Needs review", int(filtered["needs_review"].sum()))
        col4.metric("Poor", int((filtered["category"] == "Poor").sum()))

        st.divider()

        # --- Charts ---
        chart_col1, chart_col2 = st.columns(2)

        with chart_col1:
            category_counts = (
                filtered["category"].value_counts().reindex(CATEGORY_ORDER).fillna(0)
            )
            bar_fig = go.Figure(
                go.Bar(
                    x=category_counts.index,
                    y=category_counts.values,
                    marker_color=[CATEGORY_COLORS[c] for c in category_counts.index],
                )
            )
            bar_fig.update_layout(title="Responses by category")
            st.plotly_chart(bar_fig, use_container_width=True)

        with chart_col2:
            donut_fig = go.Figure(
                go.Pie(
                    labels=category_counts.index,
                    values=category_counts.values,
                    hole=0.5,
                    marker_colors=[CATEGORY_COLORS[c] for c in category_counts.index],
                )
            )
            donut_fig.update_layout(title="Category distribution")
            st.plotly_chart(donut_fig, use_container_width=True)

        chart_col3, chart_col4 = st.columns(2)

        with chart_col3:
            daily = filtered.copy()
            daily["date"] = daily["timestamp"].dt.date
            trend = daily.groupby("date").size().reset_index(name="count")
            trend_fig = px.line(trend, x="date", y="count", markers=True, title="Daily volume")
            st.plotly_chart(trend_fig, use_container_width=True)

        with chart_col4:
            hist_fig = px.histogram(
                filtered, x="final_confidence", nbins=10, title="Estimated Confidence distribution"
            )
            st.plotly_chart(hist_fig, use_container_width=True)

        st.divider()

        # --- Records table ---
        st.subheader("All records")
        st.dataframe(filtered.sort_values("timestamp", ascending=False), use_container_width=True)

        # --- High estimated-confidence Poor alerts ---
        alerts = filtered[
            (filtered["category"] == "Poor") & (filtered["final_confidence"] > settings.ALERT_THRESHOLD)
        ]
        if len(alerts):
            st.subheader("⚠️ High Estimated Confidence Poor alerts")
            st.dataframe(alerts, use_container_width=True)
