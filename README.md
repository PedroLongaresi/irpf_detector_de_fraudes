# 🛡️ IRPF Detector de Fraudes & Motor Pericial Forense (Zero-Knowledge Engine)

> **Motor autônomo de perícia forense cega, inspeção estrutural de streams PDF e validação matemática da cascata tributária da Receita Federal do Brasil (RFB).**

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Security: Blue Team](https://img.shields.io/badge/Security-Blue%20Team%20%26%20AppSec-red.svg)](#)
[![Performance: ~11ms](https://img.shields.io/badge/Performance-~11ms%2Fdoc-brightgreen.svg)](#)

---

## 📌 Visão Geral

O **IRPF Detector de Fraudes** é uma solução de engenharia de software e segurança defensiva (Blue Team) projetada para auditar declarações de IRPF em PDF sem depender de ferramentas externas pesadas, OCRs lentos ou soluções de terceiros suscetíveis a evasão.

O motor opera no modelo **Zero-Knowledge (Perícia Cega)**: ele audita e identifica adulterações em **qualquer PDF de IRPF sem conhecer o documento previamente** e sem necessitar de um PDF original como referência de comparação.

---

## 🚨 O Problema que Resolve

Em testes homologatórios de soluções de mercado (ex.: VerifAI Docs / Certta), constatou-se:
1. **0% de Retenção em Fraudes Vetoriais:** Documentos com renda inflada via máscara branca (*whiteout*), texto invisível (`3 Tr`) e recálculo manual de fontes passaram com classificação de **"Baixo Risco"** (100% de concessão indevida / risco de PDD).
2. **222 minutos de Parada de Esteira:** Arquivos protegidos por senha (`/Encrypt`) ou com canários de rede travaram a ingestão por **3h 42m** por ausência de *circuit breaker*.

Esta solução resolve ambos os problemas executando em **~11 milissegundos por documento**, com **Fail-Closed imediato** e auditoria em **8 dimensões forenses**.

---

## 🔬 As 8 Dimensões de Auditoria Forense

```
[ Upload do PDF ] ──▶ [ AppSec (<5ms) ] ──▶ [ Metadados/Multi-EOF ] ──▶ [ Content Streams ] ──▶ [ Equação Tributária ] ──▶ [ Laudo JSON ]
```

1. **AppSec & Resiliência (< 5ms):** Detecção instantânea de `/Encrypt` (PDF com senha), `/OpenAction`, `/JavaScript`, `/JS` e canários `/URI` (SSRF).
2. **Perícia Binária & Re-salvamento:** Identificação de múltiplos `%%EOF` (*Incremental Updates* pós-emissão) e discrepância entre `/CreationDate` e `/ModDate`.
3. **Máscara Branca (*Whiteout*):** Varredura de retângulos opacos (`re f`) com cor branca `#FFFFFF` desenhados por cima de texto pré-existente.
4. **Texto Invisível (*Dual-Layer / OCR Poisoning*):** Detecção do modo de renderização `3 Tr` (*Neither fill nor stroke*) e fontes de tamanho nulo (`0.001 Tf`).
5. **Tipografia & Fontes Não-Padrão:** Bloqueio de fontes estranhas à RFB (`/Courier`, `/Arial`) e desalinhamentos geométricos de baseline na matriz `Tm`.
6. **Integridade de Páginas & Golpe '8 de 8 Falso':** Detecção de ponteiros duplicados no array `/Kids` (ex.: página 6 duplicada para sumir com o resumo da página 7) e numeração de rodapés.
7. **Frankenstein PDF (Colagem Documental):** Extração do CPF na Página 1 e auditoria de auto-coerência em todas as páginas subsequentes.
8. **Equação Tributária da RFB:** Recálculo autônomo da cascata contábil da Página 7:
   $$\text{Base de Cálculo} = \text{Total de Rendimentos Tributáveis} - \text{Desconto Simplificado}$$
   Se a renda for inflada sem recalcular a base ou imposto, o motor calcula a diferença exata e reprova o documento.
9. **Cruzamento de Rendimentos Isentos:** Validação cruzada entre a Página 2 (Tabela de Isentos) e a Página 8 (*Outras Informações*).

---

## 📊 Matriz de Resultados (Benchmark em 26 Casos de Teste)

O motor foi testado contra uma suíte com 26 cenários de teste (`CT00` a `CT08B`):

| Caso de Teste | Descrição da Fraude / Teste | Status Cego | Score | Tempo |
| :--- | :--- | :---: | :---: | :---: |
| `CT00` | Baseline Original Íntegro (Controle Positivo) | ✅ `APROVADO` | 0/100 | 13ms |
| `CT01A` | Supressão de Marca d'Água Oficial | ❌ `REPROVADO` | 30/100 | 12ms |
| `CT01B` | Status "EM PREENCHIMENTO" (Rascunho não transmitido) | ❌ `REPROVADO` | 80/100 | 12ms |
| `CT01C` | Retificadora com Recibo Zerado (`00.00.00.00.00-00`) | ❌ `REPROVADO` | 30/100 | 11ms |
| `CT01D` | Declaração Final de Espólio (Contribuinte Falecido) | ❌ `REPROVADO` | 30/100 | 10ms |
| `CT02A` | CPF com Dígito Módulo 11 Inválido | ❌ `REPROVADO` | 50/100 | 11ms |
| `CT02B` | Nome Divergente da Proposta | ❌ `REPROVADO`* | 30/100 | 13ms |
| `CT02C` | Inversão Familiar: Alimentanda promovida a Titular | ❌ `REPROVADO` | 100/100 | 11ms |
| `CT03A` | Vigência Expirada (Exercício anterior) | ❌ `REPROVADO`** | 15/100 | 12ms |
| `CT03B` | Incoerência Temporal (Exercício vs. Ano-Calendário) | ❌ `REPROVADO` | 30/100 | 12ms |
| `CT04A` | Incompletude: Falta Página 7 (Resumo) | ❌ `REPROVADO` | 60/100 | 11ms |
| `CT04B` | Quebra de Sequência Física de Páginas | ❌ `REPROVADO` | 80/100 | 12ms |
| `CT04C` | Frankenstein PDF: CPF divergente na Pág. 2 e Total Pág. 7 | ❌ `REPROVADO` | 100/100 | 13ms |
| `CT04D` | Envio de apenas 1 página avulsa | ❌ `REPROVADO` | 30/100 | 10ms |
| `CT04E` | Golpe '8 de 8 Falso': Pág. 6 duplicada na árvore `/Kids` | ❌ `REPROVADO` | 80/100 | 11ms |
| `CT05A` | Incremental Update (Múltiplos `%%EOF`) | ❌ `REPROVADO` | 30/100 | 11ms |
| `CT05B` | Máscara Branca (*Whiteout*) sobre a Renda | ❌ `REPROVADO` | 100/100 | 12ms |
| `CT05C` | Achatamento / Rasterização virtual (*Print-to-PDF*) | ❌ `REPROVADO` | 30/100 | 12ms |
| `CT06A` | Injeção de Fonte Não-RFB (`/Courier-Bold`) | ❌ `REPROVADO` | 60/100 | 11ms |
| `CT06B` | Desalinhamento Geométrico e Escala na Matriz `Tm` | ❌ `REPROVADO` | 30/100 | 11ms |
| `CT06C` | Injeção de Texto Invisível (`3 Tr` Dual-Layer) | ❌ `REPROVADO` | 50/100 | 11ms |
| `CT07A` | Renda inflada sem recalcular a Página 7 | ❌ `REPROVADO` | 50/100 | 10ms |
| `CT07B` | Fraude Perfeita Red Team (Recálculo Integral da Pág. 7) | ⚠️ `GAP RFB`*** | 40/100 | 11ms |
| `CT07C` | Renda Isenta inflada na Pág. 2 vs Pág. 8 | ❌ `REPROVADO` | 50/100 | 11ms |
| `CT08A` | PDF com Senha (`/Encrypt` — Fail-Closed imediato) | ❌ `REPROVADO` | 50/100 | 11ms |
| `CT08B` | PDF com Payload Ativo (`/OpenAction`, `/JS`, `/URI`) | ❌ `REPROVADO` | 50/100 | 10ms |

> \* Com parâmetro `--expected-nome` da proposta.  
> \*\* Com parâmetro `--expected-exercicio`.  
> \*\*\* Alerta mandatório de consulta à API SERPRO/Receita Federal.

---

## 🎯 Entendendo o Score de Risco (0 a 100)

O **Score de Risco** é um índice numérico determinístico que quantifica o grau de evidência técnica de manipulação, fraude ou inconsistência contábil no arquivo:

### 🚦 Faixas de Decisão Operacional

| Faixa de Score | Classificação | Significado Forense | Ação Recomendada na Esteira |
| :---: | :---: | :--- | :--- |
| **`0 / 100`** | 🟢 **Risco Zero** | Documento 100% íntegro, original da Receita Federal, sem nenhum rastro de adulteração. | **Aprovação Automática (*Straight-Through Processing - STP*)**. |
| **`15 a 30 / 100`** | 🟡 **Risco Médio** | Inconsistências de regras de negócio ou arquivo re-salvo (marca d'água ausente, incremental update, exercício antigo). | **Transbordo para Mesa Humana** ou solicitação de reenvio. |
| **`40 a 45 / 100`** | 🟠 **Alerta GAP RFB** | Documento matematicamente perfeito com renda expressiva, sujeito a fraude sintética Red Team (`CT07B`). | **Consulta Obrigatória na API SERPRO / RFB** para validação do recibo. |
| **`50 a 100 / 100`** | 🔴 **Risco Crítico** | **Fraude confirmada:** máscara branca (*whiteout*), texto invisível `3 Tr`, páginas coladas de terceiros, CPF inválido ou quebra da equação tributária. | **Rejeição Automática Imediata** (economiza custo de OCR e mesa humana). |

### 🧮 Composição do Cálculo (Pesos Cumulativos)

* 🚨 **Violações CRÍTICAS (+50 pontos cada):**
  * Máscara branca (*Whiteout* sobre valores originais de rendimento).
  * Injeção de texto invisível (`3 Tr` / OCR poisoning).
  * Quebra da Equação Tributária (Renda da Pág. 1/2 não bate com o imposto da Pág. 7).
  * *Frankenstein PDF* (Página 1 tem um CPF e a Página 2 tem outro CPF diferente).
  * Inversão de papéis (o titular é na verdade um alimentando/dependente).
  * CPF com dígito verificador matematicamente inválido (Módulo 11 da RFB).
  * PDF malicioso ou com senha (`/Encrypt`, `/OpenAction`, `/JavaScript`).

* ⚠️ **Violações ALTAS (+30 pontos cada):**
  * Supressão da marca d'água oficial `PROTEGIDA POR SIGILO FISCAL`.
  * Status "EM PREENCHIMENTO" (Rascunho não transmitido à Receita Federal).
  * Injeção de fontes não oficiais da RFB (`/Courier-Bold`, `/Arial`).
  * Desalinhamento geométrico de números (salto no eixo $y$ ou escala distorcida `Tm`).
  * Múltiplos `%%EOF` (revisões incrementais pós-emissão).
  * Incompletude (ausência de páginas essenciais como o resumo tributário).

* ℹ️ **Violações MÉDIAS (+15 pontos cada):**
  * Exercício ou ano-calendário fora da janela aceita pela política de crédito.
  * Discrepância temporal entre `/CreationDate` e `/ModDate` no dicionário `/Info`.

---

## 💻 Como Utilizar

### 1. Auditoria Cega (Zero-Knowledge) em um único arquivo:
```bash
python scripts/auditar_declaracoes_irpf.py --file caminho/do/documento.pdf
```

### 2. Auditoria Cega em lote (todos os arquivos de um diretório):
```bash
python scripts/auditar_declaracoes_irpf.py --dir arquivos_teste_irpf/
```

### 3. Modo Híbrido (Perícia Forense + Dados da Proposta do Cliente):
```bash
python scripts/auditar_declaracoes_irpf.py \
  --file documento.pdf \
  --expected-cpf "250.713.388-07" \
  --expected-nome "GILSONEI DOS SANTOS" \
  --expected-exercicio "2026"
```

### 4. Exportação Estruturada em JSON (ideal para APIs e microsserviços):
```bash
python scripts/auditar_declaracoes_irpf.py --file documento.pdf --json
```

---

## 🏗️ Estrutura do Repositório

```
irpf_detector_de_fraudes/
├── scripts/
│   ├── auditar_declaracoes_irpf.py      # Motor pericial forense Blue Team (Zero-Knowledge)
│   ├── gerar_arquivos_teste_irpf.py     # Gerador cirúrgico de massa de teste Red Team
│   └── gerar_planilha_xlsx_irpf.py      # Gerador da matriz e roteiro de testes em Excel
├── arquivos_teste_irpf/                 # 26 arquivos PDF de teste (CT00 a CT08B)
├── DOC_TECNICA_SCRIPT_AUDITORIA_IRPF.md # Documentação técnica de arquitetura para Tech Leads
├── ROTEIRO_DE_TESTE_RTF_RED_BLUE_TEAM_IRPF.md # Roteiro detalhado de testes funcionais e forenses
├── ROTEIRO_DE_TESTE_IRPF_IUDOCS_VS_CERTA.xlsx # Planilha executiva com matriz de escopo
└── README.md                            # Guia completo do projeto
```

---

## 📄 Licença

Distribuído sob licença MIT. Consulte `LICENSE` para mais informações.
