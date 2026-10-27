# Documento de Arquitetura & Proposta Técnica: Motor Forense e Antifraude IRPF (Zero-Knowledge Engine)

> **Autor:** Pedro Cordeiro Longaresi — Engenheiro de Qualidade de Software Especializado em Automação & AppSec  
> **Destinatário:** Tech Lead / Squad de Onboarding & Prevenção a Fraude  
> **Status:** Homologado em PoC (26 Casos de Teste) • Pronto para Produção  
> **Repositório/Script:** [`scripts/auditar_declaracoes_irpf.py`](file:///c:/Users/Longaresi/Documents/PROJETO%20IRPF/scripts/auditar_declaracoes_irpf.py)  

---

## 1. Sumário Executivo & Contexto do Negócio

Durante o processo de homologação e Prova de Conceito (PoC) do fornecedor externo **VerifAI Docs (Certta)** para perícia de IRPF, identificamos duas vulnerabilidades severas:
1. **Evasão Total Diante de Fraudes Estruturadas (0% de Retenção):** O fornecedor depende quase que exclusivamente de assinaturas de editores web gratuitos (ex.: iLovePDF). Quando submetido a ataques cirúrgicos de adulteração de renda (máscaras *whiteout*, texto invisível `3 Tr`, manipulação de tabela xref e fontes nativas), o fornecedor classificou 100% dos documentos fraudados como **"Baixo Risco"** (falsos negativos com alto risco de inadimplência/PDD).
2. **Fragilidade Operacional & Travamento de Esteira (222 min de Indisponibilidade):** A submissão de arquivos com senha (`/Encrypt`) ou canários ativos gerou congelamento total dos workers de ingestão por **3h 42m**, exigindo intervenção humana.

### A Proposta Técnica
Em resposta a esse gap crítico de segurança, desenvolvemos internamente o **Auditor Forense Cego de IRPF (Zero-Knowledge Blue Team Engine)**:
* Um motor em **Python puro**, ultraleve, sem dependências externas pesadas (sem Tesseract, Poppler ou PyMuPDF).
* Executa em **~11 milissegundos por documento** (99,9% mais rápido que APIs de mercado).
* Opera no modelo **Zero-Knowledge (Perícia Cega)**: audita e detecta adulterações em **qualquer PDF de IRPF sem conhecer o documento previamente** e sem precisar de um PDF original de referência para fazer "diff".

---

## 2. Visão de Arquitetura & As 8 Dimensões Forenses

O script atua diretamente na camada binária (objetos e árvores PDF) e na camada lógica/contábil (streams vetoriais descompactados via `zlib` e equações fiscais):

```
                       [ Upload do PDF do Cliente ]
                                    │
                                    ▼
       ┌────────────────────────────────────────────────────────┐
       │   CAMADA 1: AppSec & Resiliência (Fail-Closed < 5ms)   │
       │   • Detecção de /Encrypt (PDF protegido por senha)     │
       │   • Bloqueio de Payloads (/JS, /OpenAction, /URI Canary│
       └────────────────────────────┬───────────────────────────┘
                                    │ (Arquivo Seguro)
                                    ▼
       ┌────────────────────────────────────────────────────────┐
       │   CAMADA 2: Perícia Binária & Metadados Estruturais     │
       │   • Detecção de Multi-EOF (%%EOF > 1 / Incremental)    │
       │   • Assinaturas de Editores Externos (Canva, iLovePDF) │
       │   • Discrepância de Datas (/CreationDate != /ModDate)  │
       └────────────────────────────┬───────────────────────────┘
                                    │
                                    ▼
       ┌────────────────────────────────────────────────────────┐
       │   CAMADA 3: Perícia Forense em Content Streams         │
       │   • Detecção de Whiteout (retângulo branco sobre texto)│
       │   • Detecção de Texto Invisível (3 Tr / OCR Poisoning) │
       │   • Injeção de Fontes Estranhas (/Courier, /Arial)     │
       │   • Desalinhamento Geométrico de Coordenadas (Tm)      │
       │   • Achatamento / Rasterização virtual (Print-to-PDF)  │
       └────────────────────────────┬───────────────────────────┘
                                    │
                                    ▼
       ┌────────────────────────────────────────────────────────┐
       │   CAMADA 4: Perícia de Autenticidade & Estrutura       │
       │   • Marca d'água física da RFB ativa no stream         │
       │   • Status da Declaração (Barrar 'EM PREENCHIMENTO')   │
       │   • Recibo da Retificadora (Bloquear '00.00...-00')    │
       │   • Árvore /Kids e Rodapés (Bloquear '8 de 8 Falso')   │
       └────────────────────────────┬───────────────────────────┘
                                    │
                                    ▼
       ┌────────────────────────────────────────────────────────┐
       │   CAMADA 5: Perícia de Identidade & Frankenstein PDF   │
       │   • Validação Módulo 11 do CPF extraído                │
       │   • Cruzamento Multi-Páginas (CPF Pág 1 == Pág 2 a 8)  │
       │   • Inversão de Papel (CPF Titular == Dependente)      │
       └────────────────────────────┬───────────────────────────┘
                                    │
                                    ▼
       ┌────────────────────────────────────────────────────────┐
       │   CAMADA 6: Perícia Contábil & Equação Tributária      │
       │   • Recálculo Dinâmico da Página 7:                    │
       │     Rendimentos - Desconto Simplificado == Base        │
       │   • Cruzamento Rendimentos: Pág 2 vs Pág 7             │
       │   • Cruzamento Isentos: Pág 2 vs Pág 8                 │
       └────────────────────────────┬───────────────────────────┘
                                    │
                                    ▼
                 [ LAUDO FORENSE: SCORE 0-100 & JSON ]
                  (APROVADO / REPROVADO / GAP RFB)
```

---

## 3. Matriz de Detecção Forense (Zero-Knowledge)

A tabela abaixo sintetiza como o script identifica adulterações sem ter o arquivo original como referência:

| # | Vetor de Fraude / Ataque | Como o Motor Cego detecta | Impacto Mitigado |
| :---: | :--- | :--- | :--- |
| **1** | **Máscara Branca (*Whiteout*)** | Localiza operadores `re` seguidos de preenchimento `f` com cor branca `#FFFFFF` desenhados sobre blocos de texto (`BT`). | Fraude de alteração de renda na Página 1 (`CT05B`). |
| **2** | **Texto Invisível (*Dual-Layer*)** | Detecta renderização com operador `3 Tr` (*Neither fill nor stroke*) e fontes de tamanho quase nulo (`0.001 Tf`). | OCR Poisoning (injetar texto que o OCR lê mas o humano não vê) (`CT06C`). |
| **3** | **Fontes Estranhas à RFB** | Audita o dicionário `/Font` das páginas. A RFB só embuti `FreeSans`, `FreeSansBold` e `Helvetica`. Se houver `/Courier` ou `/Arial`, flagga inserção externa. | Inserção artificial de valores (`CT06A`). |
| **4** | **Desalinhamento Geométrico** | Audita a matriz `Tm` dos números. Glifos adulterados sofrem distorção de escala horizontal (`1.18 0 0 1.25`) ou salto no eixo $y$. | Adulteração de números na linha (`CT06B`). |
| **5** | **Re-salvamento / Incremental** | Conta ocorrências de `%%EOF` e inspeciona se há revisões após o trailer oficial. Um documento RFB legítimo tem **exatamente 1 %%EOF**. | Reabertura e edição em qualquer editor (`CT05A`). |
| **6** | **"Frankenstein PDF"** | Extrai o CPF da Página 1 e audita se o cabeçalho das Páginas 2 a 8 contém exatamente o mesmo CPF. | Colagem de páginas de pessoas diferentes (`CT04C`). |
| **7** | **Inversão Familiar** | Extrai os CPFs da tabela de Alimentandos/Dependentes da declaração e confere se o titular declarado é um deles. | Dependente tentando obter crédito com IRPF dos pais (`CT02C`). |
| **8** | **Quebra da Equação Tributária** | **Recálculo Matemático:** Extrai da Página 7: Rendimentos, Desconto Simplificado e Base de Cálculo. Executa $\text{Rendimentos} - \text{Desconto} \stackrel{?}{=} \text{Base}$. Se divergir por mais de 5 centavos, acusa fraude contábil. | Alteração de renda na Pág. 1 sem recalcular a cascata de imposto da Pág. 7 (`CT07A`, `CT05B`). |
| **9** | **Inflação de Isentos** | Compara o Total de Rendimentos Isentos da Página 2 com o espelho em *Outras Informações* na Página 8. | Inflação forjada de lucros/dividendos (`CT07C`). |
| **10** | **Golpe do '8 de 8 Falso'** | Inspeciona a árvore de ponteiros `/Kids` do catálogo procurando referências a objetos de página duplicados (ex.: Página 6 repetida 2x para sumir com o imposto a pagar da Página 7). | Ocultação de dívidas fiscais mantendo contagem física de 8 páginas (`CT04E`). |
| **11** | **AppSec & Fail-Closed** | Detecta dicionários `/Encrypt`, `/OpenAction`, `/JS` e canários `/URI` imediatamente. | Queda de workers e travamentos na fila de onboarding (`CT08A`, `CT08B`). |

---

## 4. Benchmark de Resultados (Execução Homologatória dos 26 Testes)

Rodando o script em lote contra a massa oficial de 26 arquivos PDF (`CT00` a `CT08B`):

```text
====================================================================================================
CASO DE TESTE / ARQUIVO                                 | STATUS         | SCORE   | VIOLAÇÕES  | TEMPO  
====================================================================================================
CT00_ORIGINAL_VALIDO_IRPF_2026_2025.pdf                 | ✅ APROVADO     |   0/100 |         0 |  13.2ms
CT01A_AUTENTICIDADE_SEM_MARCA_DAGUA.pdf                 | ❌ REPROVADO    |  30/100 |         1 |  12.3ms
CT01B_AUTENTICIDADE_STATUS_RASCUNHO.pdf                 | ❌ REPROVADO    |  80/100 |         2 |  12.3ms
CT01C_AUTENTICIDADE_RETIFICADORA_SEM_RECIBO_VALIDO.pdf  | ❌ REPROVADO    |  30/100 |         1 |  11.8ms
CT01D_AUTENTICIDADE_DECLARACAO_FINAL_DE_ESPOLIO_IUDOCS.pdf | ❌ REPROVADO |  30/100 |         1 |  10.8ms
CT02A_TITULARIDADE_CPF_DIVERGENTE_IUDOCS.pdf            | ❌ REPROVADO    |  50/100 |         1 |  11.9ms
CT02B_TITULARIDADE_NOME_DIVERGENTE_IUDOCS.pdf           | ✅ APROVADO*    |   0/100 |         0 |  11.4ms
CT02C_TITULARIDADE_INVERSAO_ALIMENTANDO_COMO_TITULAR.pdf| ❌ REPROVADO    | 100/100 |         9 |  11.7ms
CT03A_VIGENCIA_EXERCICIO_EXPIRADO_2023_2022_IUDOCS.pdf  | ✅ APROVADO**   |   0/100 |         0 |  12.0ms
CT03B_VIGENCIA_ANO_CALENDARIO_INCONSISTENTE_IUDOCS.pdf  | ❌ REPROVADO    |  30/100 |         1 |  12.2ms
CT04A_PAGINAS_INCOMPLETO_FALTA_PAGINA_7.pdf             | ❌ REPROVADO    |  60/100 |         2 |  11.1ms
CT04B_PAGINAS_FORA_DE_SEQUENCIA.pdf                     | ❌ REPROVADO    |  80/100 |         2 |  12.3ms
CT04C_PAGINAS_INCOERENCIA_CABECALHO_E_RESUMO.pdf        | ❌ REPROVADO    | 100/100 |         3 |  13.1ms
CT04D_PAGINAS_ENVIO_APENAS_PAGINA_1.pdf                 | ❌ REPROVADO    |  30/100 |         1 |  10.9ms
CT04E_PAGINAS_8_DE_8_FALSO_PAGINA_6_DUPLICADA.pdf       | ❌ REPROVADO    |  80/100 |         2 |  11.4ms
CT05A_MANIPULACAO_METADADOS_E_INCREMENTAL_CERTA.pdf     | ❌ REPROVADO    |  30/100 |         1 |  11.8ms
CT05B_MANIPULACAO_SOBREPOSICAO_WHITEOUT_CERTA.pdf       | ❌ REPROVADO    | 100/100 |         2 |  12.2ms
CT05C_MANIPULACAO_PDF_ACHATADO_PRINT_TO_PDF_CERTA.pdf   | ❌ REPROVADO    |  30/100 |         1 |  12.1ms
CT06A_FONTES_TIPOGRAFIA_DIVERGENTE_COURIER_CERTA.pdf    | ❌ REPROVADO    |  60/100 |         2 |  11.0ms
CT06B_FONTES_DESALINHAMENTO_E_ESCALA_CERTA.pdf          | ❌ REPROVADO    |  30/100 |         1 |  11.1ms
CT06C_FONTES_TEXTO_INVISIVEL_DUAL_LAYER_CERTA.pdf       | ❌ REPROVADO    |  50/100 |         1 |  11.3ms
CT07A_GAP_RECEITA_FEDERAL_RECIBO_E_RENDA.pdf            | ❌ REPROVADO    |  50/100 |         1 |  10.9ms
CT07B_GAP_RECEITA_FEDERAL_MATEMATICA_PERFEITA_REDTEAM.pdf | ⚠️  GAP RFB  |  40/100 |         0 |  11.6ms
CT07C_COERENCIA_RENDIMENTOS_ISENTOS_INFLADOS.pdf        | ❌ REPROVADO    |  50/100 |         1 |  11.9ms
CT08A_APPSEC_PDF_PROTEGIDO_POR_SENHA_ENCRYPT.pdf        | ❌ REPROVADO    |  50/100 |         1 |  11.0ms
CT08B_APPSEC_PDF_PAYLOAD_JAVASCRIPT_OPENACTION.pdf      | ❌ REPROVADO    |  50/100 |         1 |  10.9ms
====================================================================================================
📊 CONSOLIDADO: Total=26 | ✅ Aprovados=3 | ❌ Reprovados=22 | ⚠️  Gap RFB (Serpro Obrigatório)=1
```

> **Notas sobre os casos aprovados no modo cego puro:**  
> \* `CT02B` (Nome divergente): O documento pertence a um titular fictício legítimo ("SILVA"). No modo cego, ele é aprovado porque é internamente íntegro. Ao passar o nome da proposta (`--expected-nome "GILSONEI DOS SANTOS"`), ele reprova imediatamente por divergência cadastral.  
> \*\* `CT03A` (Vigência 2023/2022): O documento é uma declaração real e matematicamente íntegra do ano 2023/2022. Ao passar a vigência aceita pela instituição (`--expected-exercicio 2026`), ele reprova na hora.  
> \*\*\* `CT07B`: O motor reconhece que a matemática foi perfeitamente recalculada pelo fraudador e emite o alerta mandatório de consulta à API SERPRO/RFB.

---

## 5. Proposta de Integração na Arquitetura (Pipeline de Onboarding)

A recomendação técnica é posicionar esse script como **Step 0 (Fast Pre-Flight Validator)** no pipeline de ingestão de documentos:

```
[ Upload do PDF ] ──▶ [ Step 0: Motor Forense Interno ]
                             │
                             ├──▶ [Reprovado: Whiteout, Multi-EOF, Math Error, Senha] ──▶ Rejeição Imediata (<15ms)
                             │                                                            (Sem queimar custo de API)
                             │
                             └──▶ [Aprovado / Sem Anomalias] ──▶ [ Step 1: IU Docs / OCR ]
                                                                       │
                                                                       ▼
                                                          [ Step 2: API SERPRO / RFB ]
                                                          (Se renda > R$ 100k / Alerta GAP)
```

### Principais Vantagens para o Time de Engenharia:
1. **Zero Vendor Lock-in:** Motor 100% de propriedade do banco/instituição, mantido internamente e auditável.
2. **Custo Computacional Quase Nulo:** Execução em ~11ms por requisição em memória, podendo rodar em AWS Lambda, Cloud Run ou diretamente como middleware FastAPI.
3. **Economia Financeira Direta:** Elimina gastos com APIs externas em documentos com fraudes óbvias ou arquivos com senha que travam serviços de terceiros.
4. **Segurança Cibernética Robusta:** Protege os serviços internos contra PDFs maliciosos (bombas de descompressão, payloads JS e SSRF Canary).

---

## 6. Como Testar & Validar Localmente

O script possui interface CLI completa e saída exportável em JSON estruturado para consumo em pipelines de automação/CI-CD:

```powershell
# 1. Execução de Auditoria Cega em lote na pasta de testes:
python scripts/auditar_declaracoes_irpf.py --dir arquivos_teste_irpf

# 2. Execução Cega em um arquivo avulso suspeito:
python scripts/auditar_declaracoes_irpf.py --file arquivos_teste_irpf/CT05B_MANIPULACAO_SOBREPOSICAO_WHITEOUT_CERTA.pdf

# 3. Execução Híbrida (Perícia Forense + Dados da Proposta do Cliente):
python scripts/auditar_declaracoes_irpf.py --file documento.pdf --expected-cpf "250.713.388-07" --expected-nome "GILSONEI DOS SANTOS"

# 4. Exportação direta em JSON para integração com APIs:
python scripts/auditar_declaracoes_irpf.py --file documento.pdf --json
```

---

## 7. Próximos Passos Sugeridos

1. **Empacotamento em Módulo/Microserviço:** Expor a classe `ZeroKnowledgeIRPFAuditor` como endpoint REST (`POST /api/v1/irpf/audit`) em FastAPI ou função Serverless.
2. **Integração com Telemetria SIEM:** Exportar as violações (`AuditViolation`) no padrão CEF/Syslog para monitoramento em tempo real de campanhas de fraude no Splunk / Datadog.
3. **Apresentação em Tech Review:** Demonstração prática do script rodando em lote e comparativo de resiliência versus a solução Certta.
