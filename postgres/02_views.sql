-- BI schema (optional but recommended)
CREATE SCHEMA IF NOT EXISTS bi;

-- This view flattens the star schema into a Superset-friendly dataset
CREATE OR REPLACE VIEW bi.vw_erkrankungen_monatlich AS
SELECT
  dd.jahr                   AS year,
  dd.monat                  AS month,
  dd.saison                 AS season,

  ds.bezeichnung            AS syndrome,
  da.altersgruppe           AS age_group,
  de.typ                    AS ed_type,

  fe.relative_cases         AS relative_cases,
  fe.relative_cases_7day_ma AS relative_cases_7day_ma,
  fe.expected_value         AS expected_value,
  fe.expected_lowerbound    AS expected_lowerbound,
  fe.expected_upperbound    AS expected_upperbound,
  fe.ed_count               AS ed_count,

  fe.temperature_mean       AS temperature_mean,
  fe.precipitation          AS precipitation,
  fe.sunshine_duration      AS sunshine_duration,

  -- A real date is convenient for time-series charts
  make_date(dd.jahr, dd.monat, 1) AS month_date

FROM fakt_erkrankungen fe
JOIN dim_datum dd
  ON dd.datum_key = fe.datum_key
JOIN dim_syndrom ds
  ON ds.syndrom_key = fe.syndrom_key
JOIN dim_altersgruppe da
  ON da.altersgruppe_key = fe.altersgruppe_key
JOIN dim_edtype de
  ON de.edtype_key = fe.edtype_key;

