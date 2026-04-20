# TrendVibe – System Priorytetyzacji Zgłoszeń BOK („Sprytne Zwroty AI" v2)

Każda minuta zwłoki w odpowiedzi na pilne zgłoszenie klienta ma swoją cenę. Ten system rozwiązuje ten problem, automatycznie oceniając pilność wiadomości (URGENCY_SCORE) i kategoryzując poziom ryzyka prawnego (RISK_LEVEL) – zanim konsultant zdąży wypić poranną kawę. Całość działa lokalnie, bez żadnych zewnętrznych, płatnych API, opierając się wyłącznie na modelach open-source.

---

## 🚀 Jak uruchomić projekt

1. **Wymagania wstępne:** Python 3.11.x lub 3.12.x (64-bit).
2. **Instalacja zależności:** Otwórz terminal w folderze z projektem i uruchom:
   ```
   pip install -r requirements.txt
   ```
3. **Dane wejściowe:** Upewnij się, że w tym samym katalogu co `main.py` znajduje się plik `do_weryfikacji_recznej_START.csv`.
4. **Uruchomienie:**
   ```
   python main.py
   ```
5. **Wynik:** Po zakończeniu (przy pierwszym uruchomieniu model pobiera się z sieci – to chwilę potrwa) w folderze pojawi się plik `kolejka_priorytetowa.csv` z gotową, posortowaną listą priorytetów.

---

## 🧠 Dlaczego akurat ten model NLP?

**Model:** `bardsai/twitter-sentiment-pl-base` (Hugging Face Transformers)

Klient, który jest sfrustrowany, nie pisze jak prawnik – pisze jak człowiek. Skróty, potoczne zwroty, emocje wprost. Właśnie dlatego wybraliśmy model wytrenowany na milionach wpisów z polskiego Twittera: język mediów społecznościowych jest zaskakująco bliski temu, co ląduje w skrzynce Biura Obsługi Klienta.

Model oparty na architekturze RoBERTa w wariancie `base` to świadomy kompromis: wysoka dokładność przy niskim zużyciu zasobów. Działa płynnie nawet bez dedykowanej karty graficznej, co spełnia jeden z kluczowych wymogów projektu – pełna lokalność bez zewnętrznych kosztów.

---

## ⚖️ Słowa kluczowe sygnalizujące ryzyko prawne

Zamiast czekać, aż sprawa trafi do sądu, system wyłapuje sygnały ostrzegawcze już na etapie wiadomości. Lista słów kluczowych odzwierciedla realia konfliktów konsumenckich w Polsce:

- `sąd`, `sądzie`, `pozew` – bezpośrednia groźba drogi sądowej
- `prawnik`, `kancelari` – sygnał wsparcia prawnego
- `rzecznik praw`, `rzecznika praw` – odwołanie do Rzecznika Praw Konsumenta
- `uokik` – groźba zgłoszenia do UOKiK
- `policj`, `prokuratur` – zaangażowanie organów ścigania
- `oszustwo`, `oszukany`, `okradzion`, `kradzież` – mocne sformułowania często stanowiące podstawę ostrego sporu

Celowo używamy rdzeni słów, a nie pełnych form – dzięki temu `policj` dopasuje zarówno „policja", „policji", jak i „policję", bez potrzeby ręcznego wypisywania każdej odmiany.

---

## 🛠️ Co poszło dalej, niż wymagała specyfikacja

Dobry system to nie tylko poprawna logika – to też odporność na rzeczy, których nie przewidzieliśmy. Dlatego zadbaliśmy o kilka dodatkowych warstw bezpieczeństwa:

**Ochrona przed przepełnieniem modelu (Truncation)**
Pipeline działa ze flagą `truncation=True`. Jeśli klient wklei treść całego regulaminu do pola wiadomości (tak, to się zdarza), model nie wywali błędu – po prostu bezpiecznie przytnie input do dopuszczalnego limitu tokenów. Dodana flaga `top_k=None` zapewnia kompatybilność z nowszymi wersjami biblioteki Hugging Face.

**Polskie znaki bez kompromisów (JSON)**
Zamiast rzutowania na string, lista powodów (REASONS) jest serializowana przez bibliotekę `json` z flagą `ensure_ascii=False`. Żadnych tajemniczych znaków zapytania zamiast „ą", „ę" czy „ż" w wynikowym pliku CSV.

**Koniec z fałszywymi alarmami (Regex Word Boundaries)**
System używa wyrażeń regularnych z granicami słów (`\b`) zamiast prostego wyszukiwania podciągów. Dzięki temu słowo `sąd` nie wyzwoli alarmu w słowie `rozsądny`. Flaga `re.IGNORECASE` sprawia, że wielkość liter przestaje mieć znaczenie, bez duplikowania reguł.

**Szybkość przez przetwarzanie wsadowe (Batching)**
Dane trafiają do pipeline'u NLP w paczkach, a nie rekord po rekordzie. Transformery lubią batche – to pozwoliło skrócić czas przetwarzania całego pliku z minut do ułamków sekund.
