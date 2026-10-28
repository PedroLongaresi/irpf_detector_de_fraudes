# Roteiro de Teste Funcional, Forense e de Segurança (RTF) — Envio de IRPF (IU Docs vs. Certa) com Validação Red Team & Blue Team

> **Squad Multiagente Responsável:**
> - **Agente QA (`agente_qa`)**: Roteiro de Teste Funcional (RTF), Passos de Execução, Pré-condições e Critérios de Aceite.
> - **Agente Copywriter (`agente_copywriter`)**: Fidelidade Textual 100% à Declaração Original da Receita Federal (`GILSONEI DOS SANTOS`) e Mensagens de Validação.
> - **Agente Desenvolvedor (`agente_desenvolvedor`)**: Engenharia Cirúrgica de Streams PDF (`FlateDecode` `0x78 0x9C` + `xref`) via [`SurgicalPDFBuilder`](file:///c:/Users/Longaresi/Documents/PROJETO%20IRPF/gerar_arquivos_teste_irpf.py#L32-L108).
> - **Agente de Segurança da Informação (`agente_seguranca_info` — Red Team & Blue Team)**: Simulação de Ataques de Evasão/Bypass (Red Team) e Regras de Detecção Forense, Equação Tributária, Correlação e Telemetria SIEM/Antifraude (Blue Team).

---

## 1. Visão Geral do Roteiro de Teste (RTF) e Matriz de Escopo

Este **Roteiro de Teste Funcional e Forense (RTF)** guia passo a passo a execução homologatória do fluxo de envio de **IRPF (Exercício 2026 / Ano-Calendário 2025)** separando as validações entre o motor de regras/OCR (**IU Docs**) e o motor de perícia forense de arquivos (**Certa**), conforme a matriz oficial ([imagem (10).png](file:///c:/Users/Longaresi/Documents/PROJETO%20IRPF/imagem%20(10).png)):

| # | Funcionalidade | O que valida *(Texto Original)* | IU Docs | Certa | Roteiros Associados |
| :-: | :--- | :--- | :-: | :-: | :--- |
| **0** | **Baseline (Controle Positivo)** | Documento original íntegro da Receita Federal | 🟠 **SIM** | 🟠 **SIM** | `RT-00` |
| **1** | **Autenticidade** | `Marca d'adua e status da declaração` | 🟠 **SIM** | 🟠 **SIM** | `RT-01A`, `RT-01B` |
| **2** | **Titularidade** | `CPF e nome nas bases corporativas` | 🟠 **SIM** | ⚪ **NÃO** | `RT-02A`, `RT-02B` |
| **3** | **Vigência** | `Exercício aceito pela regra` | 🟠 **SIM** | ⚪ **NÃO** | `RT-03A`, `RT-03B` |
| **4** | **Páginas** | `Completude, sequência e coerência` | 🟠 **SIM** | 🟠 **SIM** | `RT-04A`, `RT-04B`, `RT-04C` |
| **5** | **Manipulação do arquivo** | `Detecção de adulteração em arquivos` | ⚪ **NÃO** | 🟠 **SIM** | `RT-05A`, `RT-05B` |
| **6** | **Fontes e tipografias** | `Se existem elementos alterados ou inseridos artificialmente` | ⚪ **NÃO** | 🟠 **SIM** | `RT-06A`, `RT-06B` |
| **7** | **Validação na Receita Federal** | `Cross check com a receita federal para validação dos dados` | ⚪ **NÃO** | ⚪ **NÃO** | `RT-07A` *(PoC Red/Blue Team)* |

---

## 2. Pré-Condições do Ambiente de Teste (Setup QA & Blue Team)

Antes de iniciar a execução dos roteiros `RT-00` a `RT-07A`, configure na base corporativa/homologação o titular correspondente ao documento original [XXXXX-IRPF-2026-2025-origi-imagem-declaracao.pdf]:

- **Nome Cadastrado na Base Corporativa:** `XXXXXX DOS SANTOS`
- **CPF Cadastrado na Base Corporativa:** `XXX.XXX.XXX-XX`
- **Data de Nascimento:** `30/01/1977`
- **Regra de Vigência Ativa no IU Docs:** `EXERCÍCIO 2026` / `ANO-CALENDÁRIO 2025`
- **Assinatura Forense Baseline na Certa:**
  - `Creator`: `JasperReports Library version 5.6.1`
  - `Producer`: `iText 2.1.7 by 1T3XT`
  - Header de compressão `FlateDecode`: `0x78 0x9C` (padrão `java.util.zip.Deflater`)
  - Dicionário de Fontes permitido por página: `/F1` (`Helvetica`), `/F2` (`QWIOTU+FreeSansBold`), `/F3` (`ZBXMLK+FreeSans`).

---

## 3. Roteiro de Teste Passo a Passo (`RT-00` a `RT-07A`) com Validação Red Team & Blue Team

---

### `RT-00` — Baseline de Controle Positivo (Declaração Original Íntegra)
- **Objetivo:** Validar que o documento original autêntico é aprovado sem falsos positivos tanto no **IU Docs** quanto na **Certa**.
- **Arquivo de Teste (PDF):** [CT00_ORIGINAL_VALIDO_IRPF_2026_2025.pdf](file:///c:/Users/Longaresi/Documents/PROJETO%20IRPF/arquivos_teste_irpf/CT00_ORIGINAL_VALIDO_IRPF_2026_2025.pdf) ([Versão `.rtf`](file:///c:/Users/Longaresi/Documents/PROJETO%20IRPF/arquivos_teste_irpf_rtf/CT00_ORIGINAL_VALIDO_IRPF_2026_2025.rtf))
- **Passo a Passo de Execução:**
  1. Iniciar proposta/envio de documento para o titular `GILSONEI DOS SANTOS` (`CPF: 250.713.388-07`).
  2. Realizar upload do arquivo `CT00_ORIGINAL_VALIDO_IRPF_2026_2025.pdf`.
  3. Inspecionar o retorno individual da API/painel do **IU Docs** e da **Certa**.
- **Resultado Esperado:**
  - **IU Docs:** ✅ `APROVADO` (Marca d'água `PROTEGIDA POR SIGILO FISCAL` presente, Status `Declaração de Ajuste Anual Original`, Recibo `11.26.13.14.00-02`, CPF `250.713.388-07`, Nome `GILSONEI DOS SANTOS`, Vigência `2026/2025`, 8 páginas coerentes e Total `103.551,12`).
  - **Certa:** ✅ `APROVADO` (Único `%%EOF`, metadados `JasperReports 5.6.1 / iText 2.1.7`, fontes nativas `FreeSans` sem objetos sobrepostos).
- **Validação de Segurança (Red Team vs. Blue Team):**
  - 🔴 **Tática Red Team:** *Replay Attack* — submeter este mesmo PDF autêntico em múltiplas contas ou propostas diferentes.
  - 🔵 **Controle Blue Team:** Registrar o hash `SHA-256` do arquivo + tupla `(CPF, Exercício, Nº Recibo 11.26.13.14.00-02)` para bloquear reutilização cruzada em contas distintas (`INFO: IRPF_BASELINE_VALID`).

---

### `RT-01A` — Funcionalidade 1: Autenticidade (Supressão da Marca d'Água)
- **Objetivo:** Validar se **IU Docs** e **Certa** reprovam declaração sem a marca d'água oficial `PROTEGIDA POR SIGILO FISCAL`.
- **Arquivo de Teste (PDF):** [CT01A_AUTENTICIDADE_SEM_MARCA_DAGUA.pdf](file:///c:/Users/Longaresi/Documents/PROJETO%20IRPF/arquivos_teste_irpf/CT01A_AUTENTICIDADE_SEM_MARCA_DAGUA.pdf) ([Versão `.rtf`](file:///c:/Users/Longaresi/Documents/PROJETO%20IRPF/arquivos_teste_irpf_rtf/CT01A_AUTENTICIDADE_SEM_MARCA_DAGUA.rtf))
- **Texto Mantido vs. Alteração:** 100% do texto das 8 páginas foi mantido idêntico ao original; apenas o comando gráfico `/img1 Do` a `/img15 Do` foi substituído por `q Q`.
- **Passo a Passo de Execução:**
  1. Submeter `CT01A_AUTENTICIDADE_SEM_MARCA_DAGUA.pdf` no fluxo de validação.
  2. Verificar o alerta de **Autenticidade** no **IU Docs** e na **Certa**.
- **Resultado Esperado:**
  - **IU Docs:** ❌ `REPROVADO` (*"Falha de Autenticidade: Marca d'água oficial 'PROTEGIDA POR SIGILO FISCAL' ausente"*).
  - **Certa:** ❌ `REPROVADO` (*"Falha de Autenticidade: Supressão da camada de marca d'água padrão do template RFB"*).
- **Validação de Segurança (Red Team vs. Blue Team):**
  - 🔴 **Tática Red Team:** Remover apenas o operador `Do` no content stream mantendo os objetos de imagem `/img1` a `/img15` no dicionário `/Resources/XObject` para enganar validadores que só checam a existência do XObject no PDF.
  - 🔵 **Controle Blue Team:** A **Certa** deve auditar se cada XObject declarado em `/Resources/XObject` possui invocação ativa `Do` dentro do stream da respectiva página (`HIGH: WATERMARK_SUPPRESSION_DETECTED`).

---

### `RT-01B` — Funcionalidade 1: Autenticidade (Declaração com Status "EM PREENCHIMENTO" / Rascunho)
- **Objetivo:** Validar se **IU Docs** e **Certa** reprovam declarações não transmitidas (rascunho gerado antes do envio à RFB).
- **Arquivo de Teste (PDF):** [CT01B_AUTENTICIDADE_STATUS_RASCUNHO.pdf](file:///c:/Users/Longaresi/Documents/PROJETO%20IRPF/arquivos_teste_irpf/CT01B_AUTENTICIDADE_STATUS_RASCUNHO.pdf) ([Versão `.rtf`](file:///c:/Users/Longaresi/Documents/PROJETO%20IRPF/arquivos_teste_irpf_rtf/CT01B_AUTENTICIDADE_STATUS_RASCUNHO.rtf))
- **Texto Mantido vs. Alteração:** Marca d'água alterada para `EM PREENCHIMENTO`, Tipo de declaração alterado para `Declaração EM PREENCHIMENTO` e linha de recibo alterada para `Declaração em preenchimento - Recibo de entrega não gerado`.
- **Passo a Passo de Execução:**
  1. Submeter `CT01B_AUTENTICIDADE_STATUS_RASCUNHO.pdf` no fluxo de validação.
  2. Verificar a reprovação por status inválido em ambos os motores.
- **Resultado Esperado:**
  - **IU Docs:** ❌ `REPROVADO` (*"Falha de Autenticidade: A declaração encontra-se com status 'EM PREENCHIMENTO' e sem recibo de entrega"*).
  - **Certa:** ❌ `REPROVADO` (*"Falha de Autenticidade: Marca d'água e status incompatíveis com declaração transmitida"*).
- **Validação de Segurança (Red Team vs. Blue Team):**
  - 🔴 **Tática Red Team:** Preencher renda fictícia no PGD da Receita Federal, imprimir a imagem da declaração antes de transmitir (para não cometer crime de declaração falsa perante o Fisco) e enviá-la ao banco.
  - 🔵 **Controle Blue Team:** Bloqueio imediato por regex textual (`EM PREENCHIMENTO`) no **IU Docs** combinado com verificação de camada de marca d'água na **Certa** (`MEDIUM: UNTRANSMITTED_DRAFT_SUBMISSION`).

---

### `RT-02A` — Funcionalidade 2: Titularidade — Exclusivo IU Docs (CPF Divergente da Base Corporativa)
- **Objetivo:** Comprovar a separação de escopo: o **IU Docs DEVE REPROVAR** por divergência de CPF nas bases corporativas, enquanto a **Certa DEVE APROVAR** (pois a Certa não valida titularidade e o arquivo foi gerado cirurgicamente sem rastro forense).
- **Arquivo de Teste (PDF):** [CT02A_TITULARIDADE_CPF_DIVERGENTE_IUDOCS.pdf](file:///c:/Users/Longaresi/Documents/PROJETO%20IRPF/arquivos_teste_irpf/CT02A_TITULARIDADE_CPF_DIVERGENTE_IUDOCS.pdf) ([Versão `.rtf`](file:///c:/Users/Longaresi/Documents/PROJETO%20IRPF/arquivos_teste_irpf_rtf/CT02A_TITULARIDADE_CPF_DIVERGENTE_IUDOCS.rtf))
- **Texto Mantido vs. Alteração:** Todo o texto original foi mantido, alterando apenas o CPF `250.713.388-07` para `250.713.388-88` nas 8 páginas (usando o glifo nativo `8` já existente nas fontes `/F2` e `/F3`).
- **Passo a Passo de Execução:**
  1. Na proposta do titular `250.713.388-07`, enviar o arquivo `CT02A_TITULARIDADE_CPF_DIVERGENTE_IUDOCS.pdf` (que contém o CPF `250.713.388-88`).
  2. Confirmar que o **IU Docs** reprova na regra **2 - Titularidade** e que a **Certa** aprova o documento.
- **Resultado Esperado:**
  - **IU Docs:** ❌ `REPROVADO` (*"Divergência de Titularidade: O CPF 250.713.388-88 no documento diverge do CPF do titular nas bases corporativas"*).
  - **Certa:** ✅ `APROVADO` (*Escopo de Titularidade inativo na Certa; estrutura binária e fontes nativas íntegras*).
- **Validação de Segurança (Red Team vs. Blue Team):**
  - 🔴 **Tática Red Team:** Tomar a declaração verdadeira de um terceiro de alta renda e alterar cirurgicamente o CPF no stream PDF, ou enviar o documento de outra pessoa esperando falha no batimento cadastral.
  - 🔵 **Controle Blue Team:**
    1. Batimento estrito `CPF_Extraído == CPF_Sessão/Proposta` no **IU Docs**.
    2. Validação matemática do **Módulo 11 (Dígito Verificador do CPF)**: o CPF `250.713.388-88` possui DV inválido (o DV correto para `250.713.388` é `-07`), o que permite ao Blue Team classificar imediatamente como adulteração intencional (`HIGH: IDENTITY_MISMATCH_OR_INVALID_CPF_MOD11`).

---

### `RT-02B` — Funcionalidade 2: Titularidade — Exclusivo IU Docs (Nome Divergente da Base Corporativa)
- **Objetivo:** Comprovar que o **IU Docs DEVE REPROVAR** quando o nome no documento diverge do nome registrado nas bases corporativas para aquele CPF, enquanto a **Certa DEVE APROVAR**.
- **Arquivo de Teste (PDF):** [CT02B_TITULARIDADE_NOME_DIVERGENTE_IUDOCS.pdf](file:///c:/Users/Longaresi/Documents/PROJETO%20IRPF/arquivos_teste_irpf/CT02B_TITULARIDADE_NOME_DIVERGENTE_IUDOCS.pdf) ([Versão `.rtf`](file:///c:/Users/Longaresi/Documents/PROJETO%20IRPF/arquivos_teste_irpf_rtf/CT02B_TITULARIDADE_NOME_DIVERGENTE_IUDOCS.rtf))
- **Texto Mantido vs. Alteração:** Mantém `CPF: 250.713.388-07`, alterando apenas `GILSONEI DOS SANTOS` para `GILSONEI DOS SANTOS SILVA` nas 8 páginas (todos os caracteres `S, I, L, V, A` pertencem ao subset original da fonte `QWIOTU+FreeSansBold`).
- **Passo a Passo de Execução:**
  1. Submeter `CT02B_TITULARIDADE_NOME_DIVERGENTE_IUDOCS.pdf` para o titular `GILSONEI DOS SANTOS`.
  2. Verificar a reprovação exclusiva no **IU Docs** e aprovação na **Certa**.
- **Resultado Esperado:**
  - **IU Docs:** ❌ `REPROVADO` (*"Divergência de Titularidade: O nome 'GILSONEI DOS SANTOS SILVA' diverge do cadastro nas bases corporativas"*).
  - **Certa:** ✅ `APROVADO` (*Escopo de Titularidade inativo na Certa; arquivo forense íntegro*).
- **Validação de Segurança (Red Team vs. Blue Team):**
  - 🔴 **Tática Red Team:** Reutilizar caracteres já presentes na tabela de glifos da fonte embarcada (`FreeSansBold`) para alterar o nome do titular sem precisar embutir uma nova fonte no PDF.
  - 🔵 **Controle Blue Team:** Comparação exata e fonética do nome completo contra a base corporativa/Receita no **IU Docs** (`MEDIUM: HOLDER_NAME_MISMATCH`).

---

### `RT-03A` — Funcionalidade 3: Vigência — Exclusivo IU Docs (Exercício Expirado 2023 / Ano-Calendário 2022)
- **Objetivo:** Comprovar a separação de escopo: o **IU Docs DEVE REPROVAR** por exercício fora da regra de vigência (`2023/2022`), enquanto a **Certa DEVE APROVAR**.
- **Arquivo de Teste (PDF):** [CT03A_VIGENCIA_EXERCICIO_EXPIRADO_2023_2022_IUDOCS.pdf](file:///c:/Users/Longaresi/Documents/PROJETO%20IRPF/arquivos_teste_irpf/CT03A_VIGENCIA_EXERCICIO_EXPIRADO_2023_2022_IUDOCS.pdf) ([Versão `.rtf`](file:///c:/Users/Longaresi/Documents/PROJETO%20IRPF/arquivos_teste_irpf_rtf/CT03A_VIGENCIA_EXERCICIO_EXPIRADO_2023_2022_IUDOCS.rtf))
- **Texto Mantido vs. Alteração:** Altera `EXERCÍCIO 2026` / `ANO-CALENDÁRIO 2025` para `EXERCÍCIO 2023` / `ANO-CALENDÁRIO 2022` nas 8 páginas e referências da Página 1.
- **Passo a Passo de Execução:**
  1. Submeter `CT03A_VIGENCIA_EXERCICIO_EXPIRADO_2023_2022_IUDOCS.pdf`.
  2. Confirmar reprovação na regra **3 - Vigência** pelo **IU Docs** e aprovação pela **Certa**.
- **Resultado Esperado:**
  - **IU Docs:** ❌ `REPROVADO` (*"Vigência Inválida: O exercício informado (EXERCÍCIO 2023 / ANO-CALENDÁRIO 2022) não é aceito pela regra vigente"*).
  - **Certa:** ✅ `APROVADO` (*Escopo de Vigência inativo na Certa*).
- **Validação de Segurança (Red Team vs. Blue Team):**
  - 🔴 **Tática Red Team:** Enviar declaração de anos anteriores em que o proponente possuía maior capacidade financeira.
  - 🔵 **Controle Blue Team:** Além do bloqueio de vigência no **IU Docs**, a correlação Blue Team detecta **Paradoxo Temporal Forense**: o texto declara `EXERCÍCIO 2023`, mas a Evolução Patrimonial na Pág. 8 cita `31/12/2024` e `31/12/2025` e o metadado `/CreationDate` é de `2026` (`MEDIUM: EXPIRED_TAX_YEAR_OR_TEMPORAL_PARADOX`).

---

### `RT-03B` — Funcionalidade 3: Vigência — Exclusivo IU Docs (Incoerência Exercício 2026 vs. Ano-Calendário 2023)
- **Objetivo:** Validar se o **IU Docs** reprova declaração com par temporal impossível (`EXERCÍCIO 2026` com `ANO-CALENDÁRIO 2023`), enquanto a **Certa** aprova por não validar regra de vigência.
- **Arquivo de Teste (PDF):** [CT03B_VIGENCIA_ANO_CALENDARIO_INCONSISTENTE_IUDOCS.pdf](file:///c:/Users/Longaresi/Documents/PROJETO%20IRPF/arquivos_teste_irpf/CT03B_VIGENCIA_ANO_CALENDARIO_INCONSISTENTE_IUDOCS.pdf) ([Versão `.rtf`](file:///c:/Users/Longaresi/Documents/PROJETO%20IRPF/arquivos_teste_irpf_rtf/CT03B_VIGENCIA_ANO_CALENDARIO_INCONSISTENTE_IUDOCS.rtf))
- **Passo a Passo de Execução:**
  1. Submeter `CT03B_VIGENCIA_ANO_CALENDARIO_INCONSISTENTE_IUDOCS.pdf`.
  2. Verificar reprovação no **IU Docs** e aprovação na **Certa**.
- **Resultado Esperado:**
  - **IU Docs:** ❌ `REPROVADO` (*"Vigência Inválida: Inconsistência entre Exercício (2026) e Ano-Calendário (2023)"*).
  - **Certa:** ✅ `APROVADO`.
- **Validação de Segurança (Red Team vs. Blue Team):**
  - 🔴 **Tática Red Team:** Adulterar apenas o ano de `EXERCÍCIO` para o ano atual esquecendo de atualizar o `ANO-CALENDÁRIO` (ou vice-versa).
  - 🔵 **Controle Blue Team:** Regra invariante `Exercicio - Ano_Calendario == 1` em todas as páginas (`HIGH: IMPOSSIBLE_TAX_CALENDAR_PAIR`).

---

### `RT-04A` — Funcionalidade 4: Páginas — Compartilhado (Incompletude: Remoção da Página 7 - Resumo)
- **Objetivo:** Validar se **IU Docs** e **Certa** reprovam declaração incompleta (7 páginas físicas no arquivo, faltando a `Página 7 de 8`).
- **Arquivo de Teste (PDF):** [CT04A_PAGINAS_INCOMPLETO_FALTA_PAGINA_7.pdf](file:///c:/Users/Longaresi/Documents/PROJETO%20IRPF/arquivos_teste_irpf/CT04A_PAGINAS_INCOMPLETO_FALTA_PAGINA_7.pdf) ([Versão `.rtf`](file:///c:/Users/Longaresi/Documents/PROJETO%20IRPF/arquivos_teste_irpf_rtf/CT04A_PAGINAS_INCOMPLETO_FALTA_PAGINA_7.rtf))
- **Passo a Passo de Execução:**
  1. Submeter `CT04A_PAGINAS_INCOMPLETO_FALTA_PAGINA_7.pdf`.
  2. Verificar reprovação em **IU Docs** e **Certa** na funcionalidade **4 - Páginas**.
- **Resultado Esperado:**
  - **IU Docs:** ❌ `REPROVADO` (*"Inconsistência de Páginas: Documento incompleto (7 de 8 páginas; ausência da Página 7 - Resumo)"*).
  - **Certa:** ❌ `REPROVADO` (*"Inconsistência de Páginas: Quebra de completude e salto de paginação"*).
- **Validação de Segurança (Red Team vs. Blue Team):**
  - 🔴 **Tática Red Team:** Remover páginas específicas (como Bens e Direitos, Dívidas e Ônus Reais ou Resumo do Imposto a Pagar) para ocultar alavancagem ou inconsistência fiscal.
  - 🔵 **Controle Blue Team:** Além da contagem `Página X de 8`, a análise binária da **Certa** detecta que o objeto `29 0 obj` (Página 7) foi desvinculado do array `/Kids`, mas permanece órfão dentro da tabela `xref` (`HIGH: INTENTIONAL_PAGE_REMOVAL`).

---

### `RT-04B` — Funcionalidade 4: Páginas — Compartilhado (Quebra de Sequência: Página 3 antes da Página 2)
- **Objetivo:** Validar se **IU Docs** e **Certa** reprovam documento com páginas fora da ordem sequencial (`1, 3, 2, 4, 5, 6, 7, 8`).
- **Arquivo de Teste (PDF):** [CT04B_PAGINAS_FORA_DE_SEQUENCIA.pdf](file:///c:/Users/Longaresi/Documents/PROJETO%20IRPF/arquivos_teste_irpf/CT04B_PAGINAS_FORA_DE_SEQUENCIA.pdf) ([Versão `.rtf`](file:///c:/Users/Longaresi/Documents/PROJETO%20IRPF/arquivos_teste_irpf_rtf/CT04B_PAGINAS_FORA_DE_SEQUENCIA.rtf))
- **Passo a Passo de Execução:**
  1. Submeter `CT04B_PAGINAS_FORA_DE_SEQUENCIA.pdf`.
  2. Verificar reprovação por quebra de sequência em ambos os motores.
- **Resultado Esperado:**
  - **IU Docs:** ❌ `REPROVADO` (*"Inconsistência de Páginas: Quebra na sequência lógica das páginas (Página 3 de 8 antecede a Página 2 de 8)"*).
  - **Certa:** ❌ `REPROVADO` (*"Inconsistência de Páginas: Reordenação anômala na árvore /Pages"*).
- **Validação de Segurança (Red Team vs. Blue Team):**
  - 🔴 **Tática Red Team:** Extrair e remontar páginas do PDF em ferramentas de *split & merge*, errando a ordenação ou tentando confundir parsers posicionais de OCR.
  - 🔵 **Controle Blue Team:** Verificação estritamente crescente do rodapé (`1..N`) no **IU Docs** e verificação da monotonicidade dos IDs de objetos em `/Kids` (`[1, 9, 13, 17, 21, 25, 29, 33]`) na **Certa** (`MEDIUM: PAGE_TREE_REORDERING`).

---

### `RT-04C` — Funcionalidade 4: Páginas — Compartilhado (Incoerência de Cabeçalho na Pág. 2 e Resumo na Pág. 7)
- **Objetivo:** Validar se **IU Docs** e **Certa** detectam enxerto/incoerência entre páginas (CPF `250.713.388-55` na Página 2 vs `250.713.388-07` nas demais, e Total `203.551,12` na Página 7 vs `103.551,12` na Página 2).
- **Arquivo de Teste (PDF):** [CT04C_PAGINAS_INCOERENCIA_CABECALHO_E_RESUMO.pdf](file:///c:/Users/Longaresi/Documents/PROJETO%20IRPF/arquivos_teste_irpf/CT04C_PAGINAS_INCOERENCIA_CABECALHO_E_RESUMO.pdf) ([Versão `.rtf`](file:///c:/Users/Longaresi/Documents/PROJETO%20IRPF/arquivos_teste_irpf_rtf/CT04C_PAGINAS_INCOERENCIA_CABECALHO_E_RESUMO.rtf))
- **Passo a Passo de Execução:**
  1. Submeter `CT04C_PAGINAS_INCOERENCIA_CABECALHO_E_RESUMO.pdf`.
  2. Confirmar reprovação por incoerência entre páginas em ambos os sistemas.
- **Resultado Esperado:**
  - **IU Docs:** ❌ `REPROVADO` (*"Incoerência entre Páginas: Divergência de CPF na Página 2 e divergência contábil entre a soma de rendimentos da Página 2 (103.551,12) e o Resumo da Página 7 (203.551,12)"*).
  - **Certa:** ❌ `REPROVADO` (*"Incoerência entre Páginas: Quebra de consistência nos cabeçalhos e totalizadores do documento"*).
- **Validação de Segurança (Red Team vs. Blue Team):**
  - 🔴 **Tática Red Team:** *Ataque "Frankenstein"* — substituir apenas a página de Resumo (Pág. 7) ou a página de Rendimentos (Pág. 2) por outra adulterada.
  - 🔵 **Controle Blue Team:** Invariância de cabeçalho (`CPF + Nome + Exercício`) em todas as $N$ páginas e reconciliação contábil cruzada (`CRITICAL: CROSS_PAGE_ACCOUNTING_OR_CPF_TAMPERING`).

---

### `RT-05A` — Funcionalidade 5: Manipulação do Arquivo — Exclusivo Certa (Incremental Update com Metadados Oficiais RFB)
- **Objetivo:** Comprovar que, mesmo quando o fraudador preserva ou falsifica os metadados oficiais da Receita Federal (`JasperReports 5.6.1 / iText 2.1.7`), a **Certa DEVE REPROVAR** a estrutura de *Incremental Update* (múltiplos `%%EOF`), enquanto o **IU Docs APROVA**.
- **Arquivo de Teste (PDF):** [CT05A_MANIPULACAO_METADADOS_E_INCREMENTAL_CERTA.pdf](file:///c:/Users/Longaresi/Documents/PROJETO%20IRPF/arquivos_teste_irpf/CT05A_MANIPULACAO_METADADOS_E_INCREMENTAL_CERTA.pdf) ([Versão `.rtf`](file:///c:/Users/Longaresi/Documents/PROJETO%20IRPF/arquivos_teste_irpf_rtf/CT05A_MANIPULACAO_METADADOS_E_INCREMENTAL_CERTA.rtf))
- **Passo a Passo de Execução:**
  1. Submeter `CT05A_MANIPULACAO_METADADOS_E_INCREMENTAL_CERTA.pdf`.
  2. Confirmar que o arquivo **PASSA no teste de metadados da Certa** (metadados oficiais RFB) e é avaliado quanto à presença de blocos `xref` incrementais.
- **Resultado Esperado:**
  - **IU Docs:** ✅ `APROVADO` (*Texto e regras de negócio intactos*).
  - **Certa:** ❌ `REPROVADO` (*"Manipulação do Arquivo Detectada: Estrutura de atualização incremental (múltiplos %%EOF / /Prev) detectada no arquivo"*).
- **Validação de Segurança (Red Team vs. Blue Team):**
  - 🔴 **Tática Red Team:** Salvar atualizações incrementais preservando o dicionário `/Info` oficial para tentar burlar regras superficiais de metadados.
  - 🔵 **Controle Blue Team:** Proibição estrita de `Incremental Updates` (`count(%%EOF) == 1`) na **Certa** (`HIGH: INCREMENTAL_UPDATE_DETECTED`).

---

### `RT-05B` — Funcionalidade 5: Manipulação do Arquivo — Exclusivo Certa (Adulteração de Renda por Sobreposição "Whiteout")
- **Objetivo:** Comprovar que a **Certa DEVE REPROVAR** adulteração de valores financeiros feita com retângulo branco sobreposto (*Whiteout* de `31.134,89` para `81.134,89` na Pág. 1 e Total `153.551,12` nas Págs. 2 e 7) mesmo mantendo metadados oficiais RFB (`JasperReports 5.6.1 / iText 2.1.7`), enquanto o **IU Docs APROVA**.
- **Arquivo de Teste (PDF):** [CT05B_MANIPULACAO_SOBREPOSICAO_WHITEOUT_CERTA.pdf](file:///c:/Users/Longaresi/Documents/PROJETO%20IRPF/arquivos_teste_irpf/CT05B_MANIPULACAO_SOBREPOSICAO_WHITEOUT_CERTA.pdf) ([Versão `.rtf`](file:///c:/Users/Longaresi/Documents/PROJETO%20IRPF/arquivos_teste_irpf_rtf/CT05B_MANIPULACAO_SOBREPOSICAO_WHITEOUT_CERTA.rtf))
- **Passo a Passo de Execução:**
  1. Submeter `CT05B_MANIPULACAO_SOBREPOSICAO_WHITEOUT_CERTA.pdf`.
  2. Confirmar aprovação no teste de metadados e reprovação da **Certa** pela detecção do objeto retangular branco (`1 1 1 rg 214 157 46 11 re f`) ocultando o texto original `(31.134,89)Tj`.
- **Resultado Esperado:**
  - **IU Docs:** ✅ `APROVADO` (*Somas superficiais batem*).
  - **Certa:** ❌ `REPROVADO` (*"Manipulação do Arquivo Detectada: Adulteração por sobreposição gráfica (Whiteout) ocultando valor original sob camada retangular"*).
- **Validação de Segurança (Red Team vs. Blue Team):**
  - 🔴 **Tática Red Team:** Cobrir o valor verdadeiro de salário com uma caixa branca e preservar os metadados oficiais do emissor para passar na checagem de origem.
  - 🔵 **Controle Blue Team:** Detecção de interseção espacial (*Bounding Box Collision*) entre operadores de texto `Tj` e primitivas `re f` na **Certa** (`CRITICAL: WHITEOUT_OVERLAY_FRAUD`).

---

### `RT-06A` — Funcionalidade 6: Fontes e Tipografias — Exclusivo Certa (Inserção Artificial com Fonte `Courier-Bold`)
- **Objetivo:** Comprovar a separação de escopo: o **IU Docs DEVE APROVAR** (pois todos os textos e valores numéricos são idênticos ao original), enquanto a **Certa DEVE REPROVAR** ao detectar a fonte artificial `/F4` (`Courier-Bold`, `9.5 Tf`) nos valores `31.134,89` (Pág. 1) e `36.000,00` (Pág. 2).
- **Arquivo de Teste (PDF):** [CT06A_FONTES_TIPOGRAFIA_DIVERGENTE_COURIER_CERTA.pdf](file:///c:/Users/Longaresi/Documents/PROJETO%20IRPF/arquivos_teste_irpf/CT06A_FONTES_TIPOGRAFIA_DIVERGENTE_COURIER_CERTA.pdf) ([Versão `.rtf`](file:///c:/Users/Longaresi/Documents/PROJETO%20IRPF/arquivos_teste_irpf_rtf/CT06A_FONTES_TIPOGRAFIA_DIVERGENTE_COURIER_CERTA.rtf))
- **Passo a Passo de Execução:**
  1. Submeter `CT06A_FONTES_TIPOGRAFIA_DIVERGENTE_COURIER_CERTA.pdf`.
  2. Confirmar aprovação no **IU Docs** e reprovação na **Certa** no item **6 - Fontes e tipografias**.
- **Resultado Esperado:**
  - **IU Docs:** ✅ `APROVADO` (*IU Docs não valida fontes/tipografias*).
  - **Certa:** ❌ `REPROVADO` (*"Anomalia Tipográfica: Elemento inserido artificialmente com fonte divergente (Courier-Bold /F4) do padrão nativo da Receita Federal (ZBXMLK+FreeSans)"*).
- **Validação de Segurança (Red Team vs. Blue Team):**
  - 🔴 **Tática Red Team:** Editar um número no PDF limpando os metadados `/Info`, porém utilizando uma fonte do sistema (`Courier`, `Arial`, `Times-Roman`, `Calibri`) por não conseguir reconstruir o subset TrueType embarcado pelo JasperReports.
  - 🔵 **Controle Blue Team:** Auditoria estrita do dicionário `/Resources/Font` na **Certa**, bloqueando qualquer página que declare mais que as 3 fontes nativas (`/F1`, `/F2`, `/F3`) (`HIGH: INTRUDER_FONT_INJECTION`).

---

### `RT-06B` — Funcionalidade 6: Fontes e Tipografias — Exclusivo Certa (Desalinhamento de Baseline e Distorção de Escala)
- **Objetivo:** Comprovar que a **Certa DEVE REPROVAR** quando o fraudador utiliza a própria fonte nativa `/F3` (`ZBXMLK+FreeSans`), mas erra o alinhamento geométrico (`Tm` deslocado verticalmente em `+3.57pt`, escala distorcida `1.18 0 0 1.25` e tamanho `10 Tf` em vez de `8 Tf`), enquanto o **IU Docs DEVE APROVAR**.
- **Arquivo de Teste (PDF):** [CT06B_FONTES_DESALINHAMENTO_E_ESCALA_CERTA.pdf](file:///c:/Users/Longaresi/Documents/PROJETO%20IRPF/arquivos_teste_irpf/CT06B_FONTES_DESALINHAMENTO_E_ESCALA_CERTA.pdf) ([Versão `.rtf`](file:///c:/Users/Longaresi/Documents/PROJETO%20IRPF/arquivos_teste_irpf_rtf/CT06B_FONTES_DESALINHAMENTO_E_ESCALA_CERTA.rtf))
- **Passo a Passo de Execução:**
  1. Submeter `CT06B_FONTES_DESALINHAMENTO_E_ESCALA_CERTA.pdf`.
  2. Confirmar aprovação no **IU Docs** e reprovação na **Certa** no item **6 - Fontes e tipografias**.
- **Resultado Esperado:**
  - **IU Docs:** ✅ `APROVADO` (*Texto extraído permanece inalterado*).
  - **Certa:** ❌ `REPROVADO` (*"Anomalia Tipográfica: Desalinhamento de baseline (y-offset +3.57pt) e distorção de escala na matriz de texto Tm"*).
- **Validação de Segurança (Red Team vs. Blue Team):**
  - 🔴 **Tática Red Team:** Reutilizar a fonte nativa `/F3` para escapar do filtro de nome de fonte, mas posicionar o texto manualmente com escala ou coordenada `Y` ligeiramente fora do grid do JasperReports.
  - 🔵 **Controle Blue Team:** Verificação de matriz unitária (`1 0 0 1 X Y Tm`), tamanho constante (`8 Tf`) e colinearidade horizontal (`Y_valor == Y_fonte_pagadora = 159.28`) na **Certa** (`HIGH: TYPOGRAPHIC_GEOMETRY_ANOMALY`).

---

### `RT-07A` — Funcionalidade 7: Validação na Receita Federal — Prova de Conceito Red Team & Mitigação Blue Team
- **Objetivo:** Demonstrar na prática o **Ponto Cego Compartilhado (Item 7 Inativo em Ambos)** e validar os controles compensatórios do **Blue Team**.
- **Arquivo de Teste (PDF):** [CT07A_GAP_RECEITA_FEDERAL_RECIBO_E_RENDA_NAO_AUDITADOS_RFB.pdf](file:///c:/Users/Longaresi/Documents/PROJETO%20IRPF/arquivos_teste_irpf/CT07A_GAP_RECEITA_FEDERAL_RECIBO_E_RENDA_NAO_AUDITADOS_RFB.pdf) ([Versão `.rtf`](file:///c:/Users/Longaresi/Documents/PROJETO%20IRPF/arquivos_teste_irpf_rtf/CT07A_GAP_RECEITA_FEDERAL_RECIBO_E_RENDA_NAO_AUDITADOS_RFB.rtf))
- **Construção Red Team do Arquivo `CT-07A`:**
  - Editado cirurgicamente dentro do stream `FlateDecode` com compressão `0x78 0x9C` idêntica ao `iText 2.1.7`, mesma fonte `/F3` (`ZBXMLK+FreeSans`), mesma coordenada `1 0 0 1 217.42 159.28 Tm /F3 8 Tf`, único `xref` limpo e metadados originais `JasperReports 5.6.1 / iText 2.1.7`.
  - **Adulterações Furtivas:** Nº do Recibo alterado para `99.88.77.66.55-00`, Rendimento na Prefeitura de Arandu elevado de `31.134,89` para `81.134,89` e Total elevado de `103.551,12` para `153.551,12` nas Páginas 2 e 7.
- **Passo a Passo de Execução:**
  1. Submeter `CT07A_GAP_RECEITA_FEDERAL_RECIBO_E_RENDA_NAO_AUDITADOS_RFB.pdf` ao **IU Docs** e à **Certa**.
  2. Registrar que, sem o **Item 7 (Cross check com a Receita Federal)** e sem validação da equação tributária completa, **ambos os sistemas aprovam o arquivo adulterado** (Falso Negativo Crítico).
  3. Executar a bateria de **Controles Compensatórios Blue Team** descrita abaixo para interceptar a fraude:
- **Controles Compensatórios Blue Team (Como Detectar o `CT-07A`):**
  1. 🔵 **Auditoria da Equação Tributária na Página 7 (IU Docs Upgrade):**
     - No `CT-07A`, o Total de Rendimentos subiu para `153.551,12` e o Desconto Simplificado é `16.754,34`.
     - Logo, a **Base de Cálculo** obrigatória seria $153.551,12 - 16.754,34 = \mathbf{136.796,78}$, mas o documento exibe `86.796,78`!
     - O **Imposto Devido** obrigatório seria $(136.796,78 \times 27,5\%) - 10.853,78 = \mathbf{26.765,33}$, mas o documento exibe `13.015,33`!
     - A **Alíquota Efetiva** deveria ser $26.765,33 / 153.551,12 = \mathbf{17,43\%}$, mas o documento exibe `12,56%`!
  2. 🔵 **Proporcionalidade Rendimento vs. IRRF / Previdência / 13º Salário (Página 1):**
     - O rendimento na Prefeitura Municipal de Arandu saltou para `81.134,89`, porém o `13º salário` permaneceu `2.112,55` e o `IRRF` permaneceu `88,12` (estatisticamente impossível para um servidor municipal com R$ 81 mil tributáveis anuais).
  3. 🔵 **Auditoria de Glifos Órfãos / Tabela `/Widths` na Fonte Embarcada (Certa Upgrade):**
     - Na Página 1 do `CT-07A`, o caractere `'9'` utilizado em `99.88.77.66.55-00` e os caracteres originais substituídos deixam discrepâncias entre o histograma de caracteres do stream e o subset TrueType `ZBXMLK+FreeSans`.
  4. 🔵 **Integração Definitiva (Ativação do Item 7):**
     - Consulta automatizada do protocolo `11.26.13.14.00-02` vs `99.88.77.66.55-00` via API **Conecta gov.br / SERPRO** (`CRITICAL: STEALTH_STREAM_TAMPERING_MATH_MISMATCH`).

---

## 4. Novos Cenários Identificados no Pente-Fino do Agente de Segurança (`RT-01C`, `RT-05C`, `RT-06C`, `RT-07B`, `RT-08A`, `RT-08B`)

Após a revisão crítica do **Agente de Segurança da Informação (`agente_seguranca_info`)**, foram adicionados **6 novos cenários e arquivos de teste** (elevando a suíte para **21 arquivos PDF** e **21 arquivos RTF**):

### `RT-01C` — Funcionalidade 1: Autenticidade — Golpe da "Retificadora Oportunista" Sem Recibo Válido
- **Arquivo de Teste (PDF):** [CT01C_AUTENTICIDADE_RETIFICADORA_SEM_RECIBO_VALIDO.pdf](file:///c:/Users/Longaresi/Documents/PROJETO%20IRPF/arquivos_teste_irpf/CT01C_AUTENTICIDADE_RETIFICADORA_SEM_RECIBO_VALIDO.pdf) ([Versão `.rtf`](file:///c:/Users/Longaresi/Documents/PROJETO%20IRPF/arquivos_teste_irpf_rtf/CT01C_AUTENTICIDADE_RETIFICADORA_SEM_RECIBO_VALIDO.rtf))
- **O que faltava testar:** Fraudadores que enviam uma `Declaração de Ajuste Anual Retificadora` com recibo anterior zerado/inválido (`00.00.00.00.00-00`).
- **Resultado Esperado:** ❌ **IU Docs REPROVA** (Retificadora sem recibo válido / Velocity Check) | ❌ **Certa REPROVA** (Quebra de padrão do número de recibo).

### `RT-05C` — Funcionalidade 5: Manipulação do Arquivo — Evasão por "Print-to-PDF" / Achatamento de Camadas (Metadados Oficiais RFB)
- **Arquivo de Teste (PDF):** [CT05C_MANIPULACAO_PDF_ACHATADO_PRINT_TO_PDF_CERTA.pdf](file:///c:/Users/Longaresi/Documents/PROJETO%20IRPF/arquivos_teste_irpf/CT05C_MANIPULACAO_PDF_ACHATADO_PRINT_TO_PDF_CERTA.pdf) ([Versão `.rtf`](file:///c:/Users/Longaresi/Documents/PROJETO%20IRPF/arquivos_teste_irpf_rtf/CT05C_MANIPULACAO_PDF_ACHATADO_PRINT_TO_PDF_CERTA.rtf))
- **Ajuste Realizado:** Metadados alinhados 100% com o padrão oficial da Receita Federal (`Creator: JasperReports Library version 5.6.1` | `Producer: iText 2.1.7 by 1T3XT` | `CreationDate/ModDate: D:20260416114233-03'00'`).
- **O que testa:** Evasão forense avançada (Red Team). Com os metadados legítimos preservados, o arquivo **PASSA no teste de metadados anômalos da Certa**, forçando o motor forense a inspecionar as camadas gráficas internas e a estrutura dos streams para detectar o achatamento.
- **Resultado Esperado:** ✅ **IU Docs APROVA** (Texto e layout íntegros) | ✅ **Certa (Metadados) APROVA** (Metadados oficiais RFB legítimos) | ⚠️/❌ **Certa (Análise Gráfica):** Avaliação de integridade vetorial de objetos e fluxos.

### `RT-06C` — Funcionalidade 6: Fontes e Tipografias — Dual-Layer / Texto Invisível (`3 Tr` — OCR/Parser Poisoning)
- **Arquivo de Teste (PDF):** [CT06C_FONTES_TEXTO_INVISIVEL_DUAL_LAYER_CERTA.pdf](file:///c:/Users/Longaresi/Documents/PROJETO%20IRPF/arquivos_teste_irpf/CT06C_FONTES_TEXTO_INVISIVEL_DUAL_LAYER_CERTA.pdf) ([Versão `.rtf`](file:///c:/Users/Longaresi/Documents/PROJETO%20IRPF/arquivos_teste_irpf_rtf/CT06C_FONTES_TEXTO_INVISIVEL_DUAL_LAYER_CERTA.rtf))
- **O que faltava testar:** Injeção de texto invisível usando o modo de renderização `3 Tr` (*Neither fill nor stroke*) e fonte microscópica (`0.5 Tf`) com o valor `(250.000,00)Tj` sobreposto ao valor visível `(31.134,89)Tj` para causar *Parser Confusion* entre o que o robô lê e o que o analista humano vê.
- **Resultado Esperado:** ⚠️ **IU Docs REPROVA / ALERTA** (Divergência de camada) | ❌ **Certa REPROVA** (Detecção de operador de texto oculto `3 Tr` e tamanho `0.5 Tf`).

### `RT-07B` — Funcionalidade 7: Validação na Receita Federal — Ataque Red Team Matematicamente 100% Perfeito na Página 7
- **Arquivo de Teste (PDF):** [CT07B_GAP_RECEITA_FEDERAL_MATEMATICA_PERFEITA_REDTEAM.pdf](file:///c:/Users/Longaresi/Documents/PROJETO%20IRPF/arquivos_teste_irpf/CT07B_GAP_RECEITA_FEDERAL_MATEMATICA_PERFEITA_REDTEAM.pdf) ([Versão `.rtf`](file:///c:/Users/Longaresi/Documents/PROJETO%20IRPF/arquivos_teste_irpf_rtf/CT07B_GAP_RECEITA_FEDERAL_MATEMATICA_PERFEITA_REDTEAM.rtf))
- **O que faltava testar:** Enquanto o `CT-07A` alterava apenas o Total para `153.551,12` (sendo pego pela equação tributária da Página 7), o **`CT-07B` recalcula 100% da cascata tributária da Página 7** usando apenas glifos nativos do subset original (`FreeSans` e `FreeSansBold`):
  - **Rendimento Prefeitura (Pág. 1):** `31.134,89` $\rightarrow$ **`81.134,89`** | **Recibo:** `11.26.13.14.00-08`
  - **Total de Rendimentos Tributáveis (Págs. 2 e 7):** `103.551,12` $\rightarrow$ **`153.551,12`**
  - **Desconto Simplificado (Pág. 7):** **`16.754,34`** *(mantido no teto legal)*
  - **Base de Cálculo do Imposto (Pág. 7):** `86.796,78` $\rightarrow$ **`136.796,78`** *($153.551,12 - 16.754,34 = 136.796,78$)*
  - **Imposto Devido (Pág. 7):** `13.015,33` $\rightarrow$ **`26.765,33`** *($(136.796,78 \times 27,5\%) - 10.853,78 = 26.765,33$)*
  - **Alíquota Efetiva (Pág. 7):** `12,56%` $\rightarrow$ **`17,43%`** *($26.765,33 / 153.551,12 = 17,43\%$)*
  - **Saldo de Imposto a Pagar (Pág. 7):** `11.831,68` $\rightarrow$ **`25.581,68`** *($26.765,33 - 1.183,65 = 25.581,68$)*
  - **Valor da Quota em 8x (Pág. 7):** `1.478,96` $\rightarrow$ **`3.197,71`** *($25.581,68 / 8 = 3.197,71$)*
- **Resultado Esperado:** ⚠️ **Ambos APROVAM** — Este arquivo prova de forma definitiva que, contra uma fraude matematicamente recalculada (ou gerada diretamente no PGD oficial da RFB), **a única barreira eficaz é ativar o Item 7 (Cross-check na Receita Federal via API SERPRO / Conecta gov.br)**.

### `RT-08A` — Segurança da Aplicação (AppSec): PDF Protegido por Senha (`/Encrypt`)
- **Arquivo de Teste (PDF):** [CT08A_APPSEC_PDF_PROTEGIDO_POR_SENHA_ENCRYPT.pdf](file:///c:/Users/Longaresi/Documents/PROJETO%20IRPF/arquivos_teste_irpf/CT08A_APPSEC_PDF_PROTEGIDO_POR_SENHA_ENCRYPT.pdf) ([Versão `.rtf`](file:///c:/Users/Longaresi/Documents/PROJETO%20IRPF/arquivos_teste_irpf_rtf/CT08A_APPSEC_PDF_PROTEGIDO_POR_SENHA_ENCRYPT.rtf))
- **O que faltava testar:** Garantir que o upload de um PDF com dicionário `/Encrypt` falhe de modo seguro (*Fail-Closed* / HTTP 422) sem travar workers ou aprovar por exceção não tratada.
- **Resultado Esperado:** ❌ **REPROVADO / BLOQUEADO** tanto no **IU Docs** quanto na **Certa**.

### `RT-08B` — Segurança da Aplicação (AppSec & Manipulação): PDF com Payload Ativo (`/OpenAction /JavaScript` e `/URI` SSRF Canary)
- **Arquivo de Teste (PDF):** [CT08B_APPSEC_PDF_PAYLOAD_JAVASCRIPT_OPENACTION.pdf](file:///c:/Users/Longaresi/Documents/PROJETO%20IRPF/arquivos_teste_irpf/CT08B_APPSEC_PDF_PAYLOAD_JAVASCRIPT_OPENACTION.pdf)
- **O que faltava testar:** Injeção de `/OpenAction <</S/JavaScript/JS(...)>>` e `/AA <</O<</S/URI/URI(http://canary.redteam.internal/ssrf-irpf-test)>>>>` no objeto `/Catalog` (`157 0 obj`) para testar se o pipeline bloqueia tentativas de *Stored XSS* (contra a mesa de análise humana) e *SSRF* (contra o servidor de renderização).
- **Resultado Esperado:** ❌ **REPROVADO CRÍTICO** pela **Certa** e pelo Gateway de Upload (`CRITICAL: MALICIOUS_PDF_ACTIVE_CONTENT_JS_DETECTED`).

---

## 5. Cenários Adicionais de Fraude Bancária Real em Produção (`RT-01D`, `RT-02C`, `RT-04D`, `RT-04E`, `RT-07C`) — Total: 26 Arquivos PDF

### `RT-01D` — Funcionalidade 1/3: Declaração Final de Espólio / Contribuinte Falecido
- **Arquivo de Teste (PDF):** [CT01D_AUTENTICIDADE_DECLARACAO_FINAL_DE_ESPOLIO_IUDOCS.pdf](file:///c:/Users/Longaresi/Documents/PROJETO%20IRPF/arquivos_teste_irpf/CT01D_AUTENTICIDADE_DECLARACAO_FINAL_DE_ESPOLIO_IUDOCS.pdf)
- **Cenário Real:** O cabeçalho foi alterado nas 8 páginas de `DECLARAÇÃO DE AJUSTE ANUAL` para `DECLARAÇÃO FINAL DE ESPÓLIO` e o tipo na Página 1 para `Declaração Final de Espólio Original`.
- **Resultado Esperado:** ❌ **IU Docs REPROVA** (Bloqueio de concessão para espólio / contribuinte falecido) | ✅ **Certa APROVA** (ou alerta de template de espólio).

### `RT-02C` — Funcionalidade 2: Titularidade — Inversão Dependente/Alimentando (`KAMILE VITORIA`) como Titular
- **Arquivo de Teste (PDF):** [CT02C_TITULARIDADE_INVERSAO_ALIMENTANDO_COMO_TITULAR_IUDOCS.pdf](file:///c:/Users/Longaresi/Documents/PROJETO%20IRPF/arquivos_teste_irpf/CT02C_TITULARIDADE_INVERSAO_ALIMENTANDO_COMO_TITULAR_IUDOCS.pdf)
- **Cenário Real:** Na declaração original de Gilsonei (`250.713.388-07`), consta na Página 1 e Página 3 a alimentanda `KAMILE VITORIA DOS SANTOS` (`CPF: 526.161.888-64`). Neste teste, avalia-se se o **IU Docs** barra quando o proponente é o dependente/alimentando (cujo CPF já aparece na Página 1) ou quando os dados do alimentando são colocados na seção `IDENTIFICAÇÃO DO CONTRIBUINTE` divergindo do cabeçalho (`GILSONEI DOS SANTOS`).
- **Resultado Esperado:** ❌ **IU Docs REPROVA** (Distingue CPF de Titular vs. Dependente/Alimentando e detecta divergência entre Cabeçalho e Identificação).

### `RT-04D` — Funcionalidade 4: Páginas — Envio de Apenas 1 Página Isolada (`/Count 1`)
- **Arquivo de Teste (PDF):** [CT04D_PAGINAS_ENVIO_APENAS_PAGINA_1_SEM_DECLARACAO_COMPLETA.pdf](file:///c:/Users/Longaresi/Documents/PROJETO%20IRPF/arquivos_teste_irpf/CT04D_PAGINAS_ENVIO_APENAS_PAGINA_1_SEM_DECLARACAO_COMPLETA.pdf)
- **Cenário Real:** O proponente envia apenas a Página 1 (ou apenas o Recibo de Entrega de 1 página), omitindo as páginas 2 a 8 para esconder ausência de rendimentos, dívidas ou imposto a pagar.
- **Resultado Esperado:** ❌ **IU Docs REPROVA** (`Página 1 de 8` com apenas 1 página enviada) | ❌ **Certa REPROVA** (Truncamento severo da árvore `/Pages`).

### `RT-04E` — Funcionalidade 4: Páginas — "8 de 8 Falso" (Página 6 Duplicada 2x e Página 7 Removida)
- **Arquivo de Teste (PDF):** [CT04E_PAGINAS_8_DE_8_FALSO_PAGINA_6_DUPLICADA_SEM_PAGINA_7.pdf](file:///c:/Users/Longaresi/Documents/PROJETO%20IRPF/arquivos_teste_irpf/CT04E_PAGINAS_8_DE_8_FALSO_PAGINA_6_DUPLICADA_SEM_PAGINA_7.pdf)
- **Cenário Real (Bypass de Contagem):** O fraudador remove a Página 7 (Resumo com `SALDO IMPOSTO A PAGAR: 11.831,68`) e duplica a Página 6 (Renda Variável vazia) duas vezes (`[1, 9, 13, 17, 21, 25, 25, 33]`), mantendo o arquivo com **exatamente 8 páginas físicas (`/Count 8`)**!
- **Resultado Esperado:** ❌ **IU Docs REPROVA** (Detecta duplicação de `Página 6 de 8` e falta de `Página 7 de 8`) | ❌ **Certa REPROVA** (Referência duplicada `25 0 R` no array `/Kids`).

### `RT-07C` — Funcionalidade 4/7: Coerência Contábil & Renda Isenta — Inflação de Rendimentos Isentos (Pág. 2 vs. Pág. 8)
- **Arquivo de Teste (PDF):** [CT07C_COERENCIA_RENDIMENTOS_ISENTOS_INFLADOS_PAG2_VS_PAG8.pdf](file:///c:/Users/Longaresi/Documents/PROJETO%20IRPF/arquivos_teste_irpf/CT07C_COERENCIA_RENDIMENTOS_ISENTOS_INFLADOS_PAG2_VS_PAG8.pdf)
- **Cenário Real:** Fraudadores preferem inflar `RENDIMENTOS ISENTOS E NÃO TRIBUTÁVEIS` (Lucros e Dividendos) na Página 2 (alterado de `0,00` para `350.000,00`), pois **renda isenta não altera a Base de Cálculo nem o Imposto Devido da Página 7**! Porém, na Página 8 (`OUTRAS INFORMAÇÕES` $\rightarrow$ `Rendimentos isentos e não tributáveis`), o valor permanece `0,00`.
- **Resultado Esperado:** ❌ **IU Docs REPROVA** (Quebra de coerência contábil entre o Total de Rendimentos Isentos da Página 2 [`350.000,00`] e o espelho da Página 8 [`0,00`]).


