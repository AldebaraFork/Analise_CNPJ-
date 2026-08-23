-- Gerado por etl_cnpj.py a partir do catálogo do PostgreSQL.
-- Recriado automaticamente após a reconstrução de empresas_gold.

CREATE MATERIALIZED VIEW mv_bolhas_ano_municipio AS
 SELECT EXTRACT(year FROM e.data_abertura)::integer AS ano,
    e.cod_municipio,
    COALESCE(m.descricao, e.cod_municipio::text) AS nome_municipio,
    count(*) AS total_empresas,
    avg(e.capital_social) AS capital_medio
   FROM empresas_gold e
     LEFT JOIN municipios_referencia m ON m.codigo = e.cod_municipio
  WHERE e.data_abertura IS NOT NULL AND e.cod_municipio IS NOT NULL AND e.capital_social::double precision > 0::double precision
  GROUP BY (EXTRACT(year FROM e.data_abertura)::integer), e.cod_municipio, m.descricao;

CREATE MATERIALIZED VIEW mv_capital_ano_municipio AS
 SELECT EXTRACT(year FROM e.data_abertura)::integer AS ano,
    COALESCE(m.descricao, e.cod_municipio::text) AS cidade,
    count(*) AS empresas,
    round(percentile_cont(0.50::double precision) WITHIN GROUP (ORDER BY (e.capital_social::double precision))::numeric, 2) AS capital_mediano,
    round(avg(e.capital_social), 2) AS capital_medio
   FROM empresas_gold e
     LEFT JOIN municipios_referencia m ON m.codigo = e.cod_municipio
  WHERE e.capital_social > 0::numeric AND e.cod_municipio IS NOT NULL AND e.data_abertura >= '2005-01-01'::date
  GROUP BY (EXTRACT(year FROM e.data_abertura)::integer), (COALESCE(m.descricao, e.cod_municipio::text))
 HAVING count(*) >= 50;

CREATE MATERIALIZED VIEW mv_comparador_uf_kpis AS
 SELECT "left"(cod_municipio::text, 2) AS cod_uf,
    count(*) AS total_empresas,
    round(avg(capital_social) FILTER (WHERE capital_social::double precision > 0::double precision), 2) AS capital_medio
   FROM empresas_gold
  GROUP BY ("left"(cod_municipio::text, 2));

CREATE MATERIALIZED VIEW mv_coorte_sobrevivencia AS
 SELECT EXTRACT(year FROM data_abertura)::integer AS coorte,
    COALESCE(
        CASE
            WHEN situacao_cadastral = 8 AND data_situacao IS NOT NULL AND data_situacao >= data_abertura THEN floor((data_situacao - data_abertura)::numeric / 365.25)::integer
            ELSE NULL::integer
        END, '-1'::integer) AS ano_baixa,
    count(*) AS qtd
   FROM empresas_gold
  WHERE data_abertura >= '1990-01-01'::date
  GROUP BY (EXTRACT(year FROM data_abertura)::integer), (COALESCE(
        CASE
            WHEN situacao_cadastral = 8 AND data_situacao IS NOT NULL AND data_situacao >= data_abertura THEN floor((data_situacao - data_abertura)::numeric / 365.25)::integer
            ELSE NULL::integer
        END, '-1'::integer));

CREATE MATERIALIZED VIEW mv_crescimento_municipio AS
 SELECT EXTRACT(year FROM e.data_abertura)::integer AS ano,
    e.cod_municipio,
    COALESCE(m.descricao, e.cod_municipio::text) AS nome_municipio,
    count(*) AS total
   FROM empresas_gold e
     LEFT JOIN municipios_referencia m ON m.codigo = e.cod_municipio
  WHERE e.data_abertura IS NOT NULL AND e.cod_municipio IS NOT NULL AND e.data_abertura >= '1990-01-01 00:00:00'::timestamp without time zone
  GROUP BY (EXTRACT(year FROM e.data_abertura)::integer), e.cod_municipio, m.descricao;

CREATE MATERIALIZED VIEW mv_crescimento_uf AS
 SELECT uf,
    EXTRACT(year FROM data_abertura)::integer AS ano,
    count(*) AS aberturas
   FROM empresas_gold
  WHERE data_abertura IS NOT NULL AND uf IS NOT NULL AND uf <> ''::text
  GROUP BY uf, (EXTRACT(year FROM data_abertura)::integer);

CREATE MATERIALIZED VIEW mv_kpis_uf AS
 SELECT uf,
    count(*) AS total_empresas,
    round(avg(capital_social) FILTER (WHERE capital_social > 0::numeric), 2) AS capital_medio,
    round(100.0 * count(*) FILTER (WHERE situacao_cadastral = 2)::numeric / count(*)::numeric, 2) AS pct_ativas
   FROM empresas_gold
  WHERE uf IS NOT NULL AND uf <> ''::text
  GROUP BY uf;

CREATE MATERIALIZED VIEW mv_natalidade_mortalidade AS
 WITH aberturas AS (
         SELECT EXTRACT(year FROM empresas_gold.data_abertura)::integer AS ano,
            empresas_gold.uf,
            count(*) AS qtd
           FROM empresas_gold
          WHERE empresas_gold.data_abertura IS NOT NULL AND empresas_gold.uf IS NOT NULL AND empresas_gold.uf <> ''::text
          GROUP BY (EXTRACT(year FROM empresas_gold.data_abertura)::integer), empresas_gold.uf
        ), baixas AS (
         SELECT EXTRACT(year FROM empresas_gold.data_situacao)::integer AS ano,
            empresas_gold.uf,
            count(*) AS qtd
           FROM empresas_gold
          WHERE empresas_gold.situacao_cadastral = 8 AND empresas_gold.data_situacao IS NOT NULL AND empresas_gold.uf IS NOT NULL AND empresas_gold.uf <> ''::text
          GROUP BY (EXTRACT(year FROM empresas_gold.data_situacao)::integer), empresas_gold.uf
        )
 SELECT COALESCE(a.ano, b.ano) AS ano,
    COALESCE(a.uf, b.uf) AS uf,
    COALESCE(a.qtd, 0::bigint) AS aberturas,
    COALESCE(b.qtd, 0::bigint) AS baixas,
    COALESCE(a.qtd, 0::bigint) - COALESCE(b.qtd, 0::bigint) AS saldo
   FROM aberturas a
     FULL JOIN baixas b ON a.ano = b.ano AND a.uf = b.uf
  WHERE COALESCE(a.ano, b.ano) >= 1990 AND COALESCE(a.ano, b.ano) <= 2100;

CREATE MATERIALIZED VIEW mv_painel_ano AS
 SELECT EXTRACT(year FROM data_abertura)::integer AS ano,
    count(*) AS empresas,
    sum(capital_social) AS capital_total
   FROM empresas_gold
  WHERE capital_social > 0::numeric AND data_abertura IS NOT NULL
  GROUP BY (EXTRACT(year FROM data_abertura)::integer);

CREATE MATERIALIZED VIEW mv_painel_cidade AS
 SELECT COALESCE(m.descricao, e.cod_municipio::text) AS cidade,
    count(*) AS empresas,
    sum(e.capital_social) AS capital_total
   FROM empresas_gold e
     LEFT JOIN municipios_referencia m ON m.codigo = e.cod_municipio
  WHERE e.capital_social > 0::numeric
  GROUP BY (COALESCE(m.descricao, e.cod_municipio::text));

CREATE MATERIALIZED VIEW mv_sobrevivencia_faixas AS
 WITH duracao AS (
         SELECT e.cnae_fiscal,
            (e.data_situacao - e.data_abertura)::numeric / 365.25 AS anos
           FROM empresas_gold e
          WHERE e.situacao_cadastral = 8 AND e.data_situacao IS NOT NULL AND e.data_situacao >= e.data_abertura
        ), classificada AS (
         SELECT COALESCE(c.descricao, 'CNAE '::text || d.cnae_fiscal::text) AS setor,
                CASE
                    WHEN d.anos < 1::numeric THEN 1
                    WHEN d.anos < 3::numeric THEN 2
                    WHEN d.anos < 5::numeric THEN 3
                    WHEN d.anos < 10::numeric THEN 4
                    ELSE 5
                END AS faixa_ordem
           FROM duracao d
             LEFT JOIN cnaes_referencia c ON d.cnae_fiscal = c.codigo
        ), agregada AS (
         SELECT classificada.setor,
            classificada.faixa_ordem,
            count(*) AS qtd
           FROM classificada
          GROUP BY classificada.setor, classificada.faixa_ordem
        ), totais AS (
         SELECT agregada.setor,
            sum(agregada.qtd) AS total_setor
           FROM agregada
          GROUP BY agregada.setor
         HAVING sum(agregada.qtd) >= 1000::numeric
        )
 SELECT a.setor,
    a.faixa_ordem,
        CASE a.faixa_ordem
            WHEN 1 THEN 'Menos de 1 ano'::text
            WHEN 2 THEN '1 a 3 anos'::text
            WHEN 3 THEN '3 a 5 anos'::text
            WHEN 4 THEN '5 a 10 anos'::text
            ELSE 'Mais de 10 anos'::text
        END AS faixa,
    a.qtd,
    t.total_setor,
    round(100.0 * a.qtd::numeric / t.total_setor, 2) AS pct
   FROM agregada a
     JOIN totais t ON t.setor = a.setor;

CREATE MATERIALIZED VIEW mv_sobrevivencia_geral AS
 WITH duracao AS (
         SELECT (empresas_gold.data_situacao - empresas_gold.data_abertura)::numeric / 365.25 AS anos
           FROM empresas_gold
          WHERE empresas_gold.situacao_cadastral = 8 AND empresas_gold.data_situacao IS NOT NULL AND empresas_gold.data_situacao >= empresas_gold.data_abertura
        )
 SELECT count(*) AS total,
    round(avg(anos), 2) AS media,
    round(percentile_cont(0.50::double precision) WITHIN GROUP (ORDER BY (anos::double precision))::numeric, 2) AS mediana,
    round(percentile_cont(0.25::double precision) WITHIN GROUP (ORDER BY (anos::double precision))::numeric, 2) AS q1,
    round(percentile_cont(0.75::double precision) WITHIN GROUP (ORDER BY (anos::double precision))::numeric, 2) AS q3,
    round(percentile_cont(0.90::double precision) WITHIN GROUP (ORDER BY (anos::double precision))::numeric, 2) AS p90
   FROM duracao;

CREATE MATERIALIZED VIEW mv_sobrevivencia_setor AS
 WITH duracao AS (
         SELECT e.cnae_fiscal,
            (e.data_situacao - e.data_abertura)::numeric / 365.25 AS anos
           FROM empresas_gold e
          WHERE e.situacao_cadastral = 8 AND e.data_situacao IS NOT NULL AND e.data_situacao >= e.data_abertura
        )
 SELECT COALESCE(c.descricao, 'CNAE '::text || d.cnae_fiscal::text) AS setor,
    count(*) AS total,
    round(avg(d.anos), 2) AS media,
    round(percentile_cont(0.50::double precision) WITHIN GROUP (ORDER BY (d.anos::double precision))::numeric, 2) AS mediana,
    round(percentile_cont(0.05::double precision) WITHIN GROUP (ORDER BY (d.anos::double precision))::numeric, 2) AS p05,
    round(percentile_cont(0.25::double precision) WITHIN GROUP (ORDER BY (d.anos::double precision))::numeric, 2) AS q1,
    round(percentile_cont(0.75::double precision) WITHIN GROUP (ORDER BY (d.anos::double precision))::numeric, 2) AS q3,
    round(percentile_cont(0.95::double precision) WITHIN GROUP (ORDER BY (d.anos::double precision))::numeric, 2) AS p95
   FROM duracao d
     LEFT JOIN cnaes_referencia c ON d.cnae_fiscal = c.codigo
  GROUP BY (COALESCE(c.descricao, 'CNAE '::text || d.cnae_fiscal::text))
 HAVING count(*) >= 1000
  ORDER BY (round(percentile_cont(0.50::double precision) WITHIN GROUP (ORDER BY (d.anos::double precision))::numeric, 2)) DESC;

CREATE MATERIALIZED VIEW mv_treemap_setores AS
 SELECT "left"(cnae_fiscal::text, 2) AS divisao_cnae,
    count(*) AS total_empresas,
    sum(capital_social) AS capital_total
   FROM empresas_gold
  WHERE capital_social::double precision >= 0::double precision AND cnae_fiscal IS NOT NULL
  GROUP BY ("left"(cnae_fiscal::text, 2));

CREATE UNIQUE INDEX mv_treemap_setores_divisao_cnae_idx ON public.mv_treemap_setores USING btree (divisao_cnae);
CREATE INDEX mv_bolhas_ano_municipio_ano_idx ON public.mv_bolhas_ano_municipio USING btree (ano);
CREATE INDEX mv_crescimento_municipio_ano_idx ON public.mv_crescimento_municipio USING btree (ano);
CREATE INDEX mv_crescimento_municipio_cod_municipio_idx ON public.mv_crescimento_municipio USING btree (cod_municipio);
CREATE UNIQUE INDEX uidx_mv_comparador_uf_kpis_cod_uf ON public.mv_comparador_uf_kpis USING btree (cod_uf);
CREATE UNIQUE INDEX uidx_mv_sobrevivencia_setor ON public.mv_sobrevivencia_setor USING btree (setor);
CREATE UNIQUE INDEX uidx_mv_sobrevivencia_geral ON public.mv_sobrevivencia_geral USING btree (total);
CREATE UNIQUE INDEX uidx_mv_kpis_uf ON public.mv_kpis_uf USING btree (uf);
CREATE UNIQUE INDEX uidx_mv_crescimento_uf ON public.mv_crescimento_uf USING btree (uf, ano);
CREATE UNIQUE INDEX uidx_mv_painel_ano ON public.mv_painel_ano USING btree (ano);
CREATE UNIQUE INDEX uidx_mv_painel_cidade ON public.mv_painel_cidade USING btree (cidade);
CREATE UNIQUE INDEX uidx_mv_sobrevivencia_faixas ON public.mv_sobrevivencia_faixas USING btree (setor, faixa_ordem);
CREATE UNIQUE INDEX uidx_mv_coorte_sobrevivencia ON public.mv_coorte_sobrevivencia USING btree (coorte, ano_baixa);
CREATE UNIQUE INDEX uidx_mv_natalidade_mortalidade ON public.mv_natalidade_mortalidade USING btree (ano, uf);
CREATE UNIQUE INDEX uidx_mv_capital_ano_municipio ON public.mv_capital_ano_municipio USING btree (ano, cidade);
