"""Geração de dados sintéticos realistas para testes e demonstrações."""

from __future__ import annotations

import numpy as np

from otimizador.config import SolverSettings
from otimizador.domain.entities import CD, Cliente, Produto


def gerar_dados_sinteticos(
    settings: SolverSettings | None = None,
    seed: int = 42,
) -> tuple[list[CD], list[Cliente], list[Produto]]:
    """Gera uma instância sintética de supply chain de lácteos.

    Args:
        settings: Configurações do solver (usadas para validar ranges).
        seed: Semente do numpy para reprodutibilidade.

    Returns:
        Tripla (cds, clientes, produtos).
    """
    _ = settings  # reservado para validações futuras
    rng = np.random.default_rng(seed)

    produtos = [
        Produto("P01", "Leite UHT Integral 1L", 1.05, 5.99, 180, "A"),
        Produto("P02", "Leite UHT Desnatado 1L", 1.05, 5.49, 180, "A"),
        Produto("P03", "Iogurte Natural 170g", 0.18, 3.29, 35, "A"),
        Produto("P04", "Iogurte Grego 100g", 0.12, 4.99, 30, "B"),
        Produto("P05", "Queijo Mussarela Fat 150g", 0.15, 12.90, 45, "B"),
        Produto("P06", "Requeijão Cremoso 200g", 0.22, 7.49, 60, "B"),
        Produto("P07", "Bebida Láctea 200ml", 0.20, 2.99, 90, "C"),
        Produto("P08", "Creme de Leite 200g", 0.20, 4.29, 120, "C"),
    ]

    cidades_cd = [
        ("CD_SP", "CD São Paulo", "São Paulo", -23.5505, -46.6333),
        ("CD_RJ", "CD Rio de Janeiro", "Rio de Janeiro", -22.9068, -43.1729),
        ("CD_BH", "CD Belo Horizonte", "Belo Horizonte", -19.9167, -43.9345),
        ("CD_CPS", "CD Campinas", "Campinas", -22.9053, -47.0659),
        ("CD_CTB", "CD Curitiba", "Curitiba", -25.4290, -49.2671),
        ("CD_POA", "CD Porto Alegre", "Porto Alegre", -30.0346, -51.2177),
        ("CD_BSB", "CD Brasília", "Brasília", -15.7975, -47.8919),
        ("CD_SSA", "CD Salvador", "Salvador", -12.9714, -38.5014),
        ("CD_FOR", "CD Fortaleza", "Fortaleza", -3.7172, -38.5433),
        ("CD_REC", "CD Recife", "Recife", -8.0476, -34.8770),
        ("CD_MNS", "CD Manaus", "Manaus", -3.1190, -60.0217),
        ("CD_GO", "CD Goiânia", "Goiânia", -16.6869, -49.2648),
    ]

    cidades_cliente = [
        ("CLI01", "Cliente São Paulo Capital", "São Paulo", -23.5505, -46.6333, 850),
        ("CLI02", "Cliente Campinas", "Campinas", -22.9053, -47.0659, 320),
        ("CLI03", "Cliente Sorocaba", "Sorocaba", -23.5015, -47.4526, 180),
        ("CLI04", "Cliente Santos", "Santos", -23.9608, -46.3331, 210),
        ("CLI05", "Cliente Rio Capital", "Rio de Janeiro", -22.9068, -43.1729, 720),
        ("CLI06", "Cliente Niterói", "Niterói", -22.8833, -43.1034, 150),
        ("CLI07", "Cliente BH Capital", "Belo Horizonte", -19.9167, -43.9345, 580),
        ("CLI08", "Cliente Contagem", "Contagem", -19.9317, -44.0538, 190),
        ("CLI09", "Cliente Curitiba", "Curitiba", -25.4290, -49.2671, 420),
        ("CLI10", "Cliente Londrina", "Londrina", -23.3045, -51.1696, 160),
        ("CLI11", "Cliente Porto Alegre", "Porto Alegre", -30.0346, -51.2177, 380),
        ("CLI12", "Cliente Caxias do Sul", "Caxias do Sul", -29.1678, -51.1794, 140),
        ("CLI13", "Cliente Brasília", "Brasília", -15.7975, -47.8919, 450),
        ("CLI14", "Cliente Taguatinga", "Taguatinga", -15.8100, -48.0615, 180),
        ("CLI15", "Cliente Salvador", "Salvador", -12.9714, -38.5014, 510),
        ("CLI16", "Cliente Feira de Santana", "Feira de Santana", -12.2664, -38.9663, 170),
        ("CLI17", "Cliente Fortaleza", "Fortaleza", -3.7172, -38.5433, 390),
        ("CLI18", "Cliente Caucaia", "Caucaia", -3.7333, -38.6533, 130),
        ("CLI19", "Cliente Recife", "Recife", -8.0476, -34.8770, 340),
        ("CLI20", "Cliente Jaboatão", "Jaboatão dos Guararapes", -8.1803, -35.0014, 120),
        ("CLI21", "Cliente Manaus", "Manaus", -3.1190, -60.0217, 280),
        ("CLI22", "Cliente Goiânia", "Goiânia", -16.6869, -49.2648, 310),
        ("CLI23", "Cliente Anápolis", "Anápolis", -16.3267, -48.9525, 110),
        ("CLI24", "Cliente Vitória", "Vitória", -20.3155, -40.3128, 190),
        ("CLI25", "Cliente Florianópolis", "Florianópolis", -27.5954, -48.5480, 160),
    ]

    cds: list[CD] = []
    for cd_id, nome, cidade, lat, lon in cidades_cd:
        if cidade in {"São Paulo", "Rio de Janeiro", "Belo Horizonte", "Campinas", "Curitiba"}:
            cap_total = int(rng.integers(15_000, 25_000))
            custo_fixo = float(rng.integers(80_000, 120_000))
        elif cidade in {"Porto Alegre", "Brasília", "Salvador"}:
            cap_total = int(rng.integers(10_000, 18_000))
            custo_fixo = float(rng.integers(50_000, 80_000))
        else:
            cap_total = int(rng.integers(6_000, 12_000))
            custo_fixo = float(rng.integers(35_000, 60_000))

        cap_produto = {
            p.id: int(cap_total * rng.uniform(0.08, 0.18))
            for p in produtos
        }
        cds.append(CD(cd_id, nome, cidade, lat, lon, cap_total, custo_fixo, cap_produto))

    clientes: list[Cliente] = []
    for cli_id, nome, cidade, lat, lon, demanda_base in cidades_cliente:
        demanda: dict[str, int] = {}
        for p in produtos:
            if p.giro_classificacao == "A":
                fator = rng.uniform(0.8, 1.5)
            elif p.giro_classificacao == "B":
                fator = rng.uniform(0.4, 0.9)
            else:
                fator = rng.uniform(0.15, 0.4)

            if "Leite" in p.nome:
                fator *= 2.5

            demanda[p.id] = max(10, int(demanda_base * fator * rng.uniform(0.7, 1.3)))
        clientes.append(Cliente(cli_id, nome, cidade, lat, lon, demanda))

    return cds, clientes, produtos
