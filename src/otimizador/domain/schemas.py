"""Contratos tipados (Pydantic) para entrada e saída do solver."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ScenarioConfig(BaseModel):
    """Configuração de cenário estratégico."""

    model_config = ConfigDict(frozen=True)

    tempo_limite_segundos: int = Field(default=120, ge=1)
    cds_obrigatorios: list[int] | None = Field(default=None)
    max_cds: int | None = Field(default=None, ge=1)

    @model_validator(mode="after")
    def check_max_cds(self) -> ScenarioConfig:
        if self.max_cds is not None and self.cds_obrigatorios is not None:
            if len(self.cds_obrigatorios) > self.max_cds:
                raise ValueError(
                    "Número de CDs obrigatórios não pode exceder max_cds"
                )
        return self


class SolverInput(BaseModel):
    """Entrada tipada para o solver."""

    model_config = ConfigDict(frozen=True)

    # Usamos Any aqui para evitar circular import; validamos na camada de serviço
    cds: list
    clientes: list
    produtos: list
    config: ScenarioConfig = Field(default_factory=ScenarioConfig)

    @model_validator(mode="after")
    def check_non_empty(self) -> SolverInput:
        if not self.cds:
            raise ValueError("Lista de CDs não pode estar vazia")
        if not self.clientes:
            raise ValueError("Lista de clientes não pode estar vazia")
        if not self.produtos:
            raise ValueError("Lista de produtos não pode estar vazia")
        return self


class Allocation(BaseModel):
    """Uma alocação ótima: CD → Cliente → Produto."""

    cd_id: str
    cd_nome: str
    cd_cidade: str
    cd_lat: float
    cd_lon: float
    cliente_id: str
    cliente_nome: str
    cliente_cidade: str
    cliente_lat: float
    cliente_lon: float
    produto_id: str
    produto_nome: str
    quantidade: float = Field(ge=0.0)
    custo_transporte_total: float = Field(ge=0.0)


class StockLevel(BaseModel):
    """Nível de estoque ótimo em um CD para um produto."""

    cd_id: str
    cd_nome: str
    produto_id: str
    produto_nome: str
    estoque: float = Field(ge=0.0)
    custo_estoque_mensal: float = Field(ge=0.0)


class CDResult(BaseModel):
    """Resumo de um CD na solução ótima."""

    cd_id: str
    nome: str
    cidade: str
    lat: float
    lon: float
    custo_fixo: float = Field(ge=0.0)
    utilizacao_pct: float = Field(ge=0.0, le=100.0)
    volume_total: float = Field(ge=0.0)
    capacidade: int = Field(gt=0)


class SolverOutput(BaseModel):
    """Saída tipada do solver com todas as métricas da solução."""

    status: str  # "OPTIMO" | "VIAVEL" | "INVIAVEL"
    status_code: int
    custo_total: float = Field(ge=0.0)
    custo_fixo: float = Field(ge=0.0)
    custo_transporte: float = Field(ge=0.0)
    custo_estoque: float = Field(ge=0.0)
    cds_abertos: list[CDResult]
    alocacoes: list[Allocation]
    estoques: list[StockLevel]
    utilizacao_cds: dict[str, float]
    demanda_total: int = Field(ge=0)
    tempo_solucao_ms: int = Field(ge=0)
    iteracoes: int = Field(ge=0)
    nos: int = Field(ge=0)

    @model_validator(mode="after")
    def check_custo_consistency(self) -> SolverOutput:
        if self.status == "INVIAVEL":
            return self
        soma = self.custo_fixo + self.custo_transporte + self.custo_estoque
        # Tolerância para erros de arredondamento do solver
        if abs(soma - self.custo_total) > 1.0:
            raise ValueError(
                f"Custo total inconsistente: {self.custo_total} != {soma} "
                f"(fixo={self.custo_fixo} + transp={self.custo_transporte} + est={self.custo_estoque})"
            )
        return self
