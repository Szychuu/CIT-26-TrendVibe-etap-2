import pandas as pd
import re
import warnings
warnings.filterwarnings("ignore")

import json
from transformers import pipeline

MODEL_NAME = "bardsai/twitter-sentiment-pl-base"

print("Ładowanie modelu językowego (może to potrwać chwilę przy pierwszym uruchomieniu)...")
sentiment_analyzer = pipeline(
    "text-classification", 
    model=MODEL_NAME, 
    tokenizer=MODEL_NAME
)

LEGAL_KEYWORDS = [
    "sąd", "sądzie", "prawnik", "kancelari", "rzecznik praw", "rzecznika praw", 
    "pozew", "uokik", "policj", "prokuratur", "oszustwo", "oszukany", 
    "okradzion", "kradzież", "prawa konsumenta"
]

PATTERN_LEGAL = re.compile(r'\b(' + '|'.join(LEGAL_KEYWORDS) + r')', re.IGNORECASE)

def assign_risk_and_reasons(row):
    reasons = []
    urgency = row['URGENCY_SCORE']
    legal = row['legal_keywords_score']
    sent = row['sentiment_negative']

    if urgency > 0.75 or legal == 1.0:
        risk_level = "HIGH"
        if legal == 1.0:
            reasons.append("Wykryto słownictwo sugerujące kroki prawne")
        if urgency > 0.75:
            reasons.append("Bardzo wysoki wskaźnik ogólnej pilności (powyżej 0.75)")

    elif sent > 0.6 or urgency > 0.4:
        risk_level = "MEDIUM"
        if sent > 0.6:
            reasons.append("Wysoki poziom negatywnych emocji")
        else:
            reasons.append("Podwyższony wskaźnik pilności")

    else:
        risk_level = "LOW"
        reasons.append("Standardowe zapytanie, brak podwyższonego ryzyka")

    formatted_reasons = json.dumps(reasons, ensure_ascii=False)
    
    return pd.Series([risk_level, formatted_reasons])


def main():
    input_file = "do_weryfikacji_recznej_START.csv"
    output_file = "kolejka_priorytetowa.csv"
    
    print(f"Wczytywanie danych z pliku {input_file}...")
    try:
        df = pd.read_csv(input_file)
    except FileNotFoundError:
        print(f"Błąd: Nie znaleziono pliku {input_file}. Upewnij się, że jest w tym samym folderze.")
        return

    texts = df['CUSTOMER_MESSAGE'].fillna("").astype(str).tolist()
    
    print("Rozpoczęto analizę wiadomości. Transformery w akcji...")

    truncated_texts = [" ".join(t.split()[:150]) for t in texts]

    sentiment_results = sentiment_analyzer(
        truncated_texts, 
        batch_size=8, 
        top_k=None,
        truncation=True
    )
    
    sentiment_negative = [
        next((item['score'] for item in res if item['label'] == 'negative'), 0.0) 
        for res in sentiment_results
    ]

    legal_keywords_score = [1.0 if PATTERN_LEGAL.search(text) else 0.0 for text in texts]

    message_length_score = [min(len(t.split()) / 150.0, 1.0) for t in texts]

    df['sentiment_negative'] = sentiment_negative
    df['legal_keywords_score'] = legal_keywords_score
    df['message_length_score'] = message_length_score
    
    df['URGENCY_SCORE'] = (0.5 * df['sentiment_negative']) + (0.3 * df['legal_keywords_score']) + (0.2 * df['message_length_score'])
    df['URGENCY_SCORE'] = df['URGENCY_SCORE'].round(3)

    df[['RISK_LEVEL', 'REASONS']] = df.apply(assign_risk_and_reasons, axis=1)

    df = df.drop(columns=['sentiment_negative', 'legal_keywords_score', 'message_length_score'])

    df = df.sort_values(by='URGENCY_SCORE', ascending=False)

    df.to_csv(output_file, index=False)
    print(f"Gotowe! Wyniki posortowane i zapisane do pliku: {output_file}.")

if __name__ == "__main__":
    main()