# Pomoc

Florin to lokalna aplikacja budżetowa dla osób, których przychody zmieniają się z miesiąca na miesiąc. Dane są przechowywane lokalnie w pliku SQLite.

## Pierwsze kroki

1. Otwórz aplikację. Trafisz na **Panel**.
2. Przejdź do **Przychody** i wpisz kwotę brutto oraz odliczenia, takie jak VAT, podatek dochodowy i ZUS.
3. Wróć do **Panelu**, żeby zobaczyć dochód netto i podział budżetu.
4. Rejestruj wydatki w zakładce **Wydatki**.
5. Ustaw cele w **Oszczędnościach** i bufory kont w **Cash Flow**.

## Panel

Panel pokazuje szybki przegląd bieżącego miesiąca:

- **Dochód netto** — kwota po dodatkach i odliczeniach.
- **Podział kategorii** — procentowy i kwotowy podział dochodu.
- **Wydane** — suma wydatków z bieżącego miesiąca.
- **Pozostało** — środki, które zostały w kategoriach budżetu.
- **Ostatnie wydatki** — najnowsze wpisy z listy wydatków.

Użyj przełącznika miesiąca w górnym pasku, żeby przeglądać inne miesiące.

## Przychody

Zakładka **Przychody** służy do wpisywania pozycji, które zwiększają lub zmniejszają dochód.

- **Dodatki** to przychody, np. faktura brutto, premia lub dodatkowy projekt.
- **Odliczenia** to koszty i potrącenia, np. VAT, podatek dochodowy i ZUS.
- **Podział kategorii** określa, jaka część dochodu netto trafia do każdej kategorii budżetu.

Kliknij **Edytuj**, żeby dodać, zmienić lub usunąć pozycje oraz zmienić procenty kategorii. Procenty powinny sumować się do 100%.

## Wydatki

Zakładka **Wydatki** pozwala zapisywać i analizować wszystko, co wydajesz.

Kliknij **Dodaj wydatek** i uzupełnij:

- **Data** — dzień wydatku w formacie DD/MM/RRRR.
- **Kwota** — kwota wydatku.
- **Kategoria wydatku** — typ wydatku, np. zakupy spożywcze, transport lub zdrowie.
- **Źródło finansowania** — kategoria budżetu albo cel oszczędnościowy, z którego finansujesz wydatek.
- **Opis** — opcjonalna notatka.
- **Tagi** — opcjonalne etykiety do filtrowania.

Możesz grupować wydatki według daty albo kategorii, filtrować po źródle finansowania i wyszukiwać po opisie, tagu lub kwocie.

## Oszczędności

Zakładka **Oszczędności** pomaga planować cele i śledzić rzeczywisty postęp.

- **Rzeczywiste oszczędności** pokazują, ile faktycznie odłożono, ile brakuje i jaki jest bilans.
- **Planowanie** pokazuje miesięczny plan wpłat dla każdego celu.
- **Termin** wyróżnia miesiąc, w którym cel powinien być osiągnięty.
- **Grupy** pozwalają porządkować cele w większe zestawy.

Kliknij **Edytuj**, żeby dodać cel, grupę albo zmienić plan.

## Cash Flow

Zakładka **Cash Flow** pomaga zarządzać minimalnymi saldami na kontach.

1. W **Ustawieniach** dodaj cele cash-flow, czyli konta i minimalne salda.
2. W **Cash Flow** wpisz bieżące salda.
3. Florin obliczy, ile trzeba przelać na każde konto.
4. Pozostała kwota po uzupełnieniu kont i wydatkach wspólnych trafia do oszczędności.

## Historia

Zakładka **Historia** pokazuje poprzednie miesiące, ich dochód netto, wydatki i podział kategorii. Dane historyczne nie zmieniają się automatycznie po edycji ustawień dla nowych miesięcy.

## Ustawienia

W **Ustawieniach** możesz skonfigurować:

- **Domyślne przychody** — szablon pozycji przychodów dla nowych miesięcy.
- **Cele cash-flow** — konta i minimalne salda używane w zakładce Cash Flow.
- **Kategorie** — podział budżetu i nazwy kategorii.
- **Wygląd** — motyw kolorystyczny aplikacji.
- **Język** — język interfejsu.
- **Dane i backup** — lokalizację bazy danych i eksport bieżącego miesiąca.

Zmiany w ustawieniach są zapisywane automatycznie.

## Dane

Florin działa lokalnie. Dane są przechowywane w pliku `florin.db` w katalogu aplikacji użytkownika:

- macOS: `~/Library/Application Support/Florin/`
- Windows: `AppData/Local/Florin/`

Eksport JSON zapisuje dane aktywnego miesiąca do pliku, który możesz zachować jako kopię lub sprawdzić ręcznie.
