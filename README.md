# TrendVibe - System Priorytetyzacji Zgłoszeń BOK ("Sprytne Zwroty AI" v2)

System automatyzuje ocenę pilności zgłoszeń (URGENCY_SCORE) oraz określa kategoryczny poziom ryzyka (RISK_LEVEL) na podstawie analizy wiadomości od klientów. Rozwiązanie działa całkowicie lokalnie, wykorzystując modele open-source.

## 🚀 Instrukcja uruchomienia skryptu

1. **Wymagania wstępne:** **Python:** wersja 3.11.x lub 3.12.x (64-bit).
2. **Przygotowanie środowiska:** Otwórz terminal (lub wiersz poleceń) w folderze z projektem i zainstaluj niezbędne biblioteki za pomocą polecenia:
   `pip install -r requirements.txt`
3. **Plik z danymi:** Upewnij się, że w tym samym folderze co skrypt `main.py` znajduje się plik z danymi wejściowymi o nazwie `do_weryfikacji_recznej_START.csv`.
4. **Uruchomienie:** Wpisz w terminalu:
   `python main.py`
5. **Wynik:** Po zakończeniu działania programu (przy pierwszym uruchomieniu może to potrwać chwilę ze względu na pobieranie modelu z sieci), w folderze pojawi się plik `kolejka_priorytetowa.csv` posortowany według priorytetów.

## 🧠 Model NLP do analizy sentymentu

**Wybrany model:** `bardsai/twitter-sentiment-pl-base` (dostępny w bibliotece Hugging Face Transformers).

**Uzasadnienie wyboru:**
Do poprawnego działania na polskojęzycznych zgłoszeniach potrzebowaliśmy modelu, który "rozumie" nasz język. Model *bardsai* został wytrenowany na potężnej bazie danych z polskiego Twittera. Język używany w mediach społecznościowych jest bardzo bliski językowi, jakiego sfrustrowani klienci używają pisząc do Biura Obsługi Klienta – zawiera skróty myślowe, potoczne zwroty i silny ładunek emocjonalny. Model ten jest przy tym wariantem *base* (opartym na architekturze RoBERTa), co oznacza, że zachowuje świetny balans między wysoką dokładnością (Accuracy) a niskim zużyciem zasobów komputerowych. Dzięki temu z łatwością działa lokalnie (nawet bez dedykowanej karty graficznej), spełniając wymóg braku zewnętrznych, płatnych API.

## ⚖️ Zdefiniowane słowa kluczowe (Legal Keywords)

Do identyfikacji gróźb prawnych i eskalacji stworzono listę słów kluczowych opartą o najczęstsze zwroty w konfliktach na linii konsument-sklep:
- "sąd", "sądzie", "pozew" (Bezpośrednie groźby wkroczenia na drogę sądową)
- "prawnik", "kancelari" (Sygnalizacja wsparcia prawnego)
- "rzecznik praw", "rzecznika praw" (Odwołania do Rzecznika Praw Konsumenta)
- "uokik" (Groźba zgłoszenia do Urzędu Ochrony Konkurencji i Konsumentów)
- "policj", "prokuratur" (Zaangażowanie organów ścigania)
- "oszustwo", "oszukany", "okradzion", "kradzież" (Mocne słowa, często będące podstawą do pomówień i ostrego sporu)

Zastosowano fragmenty słów (tzw. rdzenie), aby system wyłapywał różne odmiany (np. "policj" wyłapie zarówno "policja", "policji", jak i "policję").

## 🛠 Dodatkowe optymalizacje (Performance, Bezpieczeństwo i Edge Cases)

W projekcie wykraczono poza podstawowe wymagania, wprowadzając rozwiązania podnoszące niezawodność, wydajność i odporność systemu na błędy:

1. **Zabezpieczenie przed przepełnieniem modelu (Truncation):**
   W funkcji inicjalizującej pipeline dodano flagę `truncation=True`. Gwarantuje to stabilność działania programu nawet w sytuacji, gdy klient wyśle ekstremalnie długą wiadomość (np. wklejając treść całych regulaminów), co zapobiega awariom wynikającym z przekroczenia limitu tokenów przez model. Dodano również flagę `top_k=None` dla kompatybilności z nowymi wersjami Hugging Face.
2. **Integralność danych i kodowanie (JSON):**
   Zamiast standardowego rzutowania na string, do formatowania listy powodów (REASONS) użyto biblioteki `json` z flagą `ensure_ascii=False`. Zabezpiecza to polskie znaki diakrytyczne przed błędnym kodowaniem podczas zapisu do pliku .csv, gwarantując czytelność dla końcowego użytkownika biznesowego.
3. **Zabezpieczenie przed fałszywymi alarmami (Regex Word Boundaries):**
   Użyto wyrażeń regularnych (`re.compile` z użyciem granic słów `\b`) zamiast standardowego wyszukiwania podciągów. Dzięki temu system precyzyjnie reaguje na słowa kluczowe (np. "sąd"), ignorując fałszywe dopasowania ukryte w innych wyrazach (np. "rozsądny"), oszczędzając jednocześnie zasoby dzięki wbudowanej fladze `re.IGNORECASE`.
4. **Grupowe przetwarzanie danych (Batching):**
   Skrypt ładuje dane paczkami (batch size) prosto do potoku (pipeline) NLP. Dzięki temu transformery optymalnie wykorzystują zasoby maszyny, co drastycznie skraca czas weryfikacji całego pliku z minut do ułamków sekund.
