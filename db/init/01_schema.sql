CREATE TABLE IF NOT EXISTS dim_syndrom (
  syndrom_key BIGSERIAL PRIMARY KEY,
  bezeichnung TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_edtype (
  edtype_key BIGSERIAL PRIMARY KEY,
  typ TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_altersgruppe (
  altersgruppe_key BIGSERIAL PRIMARY KEY,
  altersgruppe TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_datum (
  datum_key BIGSERIAL PRIMARY KEY,
  datum DATE NOT NULL,
  jahr INT NOT NULL,
  monat INT NOT NULL,
  woche INT NOT NULL,
  saison TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS fakt_erkrankungen (
  fakt_key BIGSERIAL PRIMARY KEY,
  datum_key BIGINT NOT NULL REFERENCES dim_datum(datum_key),
  syndrom_key BIGINT NOT NULL REFERENCES dim_syndrom(syndrom_key),
  altersgruppe_key BIGINT NOT NULL REFERENCES dim_altersgruppe(altersgruppe_key),
  edtype_key BIGINT NOT NULL REFERENCES dim_edtype(edtype_key),

  relative_cases DOUBLE PRECISION NULL,
  relative_cases_7day_ma DOUBLE PRECISION NULL,
  expected_value DOUBLE PRECISION NULL,
  expected_lowerbound DOUBLE PRECISION NULL,
  expected_upperbound DOUBLE PRECISION NULL,
  ed_count DOUBLE PRECISION NULL,

  temperature_mean DOUBLE PRECISION NULL,
  precipitation DOUBLE PRECISION NULL,
  sunshine_duration DOUBLE PRECISION NULL
);

