📢 **PLANO E ROTEIRO DE TESTES — VALIDAÇÃO DE IRPF (SEPARAÇÃO IU DOCS vs. CERTA + RED & BLUE TEAM)**

Olá, time! 👋
Estruturamos a suíte completa de testes e a massa de arquivos PDF para homologação do envio de **IRPF (Exercício 2026 / Ano-Calendário 2025)**, separando rigorosamente o escopo de validação de regras/conteúdo (**IU Docs**) do escopo de perícia forense/antifraude documental (**Certa**), com validação cruzada de **Segurança da Informação (Red Team & Blue Team)**.

---

### 📊 1. Divisão de Escopo (IU Docs vs. Certa)

| # | Funcionalidade | O que valida | IU Docs | Certa | Escopo do Teste |
| :-: | :--- | :--- | :-: | :-: | :--- |
| **1** | **Autenticidade** | Marca d'água (`PROTEGIDA POR SIGILO FISCAL`) e status da declaração | 🟠 **SIM** | 🟠 **SIM** | **Compartilhado** (`RT-01A` a `RT-01D`) |
| **2** | **Titularidade** | CPF e Nome nas bases corporativas | 🟠 **SIM** | ⚪ **NÃO** | **Exclusivo IU Docs** (`RT-02A` a `RT-02C`) |
| **3** | **Vigência** | Exercício aceito pela regra (`2026/2025`) | 🟠 **SIM** | ⚪ **NÃO** | **Exclusivo IU Docs** (`RT-03A`, `RT-03B`) |
| **4** | **Páginas** | Completude, sequência e coerência (`1 a 8`) | 🟠 **SIM** | 🟠 **SIM** | **Compartilhado** (`RT-04A` a `RT-04E`) |
| **5** | **Manipulação do arquivo** | Detecção de adulteração estrutural em arquivos | ⚪ **NÃO** | 🟠 **SIM** | **Exclusivo Certa** (`RT-05A` a `RT-05C`) |
| **6** | **Fontes e tipografias** | Elementos alterados ou inseridos artificialmente | ⚪ **NÃO** | 🟠 **SIM** | **Exclusivo Certa** (`RT-06A` a `RT-06C`) |
| **7** | **Validação na Receita Federal** | Cross-check com a Receita Federal para validação dos dados | ⚪ **NÃO** | ⚪ **NÃO** | **Gap Mapeado** (`RT-07A` a `RT-07C`) |
| **8** | **AppSec (Upload PDF)** | Proteção contra PDF com senha (`/Encrypt`) e scripts ativos (`/JS`, `/URI`) | 🛡️ **SIM** | 🛡️ **SIM** | **Segurança / AppSec** (`RT-08A`, `RT-08B`) |

---

### 📑 2. Como está organizada a Planilha Oficial (`ROTEIRO_DE_TESTE_IRPF_IUDOCS_VS_CERTA.xlsx`)

A planilha possui **4 abas** prontas para acompanhamento de QA e Segurança:

1️⃣ **Aba `1_Matriz_IUDocs_vs_Certa` (Visão Executiva):**
* Quadro comparativo das funcionalidades entre **IU Docs** e **Certa**, indicando onde cada motor atua (`SIM`/`NÃO`), quais casos de teste cobrem cada item e o resumo de risco.

2️⃣ **Aba `2_Roteiro_de_Teste_26_Casos` (Execução Passo a Passo QA):**
* Contém os **26 roteiros de teste (`RT-00` a `RT-08B`)** vinculados aos **26 arquivos PDF** gerados cirurgicamente a partir do documento original (mantendo 99,9% do texto, fontes nativas `FreeSans` e metadados originais `JasperReports 5.6.1 / iText 2.1.7` onde aplicável):
  * **Baseline (`RT-00`):** Documento original íntegro $\rightarrow$ **IU Docs: APROVA | Certa: APROVA**.
  * **Autenticidade (`RT-01A` a `RT-01D`):** Sem marca d'água (`RT-01A`), status `EM PREENCHIMENTO` (`RT-01B`), Retificadora com recibo zerado (`RT-01C`) e **Declaração Final de Espólio / Contribuinte Falecido (`RT-01D`)** $\rightarrow$ **IU Docs: REPROVA | Certa: REPROVA**.
  * **Titularidade (`RT-02A` a `RT-02C`):** CPF divergente (`250.713.388-88`), Nome divergente (`GILSONEI DOS SANTOS SILVA`) e **Inversão Dependente/Alimentando (`KAMILE VITORIA 526.161.888-64`) tentando passar como Titular (`RT-02C`)** $\rightarrow$ **IU Docs: REPROVA | Certa: APROVA**.
  * **Vigência (`RT-03A`, `RT-03B`):** Exercício expirado (`2023/2022`) e Ano-Calendário inconsistente (`2026/2023`) $\rightarrow$ **IU Docs: REPROVA | Certa: APROVA**.
  * **Páginas (`RT-04A` a `RT-04E`):** Falta da Página 7 (`RT-04A`), páginas fora de ordem (`RT-04B`), incoerência de CPF/Total entre páginas (`RT-04C`), **envio de apenas 1 página isolada (`RT-04D`)** e **"8 de 8 Falso" com Página 6 duplicada 2x sem a Página 7 (`RT-04E`)** $\rightarrow$ **IU Docs: REPROVA | Certa: REPROVA**.
  * **Manipulação do Arquivo (`RT-05A` a `RT-05C`):** Metadados `Canva/ilovepdf` + múltiplos `%%EOF`, adulteração de renda por retângulo branco sobreposto (*Whiteout*) e PDF achatado via `Print to PDF` $\rightarrow$ **IU Docs: APROVA | Certa: REPROVA**.
  * **Fontes e Tipografias (`RT-06A` a `RT-06C`):** Inserção artificial com fonte `Courier-Bold`, desalinhamento geométrico de baseline (`+3.57pt`) e injeção de texto invisível (`3 Tr` *Dual-Layer / OCR Poisoning*) $\rightarrow$ **IU Docs: APROVA | Certa: REPROVA**.
  * **Gap 7 — Validação na Receita Federal & Renda Isenta (`RT-07A` a `RT-07C`):**
    * `RT-07A`: Recibo e renda adulterados (`153.551,12`) sem recalcular o imposto da Pág. 7 $\rightarrow$ Detectável pela **Equação Tributária da Página 7**.
    * `RT-07B`: Renda adulterada (`153.551,12`) com **100% da Página 7 recalculada** (`Base: 136.796,78`, `Imposto: 26.765,33`, `Alíquota: 17,43%`, `Saldo: 25.581,68`, `Quota: 3.197,71`) usando glifos nativos $\rightarrow$ **Prova de conceito de que sem consulta na API SERPRO/Receita Federal (Item 7), ambos aprovam!**
    * `RT-07C`: **Inflação de Rendimentos Isentos e Não Tributáveis (Dividendos)** na Pág. 2 (`350.000,00`) vs. espelho em Outras Informações na Pág. 8 (`0,00`) $\rightarrow$ **IU Docs: REPROVA por incoerência Pág. 2 vs. Pág. 8**.
  * **AppSec (`RT-08A`, `RT-08B`):** PDF protegido por senha (`/Encrypt`) e PDF com payload ativo (`/OpenAction /JavaScript` e `/URI` SSRF Canary) $\rightarrow$ **Ambos BLOQUEIAM (Fail-Closed)**.

3️⃣ **Aba `3_Seguranca_Red_e_Blue_Team` (Matriz Ofensiva & Defensiva):**
* Detalha os **5 vetores de ataque (Red Team)** e as **regras de detecção e correlação SIEM/Antifraude (Blue Team)**: validação de Dígito Verificador Módulo 11 do CPF, auditoria de glifos do subset `/Widths`, bloqueio de `3 Tr` (texto invisível), fechamento da Equação Tributária na Pág. 7 e sanitização de scripts ativos no PDF.

4️⃣ **Aba `4_Baseline_Texto_Original_RFB` (Dicionário do Documento Base):**
* Referência rápida com todos os textos, seções e valores originais das **Páginas 1 a 8** da declaração base utilizada nos testes.

---

### 📂 3. Acesso aos Arquivos no SharePoint
Todos os artefatos abaixo já estão disponíveis na nossa pasta do **SharePoint**:
🔗 **[Acessar Pasta do Projeto IRPF no SharePoint — COLE O LINK AQUI]**

* 📊 **Planilha do Roteiro (`.xlsx`):** `ROTEIRO_DE_TESTE_IRPF_IUDOCS_VS_CERTA.xlsx`
* 📄 **Documentação Completa (`.md`):** `ROTEIRO_DE_TESTE_RTF_RED_BLUE_TEAM_IRPF.md`
* 📁 **Massa de Testes (26 PDFs):** Pasta `arquivos_teste_irpf/` (`CT00` até `CT08B`)
