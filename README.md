# YouTube Comment Sentiment Analyzer - Flask Template

A Flask UI template for searching YouTube videos and analyzing comment sentiment using an existing ML model.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate   # Windows

pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` and add your YouTube API key.

## Add your model

Put your trained files in `models/`:

```text
models/models.pkl
models/vectorizer.pkl
```

Default prediction flow in this app:

```python
loaded_models = joblib.load("models/models.pkl")
loaded_vectorizers = joblib.load("models/vectorizer.pkl")

model_name = "LogisticRegression_Optuna"
model = loaded_models[model_name]
vectorizer = loaded_vectorizers[model_name]

preprocessed = [" ".join(preprocessor.preprocess(text)) for text in comments]
X = vectorizer.transform(preprocessed)
preds = model.predict(X)
```

Expected labels: `positive` and `negative`, or numeric labels that map to those classes.

Configuration:

```text
MODEL_PATH=models/models.pkl
VECTORIZER_PATH=models/vectorizer.pkl
MODEL_NAME=LogisticRegression_Optuna
```

If you have your exact notebook preprocessor as a Python module, you can plug it in with:

```text
PREPROCESSOR_MODULE=your_module_path
PREPROCESSOR_ATTR=preprocessor
```

If your model is a single pipeline instead of a dictionary export, `utils/sentiment_service.py` still supports that shape too.

## Run

```bash
python app.py
```

Open:

```text
http://127.0.0.1:5000
```
