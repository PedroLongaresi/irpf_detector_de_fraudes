#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gerador de Planilha Excel (.xlsx) — Roteiro de Teste (RTF), Matriz IU Docs vs. Certa e Red/Blue Team
====================================================================================================
Constrói o arquivo `ROTEIRO_DE_TESTE_IRPF_IUDOCS_VS_CERTA.xlsx` (e `PLANO_DE_TESTE_IRPF_IUDOCS_VS_CERTA.xlsx`)
nativamente no padrão OpenXML (ISO/IEC 29500) usando apenas bibliotecas padrão do Python (`zipfile`, `xml`),
com cabeçalhos estilizados, cores semafóricas, filtros automáticos, larguras de coluna ajustadas e 4 abas:
  1. `1_Matriz_IUDocs_vs_Certa`: Comparativo das 7 funcionalidades + AppSec.
  2. `2_Roteiro_de_Teste_21_Casos`: Roteiro completo passo a passo (RT-00 a RT-08B) com resultados esperados e colunas de execução QA.
  3. `3_Seguranca_Red_e_Blue_Team`: Matriz ofensiva (Red Team) vs. defensiva (Blue Team), equação tributária e SIEM.
  4. `4_Baseline_Texto_Original_RFB`: Todos os campos e valores exatos da declaração original (Páginas 1 a 8).
"""

from __future__ import annotations

import zipfile
from pathlib import Path
from typing import List, Tuple
from xml.sax.saxutils import escape

BASE_DIR = Path(__file__).resolve().parent.parent
XLSX_MAIN = BASE_DIR / "ROTEIRO_DE_TESTE_IRPF_IUDOCS_VS_CERTA.xlsx"


def col_letter(idx_1based: int) -> str:
    result = ""
    n = idx_1based
    while n > 0:
        n, rem = divmod(n - 1, 26)
        result = chr(65 + rem) + result
    return result


def build_styles_xml() -> str:
    """Estilos OpenXML para cabeçalhos, células de texto com wrap, status Aprovado/Reprovado/Alerta."""
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <fonts count="5">
    <font><sz val="10"/><color rgb="FF1F2937"/><name val="Segoe UI"/></font>
    <font><b/><sz val="11"/><color rgb="FFFFFFFF"/><name val="Segoe UI"/></font>
    <font><b/><sz val="10"/><color rgb="FF0F5132"/><name val="Segoe UI"/></font>
    <font><b/><sz val="10"/><color rgb="FF842029"/><name val="Segoe UI"/></font>
    <font><b/><sz val="10"/><color rgb="FF664D03"/><name val="Segoe UI"/></font>
  </fonts>
  <fills count="7">
    <fill><patternFill patternType="none"/></fill>
    <fill><patternFill patternType="gray125"/></fill>
    <fill><patternFill patternType="solid"><fgColor rgb="FF1E3A8A"/></patternFill></fill>
    <fill><patternFill patternType="solid"><fgColor rgb="FFEA580C"/></patternFill></fill>
    <fill><patternFill patternType="solid"><fgColor rgb="FFD1E7DD"/></patternFill></fill>
    <fill><patternFill patternType="solid"><fgColor rgb="FFF8D7DA"/></patternFill></fill>
    <fill><patternFill patternType="solid"><fgColor rgb="FFFFF3CD"/></patternFill></fill>
  </fills>
  <borders count="2">
    <border><left/><right/><top/><bottom/><diagonal/></border>
    <border>
      <left style="thin"><color rgb="FFD1D5DB"/></left>
      <right style="thin"><color rgb="FFD1D5DB"/></right>
      <top style="thin"><color rgb="FFD1D5DB"/></top>
      <bottom style="thin"><color rgb="FFD1D5DB"/></bottom>
      <diagonal/>
    </border>
  </borders>
  <cellStyleXfs count="1">
    <xf numFmtId="0" fontId="0" fillId="0" borderId="0"/>
  </cellStyleXfs>
  <cellXfs count="7">
    <!-- 0: Default -->
    <xf numFmtId="0" fontId="0" fillId="0" borderId="1" xfId="0" applyAlignment="1" applyBorder="1">
      <alignment vertical="top" wrapText="1"/>
    </xf>
    <!-- 1: Header Azul Escuro -->
    <xf numFmtId="0" fontId="1" fillId="2" borderId="1" xfId="0" applyFont="1" applyFill="1" applyAlignment="1" applyBorder="1">
      <alignment horizontal="center" vertical="center" wrapText="1"/>
    </xf>
    <!-- 2: Header Laranja Destaque -->
    <xf numFmtId="0" fontId="1" fillId="3" borderId="1" xfId="0" applyFont="1" applyFill="1" applyAlignment="1" applyBorder="1">
      <alignment horizontal="center" vertical="center" wrapText="1"/>
    </xf>
    <!-- 3: Status Verde (APROVADO / SIM) -->
    <xf numFmtId="0" fontId="2" fillId="4" borderId="1" xfId="0" applyFont="1" applyFill="1" applyAlignment="1" applyBorder="1">
      <alignment horizontal="center" vertical="center" wrapText="1"/>
    </xf>
    <!-- 4: Status Vermelho (REPROVADO / BLOQUEADO) -->
    <xf numFmtId="0" fontId="3" fillId="5" borderId="1" xfId="0" applyFont="1" applyFill="1" applyAlignment="1" applyBorder="1">
      <alignment horizontal="center" vertical="center" wrapText="1"/>
    </xf>
    <!-- 5: Status Amarelo (GAP / ALERTA / NÃO) -->
    <xf numFmtId="0" fontId="4" fillId="6" borderId="1" xfId="0" applyFont="1" applyFill="1" applyAlignment="1" applyBorder="1">
      <alignment horizontal="center" vertical="center" wrapText="1"/>
    </xf>
    <!-- 6: Centralizado Normal -->
    <xf numFmtId="0" fontId="0" fillId="0" borderId="1" xfId="0" applyAlignment="1" applyBorder="1">
      <alignment horizontal="center" vertical="top" wrapText="1"/>
    </xf>
  </cellXfs>
</styleSheet>
"""


def pick_cell_style(row_idx: int, col_idx: int, val: str, is_orange_header: bool = False) -> int:
    if row_idx == 1:
        return 2 if is_orange_header else 1
    upper = val.upper()
    if upper.startswith("APROVADO") or upper == "SIM (ATIVO)":
        return 3
    if upper.startswith("REPROVADO") or upper.startswith("BLOQUEADO"):
        return 4
    if upper.startswith("GAP") or upper.startswith("NÃO (INATIVO)") or upper.startswith("ALERTA"):
        return 5
    if col_idx == 1:
        return 6
    return 0


def build_sheet_xml(
    rows: List[List[str]],
    col_widths: List[int],
    is_orange_header: bool = False,
) -> str:
    num_rows = len(rows)
    num_cols = len(col_widths)
    last_col_letter = col_letter(num_cols)

    lines: List[str] = [
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">',
        f'  <dimension ref="A1:{last_col_letter}{num_rows}"/>',
        '  <sheetViews><sheetView tabSelected="1" workbookViewId="0">',
        '    <pane ySplit="1" topLeftCell="A2" activePane="bottomLeft" state="frozen"/>',
        '  </sheetView></sheetViews>',
        '  <cols>',
    ]
    for i, w in enumerate(col_widths, start=1):
        lines.append(f'    <col min="{i}" max="{i}" width="{w}" customWidth="1"/>')
    lines.append("  </cols>")
    lines.append("  <sheetData>")

    for r_idx, row in enumerate(rows, start=1):
        ht = 32 if r_idx == 1 else 48
        lines.append(f'    <row r="{r_idx}" ht="{ht}" customHeight="1">')
        for c_idx in range(1, num_cols + 1):
            val = row[c_idx - 1] if c_idx - 1 < len(row) else ""
            style_id = pick_cell_style(r_idx, c_idx, val, is_orange_header)
            cell_ref = f"{col_letter(c_idx)}{r_idx}"
            escaped_val = escape(str(val))
            lines.append(
                f'      <c r="{cell_ref}" s="{style_id}" t="inlineStr"><is><t xml:space="preserve">{escaped_val}</t></is></c>'
            )
        lines.append("    </row>")

    lines.append("  </sheetData>")
    lines.append(f'  <autoFilter ref="A1:{last_col_letter}{num_rows}"/>')
    lines.append("</worksheet>")
    return "\n".join(lines)


def get_sheet1_data() -> Tuple[List[List[str]], List[int]]:
    headers = [
        "#",
        "Funcionalidade (Matriz Original)",
        "O que valida (Texto Original)",
        "IU Docs",
        "Certa",
        "Escopo de Responsabilidade",
        "Roteiros / Casos de Teste Associados",
        "Observação de Segurança (Red Team & Blue Team)",
    ]
    rows = [
        headers,
        [
            "0",
            "0 Baseline (Controle Positivo)",
            "Declaração original íntegra da Receita Federal (8 páginas)",
            "SIM (Ativo)",
            "SIM (Ativo)",
            "Compartilhado (IU Docs + Certa)",
            "RT-00 (CT-00)",
            "Controle positivo bit-a-bit; Blue Team registra hash SHA-256 + Recibo contra Replay Attack.",
        ],
        [
            "1",
            "1 Autenticidade",
            "Marca d'adua e status da declaração (Marca d'água e status)",
            "SIM (Ativo)",
            "SIM (Ativo)",
            "Compartilhado (IU Docs + Certa)",
            "RT-01A, RT-01B, RT-01C, RT-01D",
            "Valida marca d'água 'PROTEGIDA POR SIGILO FISCAL', rejeita 'EM PREENCHIMENTO', Retificadora sem recibo e Declaração Final de Espólio.",
        ],
        [
            "2",
            "2 Titularidade",
            "CPF e nome nas bases corporativas",
            "SIM (Ativo)",
            "NÃO (Inativo)",
            "Exclusivo IU Docs",
            "RT-02A, RT-02B, RT-02C",
            "IU Docs cruza CPF (250.713.388-07) + Módulo 11, Nome (GILSONEI DOS SANTOS) e bloqueia inversão Dependente/Alimentando (KAMILE) como Titular.",
        ],
        [
            "3",
            "3 Vigência",
            "Exercício aceito pela regra",
            "SIM (Ativo)",
            "NÃO (Inativo)",
            "Exclusivo IU Docs",
            "RT-03A, RT-03B",
            "IU Docs exige EXERCÍCIO 2026 / ANO-CALENDÁRIO 2025 e invariante (Exercício - Ano = 1); Certa não valida vigência.",
        ],
        [
            "4",
            "4 Páginas",
            "Completude, sequência e coerência",
            "SIM (Ativo)",
            "SIM (Ativo)",
            "Compartilhado (IU Docs + Certa)",
            "RT-04A, RT-04B, RT-04C, RT-04D, RT-04E",
            "Ambos validam total de 8 páginas, rejeitam página única isolada (RT-04D), bloqueiam '8 de 8 falso' com página duplicada (RT-04E) e exigem coerência.",
        ],
        [
            "5",
            "5 Manipulação do arquivo",
            "Detecção de adulteração em arquivos",
            "NÃO (Inativo)",
            "SIM (Ativo)",
            "Exclusivo Certa",
            "RT-05A, RT-05B, RT-05C",
            "Certa detecta editores externos (Canva/ilovepdf), múltiplos %%EOF, retângulo branco sobreposto (Whiteout) e evasão por Print-to-PDF.",
        ],
        [
            "6",
            "6 Fontes e tipografias",
            "Se existem elementos alterados ou inseridos artificialmente",
            "NÃO (Inativo)",
            "SIM (Ativo)",
            "Exclusivo Certa",
            "RT-06A, RT-06B, RT-06C",
            "Certa detecta fontes intrusas (/F4 Courier-Bold), desalinhamento de baseline/escala Tm e injeção de texto invisível (3 Tr).",
        ],
        [
            "7",
            "7 Validação na Receita Federal",
            "Cross check com a receita federal para validação dos dados",
            "NÃO (Inativo)",
            "NÃO (Inativo)",
            "Gap Mapeado (Inativo em Ambos)",
            "RT-07A, RT-07B, RT-07C",
            "CT-07A (equação Pág. 7), CT-07C (Renda Isenta Pág. 2 vs Pág. 8) e CT-07B (Matemática 100% recalculada — prova necessidade da API SERPRO/RFB).",
        ],
        [
            "8",
            "8 Segurança de Aplicação (AppSec)",
            "Proteção do pipeline contra PDF com senha (/Encrypt) e Payloads Ativos (/JS, /OpenAction, /URI)",
            "SIM (Ativo)",
            "SIM (Ativo)",
            "Segurança de Upload (Red & Blue Team)",
            "RT-08A, RT-08B",
            "Garante comportamento Fail-Closed (HTTP 422) em PDFs com senha e bloqueia scripts ativos (Stored XSS / SSRF Canary).",
        ],
    ]
    widths = [6, 30, 38, 16, 16, 28, 30, 55]
    return rows, widths


def get_sheet2_data() -> Tuple[List[List[str]], List[int]]:
    headers = [
        "ID Roteiro",
        "ID Caso",
        "Pilar / Funcionalidade",
        "Escopo Alvo",
        "Arquivo de Teste PDF (arquivos_teste_irpf/)",
        "Categoria do Cenário",
        "Passo a Passo de Execução (Roteiro QA)",
        "Texto / Estrutura Original (Baseline RFB)",
        "Alteração Cirúrgica Realizada no Arquivo",
        "Resultado Esperado: IU Docs",
        "Resultado Esperado: Certa",
        "Validação Red Team (Vetor de Ataque)",
        "Validação Blue Team (Detecção & Mitigação)",
        "Status Execução QA",
        "Evidência / Observações do Testador",
    ]
    cases = [
        [
            "RT-00", "CT-00", "0. Baseline (Itens 1 a 6)", "Ambos (IU Docs + Certa)",
            "CT00_ORIGINAL_VALIDO_IRPF_2026_2025.pdf", "Baseline Positivo",
            "1. Iniciar proposta para GILSONEI DOS SANTOS (CPF 250.713.388-07).\n2. Enviar arquivo original CT00.\n3. Validar aprovação em ambos os motores.",
            "Marca d'água: PROTEGIDA POR SIGILO FISCAL | CPF: 250.713.388-07 | Nome: GILSONEI DOS SANTOS | Exercício 2026 / Ano 2025 | 8 páginas | Total: 103.551,12",
            "Nenhuma alteração. Cópia bit-a-bit fiel ao documento original (331.092 bytes).",
            "APROVADO", "APROVADO",
            "Replay Attack: Reuso do mesmo PDF autêntico em múltiplas propostas distintas.",
            "Registrar hash SHA-256 + (CPF, Exercício, Recibo 11.26.13.14.00-02) para impedir reuso cruzado.",
            "PENDENTE", "",
        ],
        [
            "RT-01A", "CT-01A", "1. Autenticidade (Sem Marca d'Água)", "Ambos (IU Docs + Certa)",
            "CT01A_AUTENTICIDADE_SEM_MARCA_DAGUA.pdf", "Matriz Base (Item 1)",
            "1. Submeter CT01A sem marca d'água.\n2. Verificar reprovação na regra 1 - Autenticidade no IU Docs e na Certa.",
            "Operador gráfico 'q 333.93 0 0 493 161 203 cm /img1 Do Q' desenhando 'PROTEGIDA POR SIGILO FISCAL' nas 8 páginas.",
            "Supressão cirúrgica do operador '/imgX Do' ('q Q') nas 8 páginas mantendo 100% do texto original intacto.",
            "REPROVADO (Sem marca d'água)", "REPROVADO (Camada de marca d'água suprimida)",
            "Remover apenas a chamada 'Do' no stream deixando os XObjects /img1..15 no dicionário para enganar checagens rasas.",
            "Certa audita se os XObjects declarados em /Resources são efetivamente invocados com 'Do' no content stream.",
            "PENDENTE", "",
        ],
        [
            "RT-01B", "CT-01B", "1. Autenticidade (Status Rascunho / Em Preenchimento)", "Ambos (IU Docs + Certa)",
            "CT01B_AUTENTICIDADE_STATUS_RASCUNHO.pdf", "Matriz Base (Item 1)",
            "1. Submeter CT01B com marca d'água 'EM PREENCHIMENTO'.\n2. Confirmar reprovação por status de rascunho não transmitido.",
            "Marca d'água: PROTEGIDA POR SIGILO FISCAL | Tipo: Declaração de Ajuste Anual Original | Recibo: 11.26.13.14.00-02",
            "Marca d'água diagonal: 'EM PREENCHIMENTO' | Tipo: 'Declaração EM PREENCHIMENTO' | Sem número de recibo.",
            "REPROVADO (Status EM PREENCHIMENTO)", "REPROVADO (Marca d'água e status de rascunho)",
            "Gerar PDF de rascunho no PGD da Receita com renda fictícia antes de transmitir ao Fisco.",
            "Bloqueio por regex de status 'EM PREENCHIMENTO' e ausência de recibo de entrega válido.",
            "PENDENTE", "",
        ],
        [
            "RT-01C", "CT-01C", "1. Autenticidade (Retificadora Sem Recibo Válido)", "Ambos (IU Docs + Certa)",
            "CT01C_AUTENTICIDADE_RETIFICADORA_SEM_RECIBO_VALIDO.pdf", "Fraude Real / Red Team",
            "1. Submeter CT01C (Declaração Retificadora com recibo anterior 00.00.00.00.00-00).\n2. Verificar bloqueio de autenticidade/protocolo.",
            "Tipo: Declaração de Ajuste Anual Original | Recibo: 11.26.13.14.00-02",
            "Tipo alterado para 'Declaração de Ajuste Anual Retificadora' com recibo anterior zerado '00.00.00.00.00-00'.",
            "REPROVADO (Retificadora sem recibo válido)", "REPROVADO (Padrão de recibo inválido)",
            "Golpe da 'Retificadora Vai-e-Volta': simular retificação de última hora para inflar renda sem lastro.",
            "Exigir recibo anterior válido (não zerado) e aplicar Velocity Check em retificadoras recentes.",
            "PENDENTE", "",
        ],
        [
            "RT-01D", "CT-01D", "1. Autenticidade & Regra (Declaração Final de Espólio)", "IU Docs (Autenticidade / Status)",
            "CT01D_AUTENTICIDADE_DECLARACAO_FINAL_DE_ESPOLIO_IUDOCS.pdf", "Fraude Real / Regra de Negócio",
            "1. Submeter CT01D (Declaração Final de Espólio).\n2. Verificar bloqueio automático de concessão para espólio / contribuinte falecido.",
            "Título: DECLARAÇÃO DE AJUSTE ANUAL | Tipo: Declaração de Ajuste Anual Original",
            "Título alterado nas 8 páginas para 'DECLARAÇÃO FINAL DE ESPÓLIO' e Tipo para 'Declaração Final de Espólio Original'.",
            "REPROVADO (Declaração de Espólio não aceita)", "APROVADO (Ou Alerta de Template de Espólio)",
            "Utilizar declaração de espólio (contribuinte falecido) ou saída definitiva do país para tentar aprovar limite.",
            "IU Docs bloqueia títulos 'DECLARAÇÃO FINAL DE ESPÓLIO' e 'DECLARAÇÃO DE SAÍDA DEFINITIVA DO PAÍS'.",
            "PENDENTE", "",
        ],
        [
            "RT-02A", "CT-02A", "2. Titularidade (CPF Divergente da Base)", "Exclusivo IU Docs",
            "CT02A_TITULARIDADE_CPF_DIVERGENTE_IUDOCS.pdf", "Matriz Base (Item 2)",
            "1. Na proposta do CPF 250.713.388-07, submeter CT02A (CPF 250.713.388-88).\n2. Validar que IU Docs REPROVA e Certa APROVA.",
            "CPF: 250.713.388-07 (presente nos cabeçalhos das 8 páginas e na Página 1).",
            "CPF alterado cirurgicamente para '250.713.388-88' usando glifos nativos das fontes /F2 e /F3 e header zlib 0x78 0x9C.",
            "REPROVADO (CPF diverge da base corporativa)", "APROVADO (Escopo inativo na Certa; arquivo forense limpo)",
            "Edição cirúrgica do CPF no stream nativo para usar declaração de terceiro sem acionar alerta forense na Certa.",
            "IU Docs valida igualdade estrita com o CPF da proposta + validação matemática Módulo 11 (DV -88 é inválido!).",
            "PENDENTE", "",
        ],
        [
            "RT-02B", "CT-02B", "2. Titularidade (Nome Divergente da Base)", "Exclusivo IU Docs",
            "CT02B_TITULARIDADE_NOME_DIVERGENTE_IUDOCS.pdf", "Matriz Base (Item 2)",
            "1. Submeter CT02B (Nome: GILSONEI DOS SANTOS SILVA).\n2. Validar que IU Docs REPROVA por nome divergente e Certa APROVA.",
            "Nome: GILSONEI DOS SANTOS (nas 8 páginas).",
            "Nome alterado cirurgicamente para 'GILSONEI DOS SANTOS SILVA' usando caracteres existentes no subset da fonte FreeSansBold.",
            "REPROVADO (Nome diverge da base corporativa)", "APROVADO (Escopo inativo na Certa; arquivo forense limpo)",
            "Reutilizar letras já presentes no subset da fonte embarcada para alterar o nome do titular sem injetar nova fonte.",
            "IU Docs realiza batimento determinístico do Nome Completo contra a base cadastral vinculada ao CPF.",
            "PENDENTE", "",
        ],
        [
            "RT-02C", "CT-02C", "2. Titularidade (Inversão Dependente/Alimentando como Titular)", "Exclusivo IU Docs",
            "CT02C_TITULARIDADE_INVERSAO_ALIMENTANDO_COMO_TITULAR_IUDOCS.pdf", "Fraude Familiar / OCR Trap",
            "1. Testar envio onde o proponente é a alimentanda KAMILE VITORIA DOS SANTOS (CPF 526.161.888-64, que consta na Pág. 1) ou com dados invertidos na Identificação vs Cabeçalho.\n2. Confirmar que IU Docs não confunde CPF de Dependente/Alimentando com o Titular da renda!",
            "Cabeçalho e Identificação: GILSONEI DOS SANTOS (250.713.388-07) | Alimentando: KAMILE VITORIA DOS SANTOS (526.161.888-64).",
            "Na seção IDENTIFICAÇÃO DO CONTRIBUINTE (Pág. 1), o Nome/CPF foi trocado para a alimentanda KAMILE VITORIA DOS SANTOS (526.161.888-64), divergindo do cabeçalho (GILSONEI).",
            "REPROVADO (Conflito Titular vs. Dependente/Alimentando)", "APROVADO (Ou Alerta de Incoerência Interna)",
            "Filho/dependente ou alimentando usa a declaração do pai/titular porque seu próprio CPF aparece na Página 1 do PDF.",
            "IU Docs deve ancorar a extração de Titularidade estritamente no par (Cabeçalho == Identificação do Contribuinte == Proponente).",
            "PENDENTE", "",
        ],
        [
            "RT-03A", "CT-03A", "3. Vigência (Exercício Expirado 2023/2022)", "Exclusivo IU Docs",
            "CT03A_VIGENCIA_EXERCICIO_EXPIRADO_2023_2022_IUDOCS.pdf", "Matriz Base (Item 3)",
            "1. Submeter CT03A (EXERCÍCIO 2023 / ANO-CALENDÁRIO 2022).\n2. Validar que IU Docs REPROVA na regra 3 - Vigência e Certa APROVA.",
            "EXERCÍCIO 2026 | ANO-CALENDÁRIO 2025 (nas 8 páginas).",
            "Alterado cirurgicamente para 'EXERCÍCIO 2023' | 'ANO-CALENDÁRIO 2022' nas 8 páginas e textos da Página 1.",
            "REPROVADO (Exercício 2023 fora da vigência)", "APROVADO (Escopo inativo na Certa; arquivo forense limpo)",
            "Apresentar declaração de anos anteriores em que o contribuinte possuía renda superior.",
            "IU Docs bloqueia exercício fora da política; correlação Blue Team detecta anacronismo com CreationDate (2026).",
            "PENDENTE", "",
        ],
        [
            "RT-03B", "CT-03B", "3. Vigência (Ano-Calendário Inconsistente)", "Exclusivo IU Docs",
            "CT03B_VIGENCIA_ANO_CALENDARIO_INCONSISTENTE_IUDOCS.pdf", "Matriz Base (Item 3)",
            "1. Submeter CT03B (EXERCÍCIO 2026 com ANO-CALENDÁRIO 2023).\n2. Validar reprovação no IU Docs e aprovação na Certa.",
            "EXERCÍCIO 2026 | ANO-CALENDÁRIO 2025",
            "Cabeçalho alterado para 'EXERCÍCIO 2026' com 'ANO-CALENDÁRIO 2023' (quebra da regra Exercício = Ano + 1).",
            "REPROVADO (Par Exercício/Ano-Calendário inválido)", "APROVADO (Escopo inativo na Certa)",
            "Adulteração parcial apenas do Exercício ou apenas do Ano-Calendário pelo fraudador.",
            "Regra invariante no IU Docs: (Exercício - Ano_Calendário == 1) em todas as páginas.",
            "PENDENTE", "",
        ],
        [
            "RT-04A", "CT-04A", "4. Páginas (Incompletude: Falta Página 7)", "Ambos (IU Docs + Certa)",
            "CT04A_PAGINAS_INCOMPLETO_FALTA_PAGINA_7.pdf", "Matriz Base (Item 4)",
            "1. Submeter CT04A contendo apenas 7 páginas (sem a Pág. 7 de Resumo).\n2. Confirmar reprovação em ambos os sistemas.",
            "8 páginas completas ('Página 1 de 8' até 'Página 8 de 8').",
            "Objeto /Pages com /Count 7 (removida a Página 7 - Resumo); rodapé salta de 'Página 6 de 8' para 'Página 8 de 8'.",
            "REPROVADO (Documento incompleto: 7 de 8 páginas)", "REPROVADO (Quebra de completude e objeto órfão)",
            "Ocultar a página de Resumo/Cálculo do Imposto ou Dívidas e Ônus Reais.",
            "IU Docs valida contagem N de M e presença obrigatória do Resumo; Certa detecta objeto órfão 29 0 obj na xref.",
            "PENDENTE", "",
        ],
        [
            "RT-04B", "CT-04B", "4. Páginas (Quebra de Sequência: Pág. 3 antes da 2)", "Ambos (IU Docs + Certa)",
            "CT04B_PAGINAS_FORA_DE_SEQUENCIA.pdf", "Matriz Base (Item 4)",
            "1. Submeter CT04B com páginas 2 e 3 invertidas.\n2. Confirmar reprovação por sequência inválida em ambos.",
            "Sequência: Página 1 de 8, Página 2 de 8, Página 3 de 8...",
            "Árvore /Kids reordenada para [1, 13, 9, 17, 21, 25, 29, 33] (Página 3 de 8 antecede a Página 2 de 8).",
            "REPROVADO (Sequência de paginação quebrada)", "REPROVADO (Árvore /Kids fora de ordem)",
            "Desmontar e remontar páginas em ferramentas de PDF merge errando a ordenação.",
            "Verificação estritamente crescente do índice de página no rodapé e monotonicidade dos IDs em /Kids.",
            "PENDENTE", "",
        ],
        [
            "RT-04C", "CT-04C", "4. Páginas (Incoerência entre Páginas: Pág. 2 e Pág. 7)", "Ambos (IU Docs + Certa)",
            "CT04C_PAGINAS_INCOERENCIA_CABECALHO_E_RESUMO.pdf", "Matriz Base (Item 4)",
            "1. Submeter CT04C.\n2. Confirmar reprovação por divergência de CPF na Pág. 2 e divergência contábil entre Pág. 2 e Pág. 7.",
            "CPF 250.713.388-07 em todas as páginas e Total de Rendimentos 103.551,12 na Pág. 2 e na Pág. 7.",
            "Na Pág. 2 o CPF do cabeçalho é '250.713.388-55'; na Pág. 7 o Total é '203.551,12' (divergindo dos '103.551,12' da Pág. 2).",
            "REPROVADO (Incoerência de cabeçalho e soma contábil)", "REPROVADO (Enxerto / Incoerência entre páginas)",
            "Ataque 'Frankenstein': enxertar página de outra declaração ou alterar apenas o Resumo sem atualizar os itens.",
            "Reconciliação cruzada obrigatória: Cabeçalho invariante nas 8 páginas e Soma(Pág. 1 + Pág. 2) == Resumo(Pág. 7).",
            "PENDENTE", "",
        ],
        [
            "RT-04D", "CT-04D", "4. Páginas (Envio de Apenas 1 Página Isolada)", "Ambos (IU Docs + Certa)",
            "CT04D_PAGINAS_ENVIO_APENAS_PAGINA_1_SEM_DECLARACAO_COMPLETA.pdf", "Erro Real / Ocultação de Dados",
            "1. Submeter CT04D contendo apenas a Página 1 (/Count 1, rodapé 'Página 1 de 8').\n2. Confirmar reprovação imediata em ambos.",
            "Declaração completa de 8 páginas (/Count 8).",
            "Árvore /Kids truncada para conter apenas a Página 1 ('<</Kids[1 0 R]/Type/Pages/Count 1>>').",
            "REPROVADO (Apenas 1 de 8 páginas enviada)", "REPROVADO (Truncamento severo de páginas)",
            "Enviar apenas a 1ª página (ou apenas o Recibo) para ocultar dívidas, evolução patrimonial e resumo de imposto.",
            "Bloqueio quando Count(Pages) == 1 ou Count(Pages) < Total_Declarado_Rodape.",
            "PENDENTE", "",
        ],
        [
            "RT-04E", "CT-04E", "4. Páginas ('8 de 8 Falso' — Página 6 Duplicada Sem Página 7)", "Ambos (IU Docs + Certa)",
            "CT04E_PAGINAS_8_DE_8_FALSO_PAGINA_6_DUPLICADA_SEM_PAGINA_7.pdf", "Bypass de Contagem / Red Team",
            "1. Submeter CT04E (que possui 8 páginas físicas, mas repete a Pág. 6 duas vezes e omite a Pág. 7).\n2. Validar se ambos detectam a duplicação e a falta da Pág. 7.",
            "Páginas 1, 2, 3, 4, 5, 6, 7, 8 distintas (/Count 8).",
            "Árvore /Kids com 8 elementos '[1, 9, 13, 17, 21, 25, 25, 33]' (/Count 8, onde a Pág. 6 aparece 2x e a Pág. 7 foi omitida).",
            "REPROVADO (Falta Página 7 e Página 6 duplicada)", "REPROVADO (Referência duplicada '25 0 R' em /Kids)",
            "Duplicar uma página vazia ('Sem Informações') para manter o PDF com 8 páginas após remover a página de Resumo.",
            "Validar conjunto exato {1..N} sem duplicatas nos rodapés e proibir referências repetidas no array /Kids.",
            "PENDENTE", "",
        ],
        [
            "RT-05A", "CT-05A", "5. Manipulação do Arquivo (Metadados + Incremental Update)", "Exclusivo Certa",
            "CT05A_MANIPULACAO_METADADOS_E_INCREMENTAL_CERTA.pdf", "Matriz Base (Item 5)",
            "1. Submeter CT05A.\n2. Validar que passa no teste de metadados (JasperReports/iText) e Certa avalia Incremental Update (%%EOF).",
            "Creator: JasperReports Library version 5.6.1 | Producer: iText 2.1.7 by 1T3XT | Único bloco xref e %%EOF.",
            "Texto 100% original, Incremental Update (/Prev 327756, duplo %%EOF) mantendo metadados oficiais RFB (JasperReports/iText) para passar na checagem de metadados.",
            "APROVADO (Texto e regras de negócio intactos)", "REPROVADO (Múltiplos %%EOF / Incremental Update detectado)",
            "Editar o PDF salvando atualização incremental mantendo cabeçalho de metadados do emissor oficial.",
            "Metadados passam na checagem da Certa; a reprovação deve ocorrer na análise estrutural de blocos xref / %%EOF.",
            "PENDENTE", "",
        ],
        [
            "RT-05B", "CT-05B", "5. Manipulação do Arquivo (Sobreposição Whiteout)", "Exclusivo Certa",
            "CT05B_MANIPULACAO_SOBREPOSICAO_WHITEOUT_CERTA.pdf", "Matriz Base (Item 5)",
            "1. Submeter CT05B.\n2. Validar que passa na checagem de metadados e Certa REPROVA pela detecção de Whiteout.",
            "Pág. 1 Prefeitura: 31.134,89 | Pág. 2 e 7 Total: 103.551,12 | Metadados oficiais JasperReports/iText.",
            "Mantém '(31.134,89)Tj' oculto na Pág. 1, desenha retângulo branco '1 1 1 rg 214 157 46 11 re f', escreve '81.134,89' por cima, atualiza Total para '153.551,12' e mantém metadados oficiais RFB.",
            "APROVADO (Somas superficiais batem)", "REPROVADO (Adulteração por sobreposição gráfica Whiteout)",
            "Cobrir valor original com caixa branca (Whiteout) preservando metadados legítimos do emissor para evitar bloqueio prévio.",
            "Passa no teste de metadados; Certa detecta colisão espacial (Bounding Box) entre texto inferior oculto e retângulo branco.",
            "PENDENTE", "",
        ],
        [
            "RT-05C", "CT-05C", "5. Manipulação do Arquivo (Print-to-PDF / Achatamento)", "Exclusivo Certa",
            "CT05C_MANIPULACAO_PDF_ACHATADO_PRINT_TO_PDF_CERTA.pdf", "Evasão Forense / Red Team",
            "1. Submeter CT05C ajustado com metadados oficiais RFB.\n2. Confirmar que PASSA no teste de metadados anômalos e testa detecção de achatamento/rasterização.",
            "Estrutura nativa JasperReports 5.6.1 / iText 2.1.7.",
            "Metadados oficiais RFB preservados (JasperReports Library version 5.6.1 / iText 2.1.7) para PASSAR no teste de metadados da Certa, com camada achatada/rasterizada.",
            "APROVADO (Texto e metadados oficiais válidos)", "AVALIAÇÃO FORENSE (Metadados Aprovados; análise de camadas/achatamento)",
            "Técnica de evasão: fraudador achata o PDF para tentar apagar camadas vetoriais, mas injeta metadados legítimos da RFB.",
            "Metadados passam 100% no motor da Certa; validação foca na integridade vetorial de objetos e fluxos gráficos.",
            "PENDENTE", "",
        ],
        [
            "RT-06A", "CT-06A", "6. Fontes e Tipografias (Fonte Intrusa Courier-Bold)", "Exclusivo Certa",
            "CT06A_FONTES_TIPOGRAFIA_DIVERGENTE_COURIER_CERTA.pdf", "Matriz Base (Item 6)",
            "1. Submeter CT06A.\n2. Validar que IU Docs APROVA e Certa REPROVA no item 6 - Fontes e tipografias.",
            "Valores '31.134,89' (Pág. 1) e '36.000,00' (Pág. 2) renderizados com a fonte nativa /F3 (ZBXMLK+FreeSans, 8 Tf).",
            "Mesmo texto original, porém os valores '31.134,89' e '36.000,00' usam fonte artificial '/F4 Courier-Bold' (9.5 Tf).",
            "APROVADO (Texto extraído é idêntico)", "REPROVADO (Fonte intrusa /F4 Courier-Bold detectada)",
            "Injetar fonte padrão do sistema (Courier, Arial, Times) ao editar valores por não ter a fonte subset original.",
            "Certa aplica whitelist estrita de fontes por página (apenas /F1 Helvetica, /F2 FreeSansBold e /F3 FreeSans).",
            "PENDENTE", "",
        ],
        [
            "RT-06B", "CT-06B", "6. Fontes e Tipografias (Desalinhamento Baseline e Escala)", "Exclusivo Certa",
            "CT06B_FONTES_DESALINHAMENTO_E_ESCALA_CERTA.pdf", "Matriz Base (Item 6)",
            "1. Submeter CT06B.\n2. Validar que IU Docs APROVA e Certa REPROVA por desalinhamento geométrico e escala.",
            "Matriz unitária '1 0 0 1 217.42 159.28 Tm /F3 8 Tf (31.134,89)Tj' alinhada à linha da fonte pagadora.",
            "Mesma fonte /F3 (FreeSans), mas com matriz distorcida '1.18 0 0 1.25 213.10 162.85 Tm' (+3.57pt no eixo Y) e tamanho '10 Tf'.",
            "APROVADO (IU Docs não avalia geometria Tm)", "REPROVADO (Desalinhamento de baseline e distorção de escala)",
            "Reutilizar a fonte nativa /F3 mas errar o alinhamento Y ou a matriz de escala ao posicionar o número editado.",
            "Certa valida matriz unitária (1 0 0 1), tamanho exato (8 Tf) e colinearidade horizontal (Y = 159.28) na tabela.",
            "PENDENTE", "",
        ],
        [
            "RT-06C", "CT-06C", "6. Fontes e Tipografias (Texto Invisível 3 Tr / Dual-Layer)", "Exclusivo Certa",
            "CT06C_FONTES_TEXTO_INVISIVEL_DUAL_LAYER_CERTA.pdf", "OCR Poisoning / Red Team",
            "1. Submeter CT06C.\n2. Validar que Certa REPROVA pela presença de texto invisível (modo 3 Tr) e fonte microscópica (0.5 Tf).",
            "Apenas texto visível normal (modo de renderização padrão 0 Tr).",
            "Injeta bloco invisível 'BT 3 Tr 1 0 0 1 217.42 159.28 Tm /F3 0.5 Tf (250.000,00)Tj 0 Tr' junto ao valor '31.134,89'.",
            "ALERTA / REPROVADO (Parser Poisoning)", "REPROVADO (Detecção de camada de texto invisível 3 Tr)",
            "OCR/Parser Poisoning: fazer o extrator de texto ler renda de 250.000,00 invisível enquanto a tela mostra 31.134,89 (ou vice-versa).",
            "Certa bloqueia imediatamente operadores de texto invisível ('3 Tr' / '7 Tr') e fontes com tamanho < 1 Tf.",
            "PENDENTE", "",
        ],
        [
            "RT-07A", "CT-07A", "7. Validação na Receita Federal (Gap Parcial — Sem Recálculo Pág. 7)", "Gap Mapeado (Ambos)",
            "CT07A_GAP_RECEITA_FEDERAL_RECIBO_E_RENDA_NAO_AUDITADOS_RFB.pdf", "Matriz Base (Item 7)",
            "1. Submeter CT07A.\n2. Observar que sem auditoria da Equação Tributária na Pág. 7 e sem API RFB, ambos aprovam.\n3. Validar bloqueio pela regra Blue Team da Equação Tributária.",
            "Recibo: 11.26.13.14.00-02 | Rendimento Pág. 1: 31.134,89 | Total Pág. 2 e 7: 103.551,12 | Base Pág. 7: 86.796,78 | Imposto: 13.015,33",
            "Altera cirurgicamente Recibo para '99.88.77.66.55-00', Rendimento para '81.134,89' e Total para '153.551,12', mas mantém Base (86.796,78) e Imposto (13.015,33) originais.",
            "GAP (Aprovado sem Equação Tributária / Reprovado com Blue Team)", "GAP (Aprovado pois não há rastro forense)",
            "Adulterar cirurgicamente os rendimentos e o totalizador mantendo fontes nativas, header 0x78 0x9C e xref limpa.",
            "Blue Team barra via Equação Tributária da Pág. 7: (153.551,12 - 16.754,34 = 136.796,78 != 86.796,78).",
            "PENDENTE", "",
        ],
        [
            "RT-07B", "CT-07B", "7. Validação na Receita Federal (Gap Total — Matemática 100% Perfeita)", "Gap Mapeado (Ambos)",
            "CT07B_GAP_RECEITA_FEDERAL_MATEMATICA_PERFEITA_REDTEAM.pdf", "PoC Executiva Red Team (Item 7)",
            "1. Submeter CT07B (onde toda a Página 7 foi matematicamente recalculada com glifos nativos).\n2. Documentar como PoC executiva que exige a ativação do Item 7 (API SERPRO/RFB).",
            "Total: 103.551,12 | Base: 86.796,78 | Imposto: 13.015,33 | Alíquota: 12,56% | Saldo: 11.831,68 | Quota: 1.478,96",
            "Recalcula TODA a Pág. 7 com glifos nativos: Total=153.551,12 | Base=136.796,78 | Imposto=26.765,33 | Alíquota=17,43% | Saldo=25.581,68 | Quota=3.197,71.",
            "GAP (Aprovado — Matemática 100% fechada)", "GAP (Aprovado — Estrutura forense 100% nativa)",
            "Recalcular toda a cascata tributária da Pág. 7 (ou gerar o PDF no próprio PGD oficial da RFB) para vencer regras internas.",
            "Prova definitiva de que o Item 7 deve ser ativado via consulta de recibo/dados na API Conecta gov.br / SERPRO.",
            "PENDENTE", "",
        ],
        [
            "RT-07C", "CT-07C", "4/7. Coerência Contábil & Renda Isenta (Inflação de Rendimentos Isentos)", "IU Docs (Coerência Pág. 2 vs Pág. 8)",
            "CT07C_COERENCIA_RENDIMENTOS_ISENTOS_INFLADOS_PAG2_VS_PAG8.pdf", "Fraude de Renda Isenta / Dividendos",
            "1. Submeter CT07C (onde Rendimentos Isentos na Pág. 2 foi inflado para 350.000,00, mas na Pág. 8 permaneceu 0,00).\n2. Validar se o IU Docs cruza o Total de Isentos da Pág. 2 com Outras Informações na Pág. 8.",
            "Pág. 2 TOTAL Rendimentos Isentos e Não Tributáveis: 0,00 | Pág. 8 Rendimentos isentos e não tributáveis: 0,00.",
            "Altera o TOTAL de 'RENDIMENTOS ISENTOS E NÃO TRIBUTÁVEIS' na Pág. 2 para '350.000,00' mantendo '0,00' na Pág. 8.",
            "REPROVADO (Incoerência Pág. 2 [350.000,00] vs Pág. 8 [0,00])", "APROVADO (Ou Alerta de Coerência Interna)",
            "Fraudar Rendimentos Isentos (Lucros e Dividendos) porque eles não alteram a Base de Cálculo nem o Imposto Devido da Pág. 7!",
            "Blue Team exige batimento cruzado obrigatório: Total_Isentos(Pág. 2) == Outras_Informações_Isentos(Pág. 8).",
            "PENDENTE", "",
        ],
        [
            "RT-08A", "CT-08A", "8. AppSec & Resiliência (PDF Protegido por Senha /Encrypt)", "Ambos (AppSec Fail-Closed)",
            "CT08A_APPSEC_PDF_PROTEGIDO_POR_SENHA_ENCRYPT.pdf", "AppSec / Resiliência",
            "1. Submeter CT08A com dicionário /Encrypt.\n2. Confirmar que ambos rejeitam imediatamente (HTTP 422) sem travar fila.",
            "PDF desbloqueado sem dicionário /Encrypt no trailer.",
            "Adiciona objeto '159 0 obj <</Filter/Standard/V 2/R 3/Length 128...>>' e referência '/Encrypt 159 0 R' no trailer.",
            "BLOQUEADO (Arquivo protegido por senha)", "BLOQUEADO (Arquivo protegido por senha)",
            "Enviar PDF criptografado para causar exceção não tratada, timeout de worker ou aprovação por Fail-Open.",
            "Validação Fail-Closed no gateway e nos motores: rejeição imediata de qualquer PDF com tag /Encrypt.",
            "PENDENTE", "",
        ],
        [
            "RT-08B", "CT-08B", "8. AppSec & Manipulação (Payload /JavaScript e /URI SSRF Canary)", "Ambos (AppSec & Certa)",
            "CT08B_APPSEC_PDF_PAYLOAD_JAVASCRIPT_OPENACTION.pdf", "AppSec / Pentest Upload",
            "1. Submeter CT08B contendo /OpenAction /JavaScript e /URI.\n2. Confirmar bloqueio crítico e sanitização antes de exibir na mesa humana.",
            "Catálogo /Root limpo (<</Names 156 0 R/Type/Catalog/Outlines 96 0 R/Pages 8 0 R...>>).",
            "Injeta '/OpenAction<</S/JavaScript/JS(app.alert(...))>>' e '/AA<</O<</S/URI/URI(http://canary.redteam.internal/ssrf-irpf-test)>>>>'.",
            "BLOQUEADO NO GATEWAY", "REPROVADO CRÍTICO (Script ativo /JS e /URI detectados)",
            "Stored XSS contra o navegador do analista de fraude e SSRF Canary para descobrir o IP interno dos servidores de OCR.",
            "Bloqueio estrito na Certa e no Gateway contra tags /OpenAction, /AA, /JS, /JavaScript, /Launch, /EmbeddedFiles e /URI.",
            "PENDENTE", "",
        ],
    ]
    rows = [headers] + cases
    widths = [12, 10, 36, 24, 52, 28, 45, 42, 48, 26, 26, 42, 45, 18, 30]
    return rows, widths


def get_sheet3_data() -> Tuple[List[List[str]], List[int]]:
    headers = [
        "ID Vetor",
        "Camada / Alvo",
        "Ameaça / Tática Ofensiva (RED TEAM)",
        "Arquivos de Teste do Vetor",
        "Controle Defensivo e Assinatura Técnica (BLUE TEAM)",
        "Regra de Correlação (IU Docs + Certa)",
        "Código de Alerta SIEM / SOC",
    ]
    rows = [
        headers,
        [
            "SEC-01",
            "Camada Binária FlateDecode & XRef",
            "Edição Cirúrgica Furtiva de Stream: Descompacta o stream original, altera strings reutilizando glifos do subset FreeSans, recompacta com header 0x78 0x9C (idêntico ao iText 2.1.7) e reconstrói uma única tabela xref mantendo Creator=JasperReports 5.6.1.",
            "CT-02A, CT-02B, CT-03A, CT-03B, CT-07A, CT-07B",
            "1. Validação do Dígito Verificador Módulo 11 do CPF (barra 250.713.388-88).\n2. Auditoria do histograma de glifos do subset TrueType (/Widths) vs caracteres efetivamente presentes no stream.\n3. Batimento cadastral e temporal no IU Docs.",
            "IU_DOCS.BusinessRule == FALSE OR CERTA.FontSubsetOrphanGlyph == TRUE -> BLOCK",
            "HIGH: STEALTH_STREAM_EDIT_OR_IDENTITY_MISMATCH",
        ],
        [
            "SEC-02",
            "Camada Gráfica & Metadados",
            "Edição Visual, Whiteout e Print-to-PDF: Uso de editores externos (Canva, iLovePDF, Foxit), cobertura de valores com retângulo branco (1 1 1 rg re f) ou achatamento via Microsoft Print to PDF.",
            "CT-05A, CT-05B, CT-05C",
            "1. Proibição de Incremental Updates (múltiplos %%EOF e /Prev).\n2. Whitelist estrita de Creator (JasperReports 5.6.1) e Producer (iText 2.1.7), bloqueando Microsoft Print to PDF.\n3. Detecção de Bounding Box Collision (texto oculto sob retângulo branco).",
            "CERTA.IncrementalUpdate == TRUE OR CERTA.WhiteoutOverlay == TRUE OR CERTA.FlattenedPDF == TRUE -> BLOCK",
            "CRITICAL: VISUAL_TAMPERING_OR_FLATTENED_PDF",
        ],
        [
            "SEC-03",
            "Camada Tipográfica & Dual-Layer",
            "Fontes Intrusas e OCR/Parser Poisoning: Injeção de fonte /F4 Courier-Bold, desalinhamento de matriz Tm (+3.57pt) ou texto invisível '3 Tr' (250.000,00 invisível sobre 31.134,89 visível).",
            "CT-06A, CT-06B, CT-06C",
            "1. Whitelist de dicionário /Font (apenas /F1, /F2, /F3).\n2. Verificação de matriz unitária '1 0 0 1 X Y Tm' e tamanho 8 Tf.\n3. Bloqueio imediato de Text Rendering Mode 3 ('3 Tr') e fontes microscópicas (< 1 Tf).",
            "CERTA.ForeignFont == TRUE OR CERTA.InvisibleText3Tr == TRUE OR CERTA.MatrixDrift == TRUE -> BLOCK",
            "CRITICAL: TYPOGRAPHIC_INJECTION_OR_3TR_POISONING",
        ],
        [
            "SEC-04",
            "Ponto Cego RFB (Item 7) — Matemática Parcial vs. Perfeita",
            "Alavancagem Fictícia de Renda: Em CT-07A altera apenas o Total para 153.551,12; em CT-07B recalcula TODA a Página 7 (Base 136.796,78, Imposto 26.765,33, Alíquota 17,43%, Saldo 25.581,68, Quota 3.197,71).",
            "CT-07A, CT-07B",
            "1. Para CT-07A: Validação da Equação Tributária na Pág. 7 e proporcionalidade Salário vs IRRF/13º na Pág. 1.\n2. Para CT-07B: Ativação do Item 7 via API Conecta gov.br / SERPRO para validar o recibo e os valores diretamente na Receita Federal.",
            "IU_DOCS.TaxMathValid == FALSE OR SERPRO_RFB.CrossCheck == FALSE -> BLOCK",
            "CRITICAL: UNVERIFIED_RFB_RECEIPT_OR_TAX_MATH_FRAUD",
        ],
        [
            "SEC-05",
            "Segurança da Aplicação (AppSec Upload)",
            "Ataques ao Parser e à Mesa de Crédito: Upload de PDF criptografado (/Encrypt) para travar workers ou injeção de /OpenAction /JavaScript (Stored XSS) e /URI (SSRF Canary).",
            "CT-08A, CT-08B",
            "1. Rejeição síncrona Fail-Closed (HTTP 422) de PDFs com tag /Encrypt.\n2. Varredura e bloqueio de tags /OpenAction, /AA, /JS, /JavaScript, /Launch, /EmbeddedFiles e /URI antes de qualquer renderização.",
            "GATEWAY.HasEncrypt == TRUE OR CERTA.HasActiveContent == TRUE -> REJECT_422_AND_ALERT_SOC",
            "CRITICAL: APPSEC_MALICIOUS_PDF_PAYLOAD",
        ],
    ]
    widths = [12, 28, 52, 28, 55, 45, 38]
    return rows, widths


def get_sheet4_data() -> Tuple[List[List[str]], List[int]]:
    headers = [
        "Página",
        "Seção do Documento Original",
        "Campo / Rótulo Oficial RFB",
        "Valor Exato no Documento Original (GILSONEI-IRPF-2026-2025-origi-imagem-declaracao.pdf)",
    ]
    rows = [
        headers,
        ["Págs. 1 a 8", "Cabeçalho Fixo", "NOME / CPF", "GILSONEI DOS SANTOS | 250.713.388-07"],
        ["Págs. 1 a 8", "Cabeçalho Fixo", "TÍTULO / VIGÊNCIA", "DECLARAÇÃO DE AJUSTE ANUAL | IMPOSTO SOBRE A RENDA - PESSOA FÍSICA | EXERCÍCIO 2026 | ANO-CALENDÁRIO 2025"],
        ["Págs. 1 a 8", "Marca d'Água e Rodapé", "Marca d'Água / Paginação", "PROTEGIDA POR SIGILO FISCAL | Página 1 de 8 até Página 8 de 8"],
        ["Página 1", "IDENTIFICAÇÃO DO CONTRIBUINTE", "Data de Nascimento / Raça/Cor", "30/01/1977 | Parda"],
        ["Página 1", "IDENTIFICAÇÃO DO CONTRIBUINTE", "Endereço Completo", "AEROPORTO ALAN KARDEC DA SILVA, Nº 70, Compl. 18710378, Bairro NASCER DO SOL, ARANDU - SP, CEP 18710-378"],
        ["Página 1", "IDENTIFICAÇÃO DO CONTRIBUINTE", "Natureza da Ocupação / Ocupação Principal", "41 - MEMBRO OU SERVIDOR PÚBLICO DA ADMINISTRAÇÃO DIRETA MUNICIPAL | 519 - OUTROS TRABALHADORES DE SERVIÇOS DIVERSOS"],
        ["Página 1", "IDENTIFICAÇÃO DO CONTRIBUINTE", "Tipo de Declaração / Recibo Anterior", "Declaração de Ajuste Anual Original | Nº do recibo da última declaração entregue do exercício de 2025: 11.26.13.14.00-02"],
        ["Página 1", "ALIMENTANDOS", "Beneficiário / Decisão Judicial", "KAMILE VITORIA DOS SANTOS | Nasc: 09/07/2003 | CPF: 526.161.888-64 | Vara cível: 1 | Comarca: AVARE - SP | Decisão: 10/07/2015"],
        ["Página 1", "RENDIMENTOS TRIBUTÁVEIS PJ (TITULAR)", "Fonte Pagadora 1", "PREFEITURA MUNICIPAL DE ARANDU (46.634.176/0001-04) | Rend: 31.134,89 | Prev: 4.012,68 | IRRF: 88,12 | 13º: 2.112,55 | IRRF 13º: 0,00"],
        ["Página 1", "RENDIMENTOS TRIBUTÁVEIS PJ (TITULAR)", "Fonte Pagadora 2", "JOSE EDUARDO DIAS SOARES (004.659.338-15) | Rend: 36.416,23 | Prev: 3.221,10 | IRRF: 758,57 | 13º: 3.359,76 | IRRF 13º: 83,51"],
        ["Página 2", "RENDIMENTOS TRIBUTÁVEIS PJ (TITULAR)", "Fonte Pagadora 3", "CAMARA MUNICIPAL DE ARANDU (50.366.467/0001-28) | Rend: 36.000,00 | Prev: 3.040,80 | IRRF: 336,96 | 13º: 2.722,76 | IRRF 13º: 23,84"],
        ["Página 2", "RENDIMENTOS TRIBUTÁVEIS PJ (TITULAR)", "TOTAL RENDIMENTOS PJ", "Rend: 103.551,12 | Prev: 10.274,58 | IRRF: 1.183,65 | 13º: 8.195,07 | IRRF 13º: 107,35"],
        ["Página 2", "TRIBUTAÇÃO EXCLUSIVA / DEFINITIVA", "01. 13º salário / TOTAL", "8.195,07 | TOTAL: 8.195,07"],
        ["Página 3", "IMPOSTO PAGO / RETIDO", "04. Imposto retido na fonte do titular", "1.183,65 (demais itens 0,00)"],
        ["Página 3", "PAGAMENTOS EFETUADOS", "Cód. 30 - Pensão Alimentícia", "KAMILE VITORIA DOS SANTOS (526.161.888-64) | Valor Pago: 6.071,40 | Parc. Não Dedutível: 0,00"],
        ["Páginas 4, 5 e 6", "ATIVIDADE RURAL / GANHOS DE CAPITAL / RENDA VARIÁVEL", "Todas as seções", "Sem Informações"],
        ["Página 7", "RESUMO — DESCONTO SIMPLIFICADO", "Rendimentos / Desconto / Base / Imposto", "Total Rendimentos: 103.551,12 | Desconto Simplificado: 16.754,34 | Base de Cálculo: 86.796,78 | Imposto Devido: 13.015,33 | Alíquota Efetiva: 12,56%"],
        ["Página 7", "RESUMO — IMPOSTO PAGO E SALDO", "Imposto Pago / Saldo a Pagar / Quotas", "Total Imposto Pago: 1.183,65 | Imposto a Restituir: 0,00 | SALDO IMPOSTO A PAGAR: 11.831,68 | 8 quotas de 1.478,96 | Débito automático: NÃO"],
        ["Página 8", "EVOLUÇÃO PATRIMONIAL E OUTRAS INFORMAÇÕES", "Bens, Dívidas e Outras Informações", "Bens e Dívidas 2024/2025: 0,00 | Rendimentos sujeitos à tributação exclusiva/definitiva: 8.195,07"],
        ["Metadados PDF", "Assinatura Binária Original", "Info / Fontes / XRef", "Creator: JasperReports Library version 5.6.1 | Producer: iText 2.1.7 by 1T3XT | Fontes: Helvetica, QWIOTU+FreeSansBold, ZBXMLK+FreeSans"],
    ]
    widths = [16, 38, 36, 85]
    return rows, widths


def create_xlsx_file(target_path: Path) -> None:
    s1_rows, s1_w = get_sheet1_data()
    s2_rows, s2_w = get_sheet2_data()
    s3_rows, s3_w = get_sheet3_data()
    s4_rows, s4_w = get_sheet4_data()

    content_types = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
  <Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>
  <Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
  <Override PartName="/xl/worksheets/sheet2.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
  <Override PartName="/xl/worksheets/sheet3.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
  <Override PartName="/xl/worksheets/sheet4.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
</Types>
"""

    root_rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>
"""

    workbook_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
          xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <sheets>
    <sheet name="1_Matriz_IUDocs_vs_Certa" sheetId="1" r:id="rId1"/>
    <sheet name="2_Roteiro_de_Teste_26_Casos" sheetId="2" r:id="rId2"/>
    <sheet name="3_Seguranca_Red_e_Blue_Team" sheetId="3" r:id="rId3"/>
    <sheet name="4_Baseline_Texto_Original_RFB" sheetId="4" r:id="rId4"/>
  </sheets>
</workbook>
"""

    workbook_rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet2.xml"/>
  <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet3.xml"/>
  <Relationship Id="rId4" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet4.xml"/>
  <Relationship Id="rId5" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
</Relationships>
"""

    with zipfile.ZipFile(target_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", content_types.strip())
        zf.writestr("_rels/.rels", root_rels.strip())
        zf.writestr("xl/workbook.xml", workbook_xml.strip())
        zf.writestr("xl/_rels/workbook.xml.rels", workbook_rels.strip())
        zf.writestr("xl/styles.xml", build_styles_xml().strip())
        zf.writestr("xl/worksheets/sheet1.xml", build_sheet_xml(s1_rows, s1_w, is_orange_header=True))
        zf.writestr("xl/worksheets/sheet2.xml", build_sheet_xml(s2_rows, s2_w, is_orange_header=False))
        zf.writestr("xl/worksheets/sheet3.xml", build_sheet_xml(s3_rows, s3_w, is_orange_header=False))
        zf.writestr("xl/worksheets/sheet4.xml", build_sheet_xml(s4_rows, s4_w, is_orange_header=True))


if __name__ == "__main__":
    create_xlsx_file(XLSX_MAIN)
    print(f"Planilha gerada com sucesso: {XLSX_MAIN} ({XLSX_MAIN.stat().st_size} bytes)")
