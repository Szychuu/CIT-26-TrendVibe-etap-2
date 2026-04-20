import pandas as pd
import re
import warnings
warnings.filterwarnings("ignore")

import json
from transformers import pipeline

# 1. Konfiguracja modelu do analizy sentymentu
MODEL_NAME = "bardsai/twitter-sentiment-pl-base"

print("Ładowanie modelu językowego (może to potrwać chwilę przy pierwszym uruchomieniu)...")
sentiment_analyzer = pipeline(
    "text-classification", 
    model=MODEL_NAME, 
    tokenizer=MODEL_NAME
)

# 2. Definicja słów kluczowych związanych z ryzykiem prawnym
LEGAL_KEYWORDS = [
    "sąd", "sądzie", "prawnik", "kancelari", "rzecznik praw", "rzecznika praw", 
    "pozew", "uokik", "policj", "prokuratur", "oszustwo", "oszukany", 
    "okradzion", "kradzież", "prawa konsumenta"
]

PATTERN_LEGAL = re.compile(r'\b(' + '|'.join(LEGAL_KEYWORDS) + r')', re.IGNORECASE)

def assign_risk_and_reasons(row):
    """
    Funkcja pomocnicza do określania poziomu ryzyka i budowania listy powodów.
    """
    reasons = []
    urgency = row['URGENCY_SCORE']
    legal = row['legal_keywords_score']
    sent = row['sentiment_negative']
    
    # Ustalanie poziomu HIGH
    if urgency > 0.75 or legal == 1.0:
        risk_level = "HIGH"
        if legal == 1.0:
            reasons.append("Wykryto słownictwo sugerujące kroki prawne")
        if urgency > 0.75:
            reasons.append("Bardzo wysoki wskaźnik ogólnej pilności (powyżej 0.75)")
            
    # Ustalanie poziomu MEDIUM
    elif sent > 0.6 or urgency > 0.4:
        risk_level = "MEDIUM"
        if sent > 0.6:
            reasons.append("Wysoki poziom negatywnych emocji")
        else:
            reasons.append("Podwyższony wskaźnik pilności")
            
    # Ustalanie poziomu LOW
    else:
        risk_level = "LOW"
        reasons.append("Standardowe zapytanie, brak podwyższonego ryzyka")
        
    # Zgodnie z wytycznymi zwracamy zrzuconą listę (np. ["powód 1", "powód 2"]).
    # Użycie json.dumps ładnie sformatuje nam pythonową listę na string wyglądający jak lista z cudzysłowami
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

    # KROK 1: Przygotowanie tekstów
    texts = df['CUSTOMER_MESSAGE'].fillna("").astype(str).tolist()
    
    print("Rozpoczęto analizę wiadomości. Transformery w akcji...")
    
    # KROK 2: Analiza sentymentu
    truncated_texts = [" ".join(t.split()[:150]) for t in texts]
    
    # Przenosimy top_k=None wprost do wywołania dla zachowania kompatybilności oraz dodajemy truncation=True
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
    
    # KROK 3: Szukanie słów prawnych 
    # Usunięto zbędne robienie lowercase, wzorzec posiada flagę re.IGNORECASE i obsługuje to automatycznie.
    legal_keywords_score = [1.0 if PATTERN_LEGAL.search(text) else 0.0 for text in texts]
    
    # KROK 4: Długość wiadomości
    message_length_score = [min(len(t.split()) / 150.0, 1.0) for t in texts]
    
    # KROK 5: Łączenie wyników 
    df['sentiment_negative'] = sentiment_negative
    df['legal_keywords_score'] = legal_keywords_score
    df['message_length_score'] = message_length_score
    
    df['URGENCY_SCORE'] = (0.5 * df['sentiment_negative']) + (0.3 * df['legal_keywords_score']) + (0.2 * df['message_length_score'])
    df['URGENCY_SCORE'] = df['URGENCY_SCORE'].round(3)
    
    # KROK 6: Przypisanie poziomu ryzyka i uzasadnienia
    df[['RISK_LEVEL', 'REASONS']] = df.apply(assign_risk_and_reasons, axis=1)
    
    # KROK 7: Porządki - usuwamy kolumny pomocnicze
    df = df.drop(columns=['sentiment_negative', 'legal_keywords_score', 'message_length_score'])
    
    # Sortowanie malejąco według URGENCY_SCORE
    df = df.sort_values(by='URGENCY_SCORE', ascending=False)
    
    # Zapis do pliku
    df.to_csv(output_file, index=False)
    print(f"Gotowe! Wyniki posortowane i zapisane do pliku: {output_file}.")

if __name__ == "__main__":
    main()