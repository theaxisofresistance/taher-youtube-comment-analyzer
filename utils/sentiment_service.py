import importlib
import os
import re
from functools import lru_cache

import joblib

LABEL_MAP = {
    0: "negative",
    "0": "negative",
    1: "positive",
    2: "positive",
    "1": "positive",
    "2": "positive",
    "neg": "negative",
    "pos": "positive",
    "negative": "negative",
    "positive": "positive",
}


class DefaultPreprocessor:
    def preprocess(self, text: str):
        cleaned = re.sub(r"https?://\S+|www\.\S+", " ", text.lower())
        cleaned = re.sub(r"[^a-z0-9\s']", " ", cleaned)
        return [token for token in cleaned.split() if token]

    def get_sentiment(self, label):
        return normalize_label(label)


def _resolve_model_asset(assets, selected_name):
    if isinstance(assets, dict):
        if selected_name in assets:
            return assets[selected_name], selected_name
        first_name = next(iter(assets), None)
        if first_name is None:
            return None, selected_name
        return assets[first_name], first_name
    return assets, selected_name


def get_default_model_name():
    return os.getenv("MODEL_NAME", "LogisticRegression_Optuna")


@lru_cache(maxsize=1)
def load_preprocessor():
    module_name = os.getenv("PREPROCESSOR_MODULE")
    attr_name = os.getenv("PREPROCESSOR_ATTR", "preprocessor")

    if module_name:
        module = importlib.import_module(module_name)
        preprocessor = getattr(module, attr_name)
        if callable(preprocessor) and not hasattr(preprocessor, "preprocess"):
            preprocessor = preprocessor()
        return preprocessor

    return DefaultPreprocessor()


@lru_cache(maxsize=1)
def load_model_bundles():
    model_path = os.getenv("MODEL_PATH", "models/models.pkl")
    vectorizer_path = os.getenv("VECTORIZER_PATH", "models/vectorizer.pkl")

    if not os.path.exists(model_path):
        return None, None

    loaded_models = joblib.load(model_path)
    loaded_vectorizers = (
        joblib.load(vectorizer_path)
        if vectorizer_path and os.path.exists(vectorizer_path)
        else None
    )

    return loaded_models, loaded_vectorizers


def get_available_model_names():
    loaded_models, _ = load_model_bundles()

    if isinstance(loaded_models, dict):
        return list(loaded_models.keys())
    if loaded_models is not None:
        return [get_default_model_name()]
    return []


def resolve_model_name(selected_name=None):
    available_models = get_available_model_names()
    default_name = get_default_model_name()

    if selected_name and selected_name in available_models:
        return selected_name
    if default_name in available_models:
        return default_name
    if available_models:
        return available_models[0]
    return selected_name or default_name


def load_model_assets(selected_name=None):
    loaded_models, loaded_vectorizers = load_model_bundles()
    active_name = resolve_model_name(selected_name)

    if loaded_models is None:
        return None, None, active_name

    model, active_name = _resolve_model_asset(loaded_models, active_name)
    vectorizer, _ = _resolve_model_asset(loaded_vectorizers, active_name)

    return model, vectorizer, active_name


def normalize_label(label):
    return LABEL_MAP.get(label, LABEL_MAP.get(str(label).lower(), "negative"))


def fallback_rule_based_sentiment(text: str):
    """Temporary fallback so the UI works before you add your real model."""
    positive_words = {"good", "great", "amazing", "love", "best", "nice", "awesome", "keren", "bagus", "mantap", "suka"}
    negative_words = {"bad", "worst", "hate", "boring", "awful", "jelek", "buruk", "benci", "parah"}

    tokens = set(text.lower().split())
    pos_score = len(tokens & positive_words)
    neg_score = len(tokens & negative_words)

    if pos_score > neg_score:
        return "positive"
    return "negative"


def preprocess_texts(texts):
    preprocessor = load_preprocessor()
    processed = []

    for text in texts:
        if hasattr(preprocessor, "preprocess"):
            tokens = preprocessor.preprocess(text)
            if isinstance(tokens, str):
                processed.append(tokens)
            else:
                processed.append(" ".join(tokens))
        else:
            processed.append(text)

    return processed


def get_active_model_name(selected_name=None):
    _, _, model_name = load_model_assets(selected_name)
    return model_name


def predict_labels(texts, model_name=None):
    model, vectorizer, _ = load_model_assets(model_name)

    if model is None:
        return [fallback_rule_based_sentiment(text) for text in texts]

    prepared_texts = preprocess_texts(texts)

    if vectorizer is not None:
        features = vectorizer.transform(prepared_texts)
        predictions = model.predict(features)
    else:
        # For sklearn Pipeline or custom model that accepts raw text directly.
        predictions = model.predict(prepared_texts)

    preprocessor = load_preprocessor()
    if hasattr(preprocessor, "get_sentiment"):
        return [preprocessor.get_sentiment(pred) for pred in predictions]
    return [normalize_label(pred) for pred in predictions]


def predict_sentiment(text: str, model_name=None):
    return predict_labels([text], model_name=model_name)[0]


def analyze_sentiments(comments, model_name=None):
    texts = [comment["text"] for comment in comments]
    labels = predict_labels(texts, model_name=model_name)

    summary = {
        "positive": 0,
        "negative": 0,
        "total": len(comments),
    }

    results = []
    for comment, label in zip(comments, labels):
        summary[label] += 1
        results.append({**comment, "sentiment": label})

    return results, summary
