"""
ai_classifier.py
-----------------
The actual "ask the AI to classify this" logic. Builds the instructions
(system prompt), builds the message (retrieved examples + new feedback),
sends it to the local Ollama model, and parses the structured reply.
"""

from functools import lru_cache

from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

from app import settings
from app.schemas import FeedbackClassification
from app.similarity_search import find_similar_examples

SYSTEM_PROMPT = """You are a customer satisfaction analyst. You will read one piece of
customer feedback and assign it to exactly one of four categories.

- "Excellent": strong satisfaction, delight, loyalty, or advocacy; enthusiastic and
  affirming feedback.

- "Good": the customer is clearly satisfied overall. Minor reservations may exist,
  but the overall feedback remains clearly positive.

- "Need Improvements": the customer identifies specific or meaningful problems that
  should be addressed. The feedback may be mixed or moderately negative, but there is
  no strong frustration, disappointment, or clear churn intent.

- "Poor": strong dissatisfaction, frustration, disappointment, serious problems, or
  clear negative experience or churn intent.

Rules:
- Judge the complete customer context: written comments, ratings, overall rating,
  and recommendation answer together.
- Resolve conflicting signals contextually. Do not calculate a numeric average of
  ratings to decide the category.
- Do not let one rating, one keyword, or one field decide the category.
- Judge the customer's overall experience and intent, not individual keywords.
- Do not classify feedback as Good simply because it is polite or contains one
  positive statement.
- When specific problems are identified and the overall feedback is mixed or
  moderately negative, consider Need Improvements.
- Use Poor when the negative experience is strong, serious, disappointing, or shows
  clear churn intent.
- Base the rationale only on what the customer actually wrote or explicitly stated
  in the feedback. Do not invent details.
- Give your own honest confidence from 0.0 to 1.0 for how sure you are of this category.
- Use lower confidence when the feedback contains conflicting or ambiguous signals.
- Return exactly these four fields:
  category, confidence, rationale, flagged_keywords.
- Return flagged_keywords as meaningful evidence phrases copied from the customer's
  actual answers, comments, or recommendation response.
- Do not return question text, field labels, product names, dates, or generic form
  metadata as flagged keywords.
- Flagged keywords are explanatory evidence only and must never be used as a
  classification rule.
"""


@lru_cache(maxsize=1)
def build_classifier_chain():
    """Builds the LangChain pipeline: prompt -> chat model -> parser."""
    chat_model = ChatOllama(
        model=settings.OLLAMA_MODEL,
        base_url=settings.OLLAMA_BASE_URL,
        temperature=0,  # low randomness so the same feedback tends to get judged the same way
        num_predict=settings.OLLAMA_NUM_PREDICT,
    )

    parser = PydanticOutputParser(pydantic_object=FeedbackClassification)

    prompt = ChatPromptTemplate.from_messages([
        ("system", "{system_prompt}\n\nRespond in exactly this format:\n{format_instructions}"),
        ("human", "{user_message}"),
    ]).partial(
        system_prompt=SYSTEM_PROMPT,
        format_instructions=parser.get_format_instructions(),
    )

    chain = prompt | chat_model | parser
    return chain


def build_user_message(feedback_text, neighbours):
    """Puts the retrieved labelled examples in front of the new feedback."""
    lines = []
    if neighbours:
        lines.append("Here are examples of feedback this team has already labelled:")
        for neighbour in neighbours:
            lines.append(f'- "{neighbour["text"]}" -> {neighbour["label"]}')
        lines.append("")
    lines.append("Now classify this new piece of feedback:")
    lines.append(f'"{feedback_text}"')
    return "\n".join(lines)


def calculate_neighbour_agreement(predicted_category, neighbours):
    """Fraction of the retrieved examples sharing the predicted category (0.0-1.0)."""
    if not neighbours:
        return 0.5

    matching_count = 0
    for neighbour in neighbours:
        if neighbour["label"] == predicted_category:
            matching_count = matching_count + 1

    return round(matching_count / len(neighbours), 2)


def classify_feedback(vector_store, feedback_text):
    """
    Full classification for one piece of feedback text.
    Returns (classification_result, retrieved_neighbours, neighbour_agreement).
    """
    neighbours = find_similar_examples(vector_store, feedback_text)
    user_message = build_user_message(feedback_text, neighbours)

    chain = build_classifier_chain()
    result = chain.invoke({"user_message": user_message})

    agreement = calculate_neighbour_agreement(result.category, neighbours)
    return result, neighbours, agreement
