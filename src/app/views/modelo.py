"""Tab: Documentação do modelo matemático."""

from __future__ import annotations

import streamlit as st


def render() -> None:
    st.markdown("### Formulacao Matematica do Modelo")

    st.markdown(r"""
    Este problema é modelado como um **Problema de Localização de Facilidades com Estoque Integrado (FLP-EI)**,
    uma classe clássica de otimização combinatória em supply chain.

    #### Índices
    - $i \in I$: Centros de Distribuição (CDs) candidatos
    - $j \in J$: Clientes / Mercados
    - $k \in K$: Produtos / SKUs

    #### Variáveis de Decisão
    | Variável | Tipo | Significado |
    |----------|------|-------------|
    | $y_i \in \{0,1\}$ | Binária | 1 se CD $i$ está aberto |
    | $z_{ik} \in \{0,1\}$ | Binária | 1 se CD $i$ estoca produto $k$ |
    | $x_{ijk} \geq 0$ | Contínua | Quantidade de $k$ enviada de $i$ para $j$ |
    | $s_{ik} \geq 0$ | Contínua | Estoque de $k$ mantido em $i$ |

    #### Função Objetivo
    $$\min Z = \underbrace{\sum_{i} f_i y_i}_{\text{Fixo}} + \underbrace{\sum_{ijk} c_{ijk} x_{ijk}}_{\text{Transporte}} + \underbrace{\sum_{ik} h_{ik} s_{ik}}_{\text{Estoque}}$$

    #### Restrições Principais
    1. **Demanda atendida:** $\sum_i x_{ijk} = d_{jk}, \; \forall j,k$
    2. **Capacidade do CD:** $\sum_{jk} x_{ijk} \leq Cap_i \cdot y_i, \; \forall i$
    3. **Lógica de estoque:** $z_{ik} \leq y_i$ e $\sum_j x_{ijk} \leq M_{ik} \cdot z_{ik}$
    4. **Estoque de segurança:** $s_{ik} \geq \alpha \sum_j x_{ijk}$  *(α configurável, default 10%)*
    5. **Limite de estoque:** $s_{ik} \leq cap_{ik} \cdot z_{ik}$

    #### Complexidade
    - Variáveis: $|I| + |I||K| + |I||J||K| + |I||K|$ (mistas: binárias + contínuas)
    - Restrições: $|J||K| + |I| + 2|I||K| + |I||K|$
    - Classe: **MIP (Mixed Integer Programming)** — NP-difícil no pior caso
    - Solver: CBC (Branch-and-Cut) via OR-Tools
    """)

    st.markdown("---")
    st.markdown("### Por que MIP?")
    st.markdown("""
    O valor deste projeto está na **modelagem matemática**:

    1. **Decisões discretas** (abrir/fechar CDs) exigem variáveis binárias
    2. **Restrições lógicas** ("só envia se estocar, só estoca se aberto") exigem big-M
    3. **Trade-off explícito** entre custo fixo (menos CDs) e custo de transporte (mais CDs = menor distância)
    4. **Escalabilidade**: o mesmo modelo serve para 12 CDs ou 120, 25 clientes ou 2.500

    O solver explora implicitamente $2^{|I|}$ combinações de CDs, mas a formulação linear permite
    que o Branch-and-Cut elimine bilhões de possibilidades sem enumerá-las.
    """)
