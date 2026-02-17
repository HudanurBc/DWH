# Data Quality & Konsistenz

Dieses Dokument beschreibt die wichtigsten Maßnahmen zur Sicherstellung der Datenqualität
im Data-Warehouse-Projekt zur Notaufnahmesurveillance und deren Integration mit Wetterdaten.

---

## 1. Datenquellen und Grundannahmen

### 1.1 Notaufnahmesurveillance (AKTIN)
- Zeitlich aufgelöste Surveillance-Daten auf **Tagesbasis**
- Bereitstellung relativer Anteile (Prozentwerte), keine absoluten Fallzahlen
- Teilweise fehlende Werte (`NA`) bei modellbasierten Kennzahlen

### 1.2 Wetterdaten (DWD)
- Monatliche, deutschlandweite Mittelwerte
- Vollständig aggregierte Zeitreihen
- Keine erwarteten Missing Values in den finalen Monatsdaten

---

## 2. Umgang mit fehlenden Werten (NA / NULL)

### 2.1 Quelle
In den AKTIN-Daten können fehlende Werte auftreten, insbesondere bei:
- `relative_cases_7day_ma`
- `expected_value`
- `expected_lowerbound`
- `expected_upperbound`

Diese fehlenden Werte entstehen z. B.:
- am Anfang von Zeitreihen
- wenn statistische Modelle für bestimmte Zeitpunkte nicht berechnet werden konnten

---

### 2.2 Transformation
Beim Einlesen der Rohdaten werden folgende Werte explizit als fehlend interpretiert:
- `"NA"`
- `"NaN"`
- leere Strings

In der Transformationsphase gilt:
- Arithmetische Mittelwerte (`mean`) ignorieren fehlende Werte automatisch
- Falls für einen Monat ausschließlich fehlende Tageswerte vorliegen, bleibt der aggregierte Monatswert ebenfalls fehlend

Es erfolgt **keine Imputation oder künstliche Ersetzung** fehlender Werte, um Verzerrungen zu vermeiden.

---

### 2.3 Laden in die Datenbank
- Fehlende Werte aus Pandas (`NaN`) werden konsequent als `NULL` in PostgreSQL gespeichert
- Dimensionsschlüssel (`datum_key`, `syndrom_key`, `altersgruppe_key`, `edtype_key`) sind **NOT NULL**
- Kennzahlen (Measures) dürfen `NULL` sein, sofern dies fachlich begründet ist

---

## 3. Aggregationslogik und Datenkonsistenz

### 3.1 Monatliche Aggregation der Surveillance-Daten
Die ursprünglichen Tagesdaten werden auf Monatsebene aggregiert.

Die Kennzahl  
**`avg_daily_relative_cases_percent`**  
wird wie folgt berechnet:
- arithmetischer Mittelwert der täglichen relativen Anteile eines Syndroms innerhalb eines Monats

Eine gewichtete Aggregation ist nicht möglich, da die Datenquelle keine täglichen absoluten Fallzahlen
(z. B. Anzahl Syndrome-Fälle oder Gesamtvorstellungen) bereitstellt.

---

### 3.2 Einheit und Wertebereiche
- Alle relativen Kennzahlen sind als **Prozentwerte im Bereich 0–100** gespeichert
- Es erfolgt keine zusätzliche Skalierung (z. B. ×100 oder ÷100)

Optional werden in der Datenbank Wertebereichsprüfungen eingesetzt, z. B.:
- Prozentwerte ≥ 0 und ≤ 100

---

## 4. Duplikate und Schlüsselvalidität

### 4.1 Faktentabelle
Für die Faktentabelle gilt der definierte Grain:

> **Monat × Syndrom × Altersgruppe × Notaufnahmetyp**

Dieser Grain wird technisch abgesichert durch:
- einen eindeutigen Constraint auf die entsprechenden Fremdschlüssel

Damit ist sichergestellt, dass:
- keine doppelten Faktzeilen existieren
- jede Kennzahl eindeutig einem fachlichen Kontext zugeordnet ist

---

## 5. Wetterdaten-Konsistenz

- Wetterdaten liegen auf Monatsebene vor
- Die Werte sind innerhalb eines Monats konstant
- Die Integration erfolgt bewusst auf derselben zeitlichen Granularität wie die aggregierten Surveillance-Daten

---

## 6. Umgang mit NULL-Werten in Auswertungen

In nachgelagerten Auswertungen (z. B. BI-Tools):
- NULL-Werte werden **nicht automatisch als 0 interpretiert**
- Zeitreihen dürfen Lücken enthalten, um fehlende Modellwerte transparent darzustellen

---

## 7. Zusammenfassung

Die Datenqualität wird durch folgende Maßnahmen sichergestellt:
- bewusster Umgang mit fehlenden Werten
- transparente Aggregationslogik
- klare Definition von Einheiten und Wertebereichen
- technische Absicherung des Fakt-Grains
- vollständige Dokumentation bekannter Datenlimitationen

Diese Vorgehensweise stellt sicher, dass Analysen reproduzierbar, nachvollziehbar und fachlich korrekt sind.

