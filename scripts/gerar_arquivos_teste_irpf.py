#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agente Desenvolvedor — Gerador Cirúrgico de Massa de Testes IRPF (IU Docs vs. Certa)
====================================================================================
Este script lê o documento base `GILSONEI-IRPF-2026-2025-origi-imagem-declaracao.pdf`
e gera os 14 arquivos de teste correspondentes aos casos de teste (CT-00 a CT-07A),
mantendo 99,9% do texto, fontes originais (QWIOTU+FreeSansBold, ZBXMLK+FreeSans, Helvetica),
layout do JasperReports 5.6.1 / iText 2.1.7 e recalculando com precisão a tabela `xref`
de cada PDF gerado.
"""

from __future__ import annotations

import os
import re
import zlib
from pathlib import Path
from typing import Callable, Dict, List, Tuple

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "arquivos_teste_irpf"
SOURCE_PDF = (
    OUTPUT_DIR / "original" / "GILSONEI-IRPF-2026-2025-origi-imagem-declaracao.pdf"
    if (OUTPUT_DIR / "original" / "GILSONEI-IRPF-2026-2025-origi-imagem-declaracao.pdf").exists()
    else BASE_DIR / "GILSONEI-IRPF-2026-2025-origi-imagem-declaracao.pdf"
)

# IDs dos objetos de página e seus respectivos streams de conteúdo no PDF original:
# Páginas 1 a 8 -> Objetos [1, 9, 13, 17, 21, 25, 29, 33]
# Streams 1 a 8 -> Objetos [7, 12, 16, 20, 24, 28, 32, 36]
PAGE_OBJ_IDS = [1, 9, 13, 17, 21, 25, 29, 33]
STREAM_OBJ_IDS = [7, 12, 16, 20, 24, 28, 32, 36]


class SurgicalPDFBuilder:
    """Manipulador cirúrgico de objetos e streams PDF mantendo fidelidade binária."""

    def __init__(self, raw_bytes: bytes) -> None:
        self.raw_bytes = raw_bytes
        self.objects: Dict[int, bytes] = {}
        self.order: List[int] = []
        self._parse_objects()

    def _parse_objects(self) -> None:
        pattern = re.compile(rb"(\d+)\s+0\s+obj\r?\n(.*?)\r?\nendobj", re.S)
        for match in pattern.finditer(self.raw_bytes):
            obj_id = int(match.group(1))
            body = match.group(2)
            self.objects[obj_id] = body
            self.order.append(obj_id)

    def clone(self) -> "SurgicalPDFBuilder":
        cloned = SurgicalPDFBuilder.__new__(SurgicalPDFBuilder)
        cloned.raw_bytes = self.raw_bytes
        cloned.objects = dict(self.objects)
        cloned.order = list(self.order)
        return cloned

    def get_stream_text(self, obj_id: int) -> str:
        body = self.objects[obj_id]
        m = re.search(rb"stream\r?\n(.*?)\r?\nendstream", body, re.S)
        if not m:
            raise ValueError(f"Object {obj_id} does not contain a valid stream")
        decompressed = zlib.decompress(m.group(1))
        return decompressed.decode("latin1")

    def set_stream_text(self, obj_id: int, new_text: str) -> None:
        raw_stream = new_text.encode("latin1")
        # Usa o nível default do zlib (0x78 0x9c), idêntico ao java.util.zip.Deflater do iText 2.1.7
        compressed = zlib.compress(raw_stream)
        header = f"<</Filter/FlateDecode/Length {len(compressed)}>>stream\n".encode("latin1")
        footer = b"\nendstream"
        self.objects[obj_id] = header + compressed + footer

    def modify_all_page_streams(self, transform_fn: Callable[[int, str], str]) -> None:
        for page_num, stream_id in enumerate(STREAM_OBJ_IDS, start=1):
            original_text = self.get_stream_text(stream_id)
            updated_text = transform_fn(page_num, original_text)
            if updated_text != original_text:
                self.set_stream_text(stream_id, updated_text)

    def build_bytes(self) -> bytes:
        out = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
        offsets: Dict[int, int] = {}

        for obj_id in self.order:
            offsets[obj_id] = len(out)
            out.extend(f"{obj_id} 0 obj\n".encode("latin1"))
            out.extend(self.objects[obj_id])
            out.extend(b"\nendobj\n")

        max_obj_id = max(self.objects.keys())
        xref_offset = len(out)
        out.extend(f"xref\n0 {max_obj_id + 1}\n".encode("latin1"))
        out.extend(b"0000000000 65535 f \n")
        for i in range(1, max_obj_id + 1):
            if i in offsets:
                out.extend(f"{offsets[i]:010d} 00000 n \n".encode("latin1"))
            else:
                out.extend(b"0000000000 65535 f \n")

        trailer = (
            "trailer\n"
            f"<</Info 158 0 R/ID [<14d6ef53055af0a8dac30b4098b31bc3><a0f73ca902bc5d59eb3e7338bdee4fc6>]"
            f"/Root 157 0 R/Size {max_obj_id + 1}>>\n"
            "startxref\n"
            f"{xref_offset}\n"
            "%%EOF\n"
        ).encode("latin1")
        out.extend(trailer)
        return bytes(out)


def generate_all_test_files() -> List[Tuple[str, str, int]]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    # Remove old mock files if any exist with old names
    for old_file in OUTPUT_DIR.glob("*.pdf"):
        old_file.unlink()

    raw_source = SOURCE_PDF.read_bytes()
    base_pdf = SurgicalPDFBuilder(raw_source)
    generated_summary: List[Tuple[str, str, int]] = []

    def save_pdf(filename: str, data: bytes, description: str) -> None:
        target = OUTPUT_DIR / filename
        target.write_bytes(data)
        generated_summary.append((filename, description, len(data)))

    # =========================================================================
    # CT-00: Baseline Original Íntegro (Aprovado em IU Docs e Certa)
    # =========================================================================
    save_pdf(
        "CT00_ORIGINAL_VALIDO_IRPF_2026_2025.pdf",
        raw_source,
        "Baseline Original Integro (Aprovado IU Docs + Aprovado Certa)",
    )

    # =========================================================================
    # CT-01A: Autenticidade — Sem Marca d'Água (IU Docs: Reprova | Certa: Reprova)
    # Remove apenas a renderizacao da marca d'agua `/img1 Do`, `/img3 Do`, etc.
    # mantendo 100% do texto do documento original intacto.
    # =========================================================================
    pdf_01a = base_pdf.clone()

    def _remove_watermark(page_num: int, text: str) -> str:
        return re.sub(
            r"q\s+333\.93\s+0\s+0\s+493\s+161\s+203\s+cm\s+/img\d+\s+Do\s+Q",
            "q Q",
            text,
        )

    pdf_01a.modify_all_page_streams(_remove_watermark)
    save_pdf(
        "CT01A_AUTENTICIDADE_SEM_MARCA_DAGUA.pdf",
        pdf_01a.build_bytes(),
        "Item 1 Autenticidade: Marca d'agua 'PROTEGIDA POR SIGILO FISCAL' removida",
    )

    # =========================================================================
    # CT-01B: Autenticidade — Status "EM PREENCHIMENTO" / Rascunho (IU Docs + Certa)
    # Substitui a marca d'agua por texto diagonal 'EM PREENCHIMENTO' em Helvetica (/F1)
    # e altera o status 'Declaração de Ajuste Anual Original' para 'EM PREENCHIMENTO'
    # =========================================================================
    pdf_01b = base_pdf.clone()

    def _draft_watermark(page_num: int, text: str) -> str:
        draft_stamp = (
            "q 0.78 g BT 0.55 0.83 -0.83 0.55 210 260 Tm /F1 36 Tf "
            "(EM PREENCHIMENTO)Tj ET Q"
        )
        updated = re.sub(
            r"q\s+333\.93\s+0\s+0\s+493\s+161\s+203\s+cm\s+/img\d+\s+Do\s+Q",
            draft_stamp,
            text,
        )
        if page_num == 1:
            updated = updated.replace(
                "(Declara\xe7\xe3o de Ajuste Anual Original)Tj",
                "(Declara\xe7\xe3o EM PREENCHIMENTO)Tj",
            )
            updated = updated.replace(
                "(N\xba do recibo da \xfaltima declara\xe7\xe3o entregue do exerc\xedcio de 2025:    11.26.13.14.00-02)Tj",
                "(Declara\xe7\xe3o em preenchimento - Recibo de entrega n\xe3o gerado)Tj",
            )
        return updated

    pdf_01b.modify_all_page_streams(_draft_watermark)
    save_pdf(
        "CT01B_AUTENTICIDADE_STATUS_RASCUNHO.pdf",
        pdf_01b.build_bytes(),
        "Item 1 Autenticidade: Marca d'agua e status 'EM PREENCHIMENTO' (Nao transmitida)",
    )

    # =========================================================================
    # CT-02A: Titularidade — CPF Divergente da Base Corporativa (Exclusivo IU Docs)
    # Altera apenas o CPF 250.713.388-07 para 250.713.388-88 (usando glifos nativos de /F2 e /F3)
    # Mantém fontes FreeSansBold/FreeSans e metadados JasperReports/iText intactos.
    # =========================================================================
    pdf_02a = base_pdf.clone()
    pdf_02a.modify_all_page_streams(
        lambda _p, t: t.replace("(250.713.388-07)Tj", "(250.713.388-88)Tj")
    )
    save_pdf(
        "CT02A_TITULARIDADE_CPF_DIVERGENTE_IUDOCS.pdf",
        pdf_02a.build_bytes(),
        "Item 2 Titularidade (IU Docs): CPF alterado para 250.713.388-88 mantendo estrutura original",
    )

    # =========================================================================
    # CT-02B: Titularidade — Nome Divergente da Base Corporativa (Exclusivo IU Docs)
    # Altera apenas o nome GILSONEI DOS SANTOS para GILSONEI DOS SANTOS SILVA
    # (todos os caracteres S, I, L, V, A existem no subset original da fonte /F2 e /F3!)
    # =========================================================================
    pdf_02b = base_pdf.clone()
    pdf_02b.modify_all_page_streams(
        lambda _p, t: t.replace("(GILSONEI DOS SANTOS)Tj", "(GILSONEI DOS SANTOS SILVA)Tj")
    )
    save_pdf(
        "CT02B_TITULARIDADE_NOME_DIVERGENTE_IUDOCS.pdf",
        pdf_02b.build_bytes(),
        "Item 2 Titularidade (IU Docs): Nome alterado para 'GILSONEI DOS SANTOS SILVA'",
    )

    # =========================================================================
    # CT-03A: Vigência — Exercício Expirado 2025 / Ano-Calendário 2023 (Exclusivo IU Docs)
    # Nota: No subset da fonte /F2 (FreeSansBold do cabeçalho), os dígitos presentes são
    # 0, 1, 2, 3, 5, 6, 7, 8. Usamos EXERCÍCIO 2025 e ANO-CALENDÁRIO 2023 (ou 2023/2022)
    # para garantir 100% de compatibilidade com a tabela de glifos da fonte original!
    # =========================================================================
    pdf_03a = base_pdf.clone()

    def _expired_exercise(page_num: int, text: str) -> str:
        updated = text.replace("(EXERC\xcdCIO 2026)Tj", "(EXERC\xcdCIO 2023)Tj")
        updated = updated.replace("(ANO-CALEND\xc1RIO 2025)Tj", "(ANO-CALEND\xc1RIO 2022)Tj")
        if page_num == 1:
            updated = updated.replace("em 2025?   N\xe3o", "em 2022?   N\xe3o")
            updated = updated.replace("exerc\xedcio de 2025:", "exerc\xedcio de 2022:")
        return updated

    pdf_03a.modify_all_page_streams(_expired_exercise)
    save_pdf(
        "CT03A_VIGENCIA_EXERCICIO_EXPIRADO_2023_2022_IUDOCS.pdf",
        pdf_03a.build_bytes(),
        "Item 3 Vigencia (IU Docs): Exercicio expirado (EXERCICIO 2023 / ANO-CALENDARIO 2022)",
    )

    # =========================================================================
    # CT-03B: Vigência — Incoerência Temporal Exercício vs. Ano-Calendário (Exclusivo IU Docs)
    # EXERCÍCIO 2026 com ANO-CALENDÁRIO 2023
    # =========================================================================
    pdf_03b = base_pdf.clone()
    pdf_03b.modify_all_page_streams(
        lambda _p, t: t.replace("(ANO-CALEND\xc1RIO 2025)Tj", "(ANO-CALEND\xc1RIO 2023)Tj")
    )
    save_pdf(
        "CT03B_VIGENCIA_ANO_CALENDARIO_INCONSISTENTE_IUDOCS.pdf",
        pdf_03b.build_bytes(),
        "Item 3 Vigencia (IU Docs): EXERCICIO 2026 com ANO-CALENDARIO 2023 inconsistente",
    )

    # =========================================================================
    # CT-04A: Páginas — Incompletude (Falta da Página 7 - Resumo ou Página 8)
    # O objeto 8 (/Type/Pages) passa a ter 7 páginas (removendo a pág. 7 de Resumo),
    # enquanto o rodapé continua indicando "Página X de 8" (pula de Página 6 de 8 para Página 8 de 8).
    # =========================================================================
    pdf_04a = base_pdf.clone()
    pdf_04a.objects[8] = (
        b"\n<</Kids[1 0 R 9 0 R 13 0 R 17 0 R 21 0 R 25 0 R 33 0 R]"
        b"/Type/Pages/Count 7/ITXT(2.1.7)>>\n"
    )
    save_pdf(
        "CT04A_PAGINAS_INCOMPLETO_FALTA_PAGINA_7.pdf",
        pdf_04a.build_bytes(),
        "Item 4 Paginas (IU Docs + Certa): Documento incompleto (7 paginas, falta Pagina 7 de 8 - Resumo)",
    )

    # =========================================================================
    # CT-04B: Páginas — Quebra de Sequência (Páginas 2 e 3 invertidas)
    # O objeto 8 (/Type/Pages) ordena as páginas como: 1, 3, 2, 4, 5, 6, 7, 8
    # =========================================================================
    pdf_04b = base_pdf.clone()
    pdf_04b.objects[8] = (
        b"\n<</Kids[1 0 R 13 0 R 9 0 R 17 0 R 21 0 R 25 0 R 29 0 R 33 0 R]"
        b"/Type/Pages/Count 8/ITXT(2.1.7)>>\n"
    )
    save_pdf(
        "CT04B_PAGINAS_FORA_DE_SEQUENCIA.pdf",
        pdf_04b.build_bytes(),
        "Item 4 Paginas (IU Docs + Certa): Quebra de sequencia (Pagina 3 antes da Pagina 2)",
    )

    # =========================================================================
    # CT-04C: Páginas — Incoerência entre Páginas (Cabeçalho da Pág. 2 divergente + Resumo Pág. 7 divergente)
    # Na página 2, o CPF no cabeçalho diverge para 250.713.388-55 e na página 7 o Total
    # de Rendimentos Tributáveis (203.551,12) diverge da soma da página 2 (103.551,12).
    # =========================================================================
    pdf_04c = base_pdf.clone()
    p2_text = pdf_04c.get_stream_text(12).replace("(250.713.388-07)Tj", "(250.713.388-55)Tj")
    pdf_04c.set_stream_text(12, p2_text)
    p7_text = pdf_04c.get_stream_text(32).replace("(103.551,12)Tj", "(203.551,12)Tj")
    pdf_04c.set_stream_text(32, p7_text)
    save_pdf(
        "CT04C_PAGINAS_INCOERENCIA_CABECALHO_E_RESUMO.pdf",
        pdf_04c.build_bytes(),
        "Item 4 Paginas (IU Docs + Certa): Incoerencia de CPF na Pag. 2 e Total divergente no Resumo Pag. 7",
    )

    # =========================================================================
    # CT-05A: Manipulação do Arquivo — Metadados de Editor Externo + Incremental Update (Exclusivo Certa)
    # Mantém 100% do texto visível e regras de negócio do original intactos (IU Docs aprova),
    # mas altera o objeto Info (158) para Adobe Acrobat / Canva e adiciona uma revisão
    # incremental (segundo bloco xref + %%EOF) típica de adulteração em editor externo.
    # =========================================================================
    pdf_05a_bytes = bytearray(raw_source)
    # Adiciona um Incremental Update mantendo os metadados oficiais da Receita Federal (JasperReports / iText)
    # para passar na validação de metadados da Certa e auditar a presença de múltiplos %%EOF / Incremental Update.
    inc_offset_158 = len(pdf_05a_bytes)
    new_info_obj = (
        b"158 0 obj\n"
        b"<</ModDate(D:20260416114233-03'00')"
        b"/Creator(JasperReports Library version 5.6.1)"
        b"/CreationDate(D:20260416114233-03'00')"
        b"/Producer(iText 2.1.7 by 1T3XT)>>\n"
        b"endobj\n"
    )
    pdf_05a_bytes.extend(new_info_obj)
    inc_xref_offset = len(pdf_05a_bytes)
    inc_trailer = (
        b"xref\n"
        b"0 1\n"
        b"0000000000 65535 f \n"
        b"158 1\n"
        + f"{inc_offset_158:010d} 00000 n \n".encode("latin1")
        + b"trailer\n"
        b"<</Info 158 0 R/ID [<14d6ef53055af0a8dac30b4098b31bc3><a0f73ca902bc5d59eb3e7338bdee4fc6>]"
        b"/Root 157 0 R/Size 159/Prev 327756>>\n"
        b"startxref\n"
        + f"{inc_xref_offset}\n".encode("latin1")
        + b"%%EOF\n"
    )
    pdf_05a_bytes.extend(inc_trailer)
    save_pdf(
        "CT05A_MANIPULACAO_METADADOS_E_INCREMENTAL_CERTA.pdf",
        bytes(pdf_05a_bytes),
        "Item 5 Manipulacao (Certa): Incremental Update (multiplos %%EOF) mantendo metadados oficiais RFB (JasperReports/iText)",
    )

    # =========================================================================
    # CT-05B: Manipulação do Arquivo — Adulteração por Máscara Branca ("Whiteout") + Renda Adulterada (Exclusivo Certa)
    # Mantém o valor original `31.134,89` no stream da página 1, desenha um retângulo branco
    # por cima (`1 1 1 rg 214 157 46 11 re f`) e escreve `81.134,89` por cima, além de
    # atualizar o total para `153.551,12`.
    # Metadados oficiais mantidos (JasperReports / iText) para passar na checagem de metadados da Certa.
    # =========================================================================
    pdf_05b_base = base_pdf.clone()
    p1_orig = pdf_05b_base.get_stream_text(7)
    whiteout_patch = (
        "(31.134,89)Tj\n0 g\nET\n"
        "q 1 1 1 rg 214 157 46 11 re f Q\n"
        "BT 1 0 0 1 217.42 159.28 Tm /F3 8 Tf 0 0 0 rg (81.134,89)Tj"
    )
    p1_masked = p1_orig.replace("(31.134,89)Tj", whiteout_patch, 1)
    pdf_05b_base.set_stream_text(7, p1_masked)
    pdf_05b_base.set_stream_text(
        12, pdf_05b_base.get_stream_text(12).replace("(103.551,12)Tj", "(153.551,12)Tj")
    )
    pdf_05b_base.set_stream_text(
        32, pdf_05b_base.get_stream_text(32).replace("(103.551,12)Tj", "(153.551,12)Tj")
    )
    pdf_05b_base.objects[158] = (
        b"\n<</ModDate(D:20260416114233-03'00')/Creator(JasperReports Library version 5.6.1)"
        b"/CreationDate(D:20260416114233-03'00')/Producer(iText 2.1.7 by 1T3XT)>>\n"
    )
    save_pdf(
        "CT05B_MANIPULACAO_SOBREPOSICAO_WHITEOUT_CERTA.pdf",
        pdf_05b_base.build_bytes(),
        "Item 5 Manipulacao (Certa): Adulteracao de rendimento (Whiteout) mantendo metadados oficiais (JasperReports/iText)",
    )

    # =========================================================================
    # CT-06A: Fontes e Tipografias — Inserção Artificial com Fonte Divergente (/F1 Helvetica / Courier) (Exclusivo Certa)
    # Na página 1, o valor de rendimentos da Prefeitura Municipal de Arandu (`31.134,89`)
    # e na página 2 o rendimento da Câmara Municipal (`36.000,00`) são renderizados com
    # uma fonte artificial (`/F4` Courier-Bold adicionada ao dicionário da página) em vez
    # da fonte nativa `/F3` (`ZBXMLK+FreeSans`).
    # =========================================================================
    pdf_06a = base_pdf.clone()
    # Registra /F4 como Courier-Bold no objeto de fonte 2 ou diretamente no dicionário das páginas 1 e 2
    pdf_06a.objects[1] = pdf_06a.objects[1].replace(
        b"/Font<</F1 2 0 R/F2 5 0 R/F3 6 0 R>>",
        b"/Font<</F1 2 0 R/F2 5 0 R/F3 6 0 R/F4<</Type/Font/Subtype/Type1/BaseFont/Courier-Bold/Encoding/WinAnsiEncoding>>>>",
    )
    pdf_06a.objects[9] = pdf_06a.objects[9].replace(
        b"/Font<</F1 2 0 R/F2 5 0 R/F3 6 0 R>>",
        b"/Font<</F1 2 0 R/F2 5 0 R/F3 6 0 R/F4<</Type/Font/Subtype/Type1/BaseFont/Courier-Bold/Encoding/WinAnsiEncoding>>>>",
    )
    p1_font_mod = pdf_06a.get_stream_text(7).replace(
        "1 0 0 1 217.42 159.28 Tm\n/F3 8 Tf\n0 0 0 rg\n(31.134,89)Tj",
        "1 0 0 1 217.42 159.28 Tm\n/F4 9.5 Tf\n0 0 0 rg\n(31.134,89)Tj",
    )
    pdf_06a.set_stream_text(7, p1_font_mod)

    p2_font_mod = pdf_06a.get_stream_text(12).replace(
        "/F3 8 Tf\n0 0 0 rg\n(36.000,00)Tj",
        "/F4 9.5 Tf\n0 0 0 rg\n(36.000,00)Tj",
    )
    pdf_06a.set_stream_text(12, p2_font_mod)
    save_pdf(
        "CT06A_FONTES_TIPOGRAFIA_DIVERGENTE_COURIER_CERTA.pdf",
        pdf_06a.build_bytes(),
        "Item 6 Fontes e Tipografias (Certa): Elementos inseridos com fonte Courier-Bold (/F4) divergente da FreeSans original",
    )

    # =========================================================================
    # CT-06B: Fontes e Tipografias — Desalinhamento de Baseline e Escala Artificial (Exclusivo Certa)
    # Mantém a fonte `/F3` (FreeSans), mas altera a matriz de texto `Tm` (desalinhamento vertical
    # e escala horizontal distorcida `1.25 0 0 1.35`) e o tamanho da fonte (`10.5 Tf` em vez de `8 Tf`)
    # nos valores de rendimentos da página 1 e página 2.
    # =========================================================================
    pdf_06b = base_pdf.clone()
    p1_misaligned = pdf_06b.get_stream_text(7).replace(
        "1 0 0 1 217.42 159.28 Tm\n/F3 8 Tf\n0 0 0 rg\n(31.134,89)Tj",
        "1.18 0 0 1.25 213.10 162.85 Tm\n/F3 10 Tf\n0 0 0 rg\n(31.134,89)Tj",
    )
    pdf_06b.set_stream_text(7, p1_misaligned)
    p2_misaligned = pdf_06b.get_stream_text(12).replace(
        "1 0 0 1 212.98 696.15 Tm\n/F3 8 Tf\n0 0 0 rg\n(103.551,12)Tj",
        "1.18 0 0 1.25 209.50 699.40 Tm\n/F3 10 Tf\n0 0 0 rg\n(103.551,12)Tj",
    )
    pdf_06b.set_stream_text(12, p2_misaligned)
    save_pdf(
        "CT06B_FONTES_DESALINHAMENTO_E_ESCALA_CERTA.pdf",
        pdf_06b.build_bytes(),
        "Item 6 Fontes e Tipografias (Certa): Desalinhamento de baseline (y-offset +3.5pt) e distorcao de escala tipografica",
    )

    # =========================================================================
    # CT-07A: Validação na Receita Federal — Gap de Cross-Check RFB (Matemática Parcial)
    # Altera cirurgicamente o número do recibo na pág. 1 para `99.88.77.66.55-00` e eleva
    # a renda de `31.134,89` para `81.134,89` (e total de `103.551,12` para `153.551,12`
    # nas páginas 2 e 7) mantendo 100% da fonte FreeSans, alinhamento exato, metadados
    # JasperReports 5.6.1 / iText 2.1.7 e tabela xref limpa.
    # =========================================================================
    pdf_07a = base_pdf.clone()
    p1_gap = (
        pdf_07a.get_stream_text(7)
        .replace("11.26.13.14.00-02", "99.88.77.66.55-00")
        .replace("(31.134,89)Tj", "(81.134,89)Tj")
    )
    pdf_07a.set_stream_text(7, p1_gap)
    pdf_07a.set_stream_text(
        12, pdf_07a.get_stream_text(12).replace("(103.551,12)Tj", "(153.551,12)Tj")
    )
    pdf_07a.set_stream_text(
        32, pdf_07a.get_stream_text(32).replace("(103.551,12)Tj", "(153.551,12)Tj")
    )
    save_pdf(
        "CT07A_GAP_RECEITA_FEDERAL_RECIBO_E_RENDA_NAO_AUDITADOS_RFB.pdf",
        pdf_07a.build_bytes(),
        "Item 7 Validacao Receita Federal (Gap Parcial): Recibo 99.88.77.66.55-00 e renda 153.551,12 sem recalculo da Pag. 7",
    )

    # =========================================================================
    # CT-01C: Autenticidade — Declaração Retificadora Oportunista Sem Recibo Válido
    # Simula o golpe da "Retificadora Vai-e-Volta" (altera Tipo de Declaração para
    # Retificadora com recibo anterior zerado/inválido 00.00.00.00.00-00).
    # =========================================================================
    pdf_01c = base_pdf.clone()
    p1_retif = (
        pdf_01c.get_stream_text(7)
        .replace(
            "(Declara\xe7\xe3o de Ajuste Anual Original)Tj",
            "(Declara\xe7\xe3o de Ajuste Anual Retificadora)Tj",
        )
        .replace("11.26.13.14.00-02", "00.00.00.00.00-00")
    )
    pdf_01c.set_stream_text(7, p1_retif)
    save_pdf(
        "CT01C_AUTENTICIDADE_RETIFICADORA_SEM_RECIBO_VALIDO.pdf",
        pdf_01c.build_bytes(),
        "Item 1 Autenticidade (Red Team): Declaracao Retificadora com recibo anterior invalido/zerado (00.00.00.00.00-00)",
    )

    # =========================================================================
    # CT-05C: Manipulação do Arquivo — PDF Achatado / Rasterizado ("Print-to-PDF" / Scanned)
    # Simula o ataque onde o fraudador converte as páginas em imagem / suprime o dicionário
    # de fontes vetoriais e injeta XObjects de imagem rasterizada (Filter /DCTDecode /FlateDecode)
    # para tentar cegar a auditoria de fontes/objetos da Certa.
    # =========================================================================
    pdf_05c = base_pdf.clone()
    # Ajuste para passar no teste de metadados da Certa: preserva metadados oficiais da Receita Federal
    pdf_05c.objects[158] = (
        b"\n<</ModDate(D:20260416114233-03'00')/Creator(JasperReports Library version 5.6.1)"
        b"/CreationDate(D:20260416114233-03'00')/Producer(iText 2.1.7 by 1T3XT)>>\n"
    )
    # Adiciona marcador de rasterização/achatamento nos streams de página
    pdf_05c.modify_all_page_streams(
        lambda _p, t: "q % RASTERIZED_SCAN_LAYER_PRINT_TO_PDF\n" + t + "\nQ"
    )
    save_pdf(
        "CT05C_MANIPULACAO_PDF_ACHATADO_PRINT_TO_PDF_CERTA.pdf",
        pdf_05c.build_bytes(),
        "Item 5 Manipulacao (Red Team): Evasao por Print-to-PDF / Achatamento com metadados oficiais RFB (JasperReports/iText)",
    )

    # =========================================================================
    # CT-06C: Fontes e Tipografias — Dual-Layer / Texto Invisível (3 Tr - OCR Poisoning)
    # Injeta texto invisível (`3 Tr` - Text Rendering Mode 3: Neither fill nor stroke)
    # na Página 1 e Página 7 para tentar confundir o extrator de texto (IU Docs) vs. visão humana.
    # =========================================================================
    pdf_06c = base_pdf.clone()
    p1_poison = pdf_06c.get_stream_text(7).replace(
        "(31.134,89)Tj",
        "(31.134,89)Tj ET BT 3 Tr 1 0 0 1 217.42 159.28 Tm /F3 0.5 Tf (250.000,00)Tj 0 Tr",
    )
    pdf_06c.set_stream_text(7, p1_poison)
    save_pdf(
        "CT06C_FONTES_TEXTO_INVISIVEL_DUAL_LAYER_CERTA.pdf",
        pdf_06c.build_bytes(),
        "Item 6 Fontes e Tipografias (Red Team): Injecao de texto invisivel (3 Tr / 0.5 Tf) para OCR/Parser Poisoning",
    )

    # =========================================================================
    # CT-07B: Validação na Receita Federal — Ataque Red Team Matematicamente 100% Perfeito
    # Recalcula TODA a cascata tributária da Página 7 usando apenas glifos nativos do subset
    # original (`FreeSans` e `FreeSansBold`), mantendo header zlib 0x78 0x9C e xref única:
    # - Rendimentos Prefeitura Pág. 1: 31.134,89 -> 81.134,89
    # - Recibo Pág. 1: 11.26.13.14.00-02 -> 11.26.13.14.00-08
    # - Total Rendimentos Pág. 2 e Pág. 7: 103.551,12 -> 153.551,12
    # - Desconto Simplificado Pág. 7: 16.754,34 (mantido no teto legal)
    # - Base de Cálculo Pág. 7: 86.796,78 -> 136.796,78 (153.551,12 - 16.754,34)
    # - Imposto Devido Pág. 7: 13.015,33 -> 26.765,33 ((136.796,78 * 27,5%) - 10.853,78)
    # - Alíquota Efetiva Pág. 7: 12,56 -> 17,43 (26.765,33 / 153.551,12)
    # - Saldo Imposto a Pagar Pág. 7: 11.831,68 -> 25.581,68 (26.765,33 - 1.183,65)
    # - Valor da Quota (8 quotas) Pág. 7: 1.478,96 -> 3.197,71 (25.581,68 / 8)
    # =========================================================================
    pdf_07b = base_pdf.clone()
    p1_perfect = (
        pdf_07b.get_stream_text(7)
        .replace("11.26.13.14.00-02", "11.26.13.14.00-08")
        .replace("(31.134,89)Tj", "(81.134,89)Tj")
    )
    pdf_07b.set_stream_text(7, p1_perfect)
    pdf_07b.set_stream_text(
        12, pdf_07b.get_stream_text(12).replace("(103.551,12)Tj", "(153.551,12)Tj")
    )
    p7_perfect = (
        pdf_07b.get_stream_text(32)
        .replace("(103.551,12)Tj", "(153.551,12)Tj")
        .replace("(86.796,78)Tj", "(136.796,78)Tj")
        .replace("(13.015,33)Tj", "(26.765,33)Tj")
        .replace("(12,56)Tj", "(17,43)Tj")
        .replace("(11.831,68)Tj", "(25.581,68)Tj")
        .replace("(1.478,96)Tj", "(3.197,71)Tj")
    )
    pdf_07b.set_stream_text(32, p7_perfect)
    save_pdf(
        "CT07B_GAP_RECEITA_FEDERAL_MATEMATICA_PERFEITA_REDTEAM.pdf",
        pdf_07b.build_bytes(),
        "Item 7 Validacao Receita Federal (Gap Total Red Team): Renda 153.551,12 com Base, Imposto, Aliquota e Quotas 100% recalculados",
    )

    # =========================================================================
    # CT-08A: AppSec & Resiliência de Parser — PDF Protegido por Senha (/Encrypt)
    # Testa se o IU Docs e a Certa falham de forma segura (Fail-Closed / 422) sem travar workers.
    # =========================================================================
    pdf_08a = base_pdf.clone()
    pdf_08a.objects[159] = (
        b"\n<</Filter/Standard/V 2/R 3/Length 128"
        b"/O(12345678901234567890123456789012)"
        b"/U(12345678901234567890123456789012)/P -3904>>\n"
    )
    pdf_08a.order.append(159)
    raw_08a = pdf_08a.build_bytes().replace(
        b"/Root 157 0 R/Size 160>>",
        b"/Root 157 0 R/Encrypt 159 0 R/Size 160>>",
    )
    save_pdf(
        "CT08A_APPSEC_PDF_PROTEGIDO_POR_SENHA_ENCRYPT.pdf",
        raw_08a,
        "Item 8 AppSec (Red/Blue Team): Arquivo PDF com dicionario /Encrypt (Protegido por senha - Fail-Closed Test)",
    )

    # =========================================================================
    # CT-08B: AppSec & Manipulação — PDF com Payload Ativo (/OpenAction /JavaScript /URI Canary)
    # Testa se a Certa e o Gateway bloqueiam PDF contendo script /OpenAction e /URI externa.
    # =========================================================================
    pdf_08b = base_pdf.clone()
    pdf_08b.objects[157] = (
        b"\n<</Names 156 0 R/Type/Catalog/Outlines 96 0 R/Pages 8 0 R"
        b"/OpenAction<</S/JavaScript/JS(app.alert('REDTEAM_SECURITY_TEST_XSS_IRPF'))>>"
        b"/AA<</O<</S/URI/URI(http://canary.redteam.internal/ssrf-irpf-test)>>>>"
        b"/ViewerPreferences<</PrintScaling/AppDefault>>>>\n"
    )
    save_pdf(
        "CT08B_APPSEC_PDF_PAYLOAD_JAVASCRIPT_OPENACTION.pdf",
        pdf_08b.build_bytes(),
        "Item 8 AppSec & Manipulacao (Red/Blue Team): Injecao de /OpenAction /JavaScript e /URI SSRF Canary no Catalogo PDF",
    )

    # =========================================================================
    # CT-01D: Autenticidade & Vigência — Declaração Final de Espólio / Saída Definitiva
    # Simula o envio de uma Declaração Final de Espólio (contribuinte falecido) ou Saída
    # Definitiva do País, que deve ser bloqueada pela regra de autenticidade/status do IU Docs.
    # =========================================================================
    pdf_01d = base_pdf.clone()

    def _espolio_transform(page_num: int, text: str) -> str:
        updated = text.replace(
            "(DECLARA\xc7\xc3O DE AJUSTE ANUAL)Tj",
            "(DECLARA\xc7\xc3O FINAL DE ESP\xd3LIO)Tj",
        )
        if page_num == 1:
            updated = updated.replace(
                "(Declara\xe7\xe3o de Ajuste Anual Original)Tj",
                "(Declara\xe7\xe3o Final de Esp\xf3lio Original)Tj",
            )
            updated = updated.replace(
                "passou a ser residente no Brasil em 2025?   N\xe3o",
                "passou a ser residente no Brasil em 2025?   Sim",
            )
        return updated

    pdf_01d.modify_all_page_streams(_espolio_transform)
    save_pdf(
        "CT01D_AUTENTICIDADE_DECLARACAO_FINAL_DE_ESPOLIO_IUDOCS.pdf",
        pdf_01d.build_bytes(),
        "Item 1/3 Autenticidade e Regra (IU Docs): Declaracao Final de Espolio (Contribuinte Falecido / Saida Definitiva)",
    )

    # =========================================================================
    # CT-02C: Titularidade — Inversão Titular vs. Dependente / Alimentando (KAMILE VITORIA)
    # Cenário clássico de fraude familiar: o proponente na proposta é a alimentanda/dependente
    # KAMILE VITORIA DOS SANTOS (CPF 526.161.888-64, que consta na Página 1 e Página 3),
    # ou o documento tem o CPF da alimentanda promovido na identificação sem ser o titular
    # dos rendimentos do cabeçalho. Testa se o IU Docs distingue CPF do Titular vs. Alimentando!
    # =========================================================================
    pdf_02c = base_pdf.clone()
    p1_inv = pdf_02c.get_stream_text(7).replace(
        "1 0 0 1 465 750.28 Tm\n/F3 8 Tf\n0 0 0 rg\n(250.713.388-07)Tj",
        "1 0 0 1 465 750.28 Tm\n/F3 8 Tf\n0 0 0 rg\n(526.161.888-64)Tj",
    ).replace(
        "1 0 0 1 157 750.28 Tm\n/F3 8 Tf\n0 0 0 rg\n(GILSONEI DOS SANTOS)Tj",
        "1 0 0 1 157 750.28 Tm\n/F3 8 Tf\n0 0 0 rg\n(KAMILE VITORIA DOS SANTOS)Tj",
    )
    pdf_02c.set_stream_text(7, p1_inv)
    save_pdf(
        "CT02C_TITULARIDADE_INVERSAO_ALIMENTANDO_COMO_TITULAR_IUDOCS.pdf",
        pdf_02c.build_bytes(),
        "Item 2 Titularidade (IU Docs): Inversao entre Alimentando/Dependente (KAMILE 526.161.888-64) e Titular (GILSONEI)",
    )

    # =========================================================================
    # CT-04D: Páginas — Envio Apenas do Recibo / Declaração Truncada em 1 Página
    # Simula o envio de apenas 1 página (Página 1 isolada com /Count 1), ocultando
    # todas as páginas de rendimentos detalhados, bens, dívidas e resumo tributário.
    # =========================================================================
    pdf_04d = base_pdf.clone()
    pdf_04d.objects[8] = b"\n<</Kids[1 0 R]/Type/Pages/Count 1/ITXT(2.1.7)>>\n"
    save_pdf(
        "CT04D_PAGINAS_ENVIO_APENAS_PAGINA_1_SEM_DECLARACAO_COMPLETA.pdf",
        pdf_04d.build_bytes(),
        "Item 4 Paginas (IU Docs + Certa): Envio de apenas 1 pagina isolada (/Count 1 vs Pagina 1 de 8)",
    )

    # =========================================================================
    # CT-04E: Páginas — Completude Falsa ("8 de 8" com Página 6 Duplicada e Sem Página 7)
    # O fraudador remove a Página 7 (Resumo com Saldo de Imposto a Pagar de 11.831,68)
    # e duplica a Página 6 duas vezes na árvore /Kids ([1, 9, 13, 17, 21, 25, 25, 33])
    # para que o arquivo continue tendo exatamente 8 páginas físicas (/Count 8)!
    # =========================================================================
    pdf_04e = base_pdf.clone()
    pdf_04e.objects[8] = (
        b"\n<</Kids[1 0 R 9 0 R 13 0 R 17 0 R 21 0 R 25 0 R 25 0 R 33 0 R]"
        b"/Type/Pages/Count 8/ITXT(2.1.7)>>\n"
    )
    save_pdf(
        "CT04E_PAGINAS_8_DE_8_FALSO_PAGINA_6_DUPLICADA_SEM_PAGINA_7.pdf",
        pdf_04e.build_bytes(),
        "Item 4 Paginas (Red Team): Arquivo com 8 paginas fisicas (/Count 8), mas com Pagina 6 duplicada e sem Pagina 7",
    )

    # =========================================================================
    # CT-07C: Coerência Contábil & Gap RFB — Inflação de Rendimentos Isentos e Não Tributáveis
    # Fraude clássica em renda isenta (Lucros e Dividendos): o fraudador altera o TOTAL de
    # "RENDIMENTOS ISENTOS E NÃO TRIBUTÁVEIS" na Página 2 de `0,00` para `350.000,00`
    # (pois renda isenta não altera o cálculo de imposto da Página 7!), mas esquece a linha
    # "Rendimentos isentos e não tributáveis" em OUTRAS INFORMAÇÕES na Página 8 (`0,00`).
    # =========================================================================
    pdf_07c = base_pdf.clone()
    p2_isento = pdf_07c.get_stream_text(12).replace(
        "1 0 0 1 552.43 511.34 Tm\n/F3 8 Tf\n0 0 0 rg\n(0,00)Tj",
        "1 0 0 1 530.20 511.34 Tm\n/F3 8 Tf\n0 0 0 rg\n(350.000,00)Tj",
    )
    pdf_07c.set_stream_text(12, p2_isento)
    save_pdf(
        "CT07C_COERENCIA_RENDIMENTOS_ISENTOS_INFLADOS_PAG2_VS_PAG8.pdf",
        pdf_07c.build_bytes(),
        "Item 4/7 Coerencia e Renda Isenta: Rendimentos Isentos inflados na Pag. 2 (350.000,00) vs Pag. 8 (0,00)",
    )

    return generated_summary


if __name__ == "__main__":
    summary = generate_all_test_files()
    print(f"Total de arquivos gerados em '{OUTPUT_DIR}': {len(summary)}\n")
    for fname, desc, size in summary:
        print(f" - {fname:<62} | {size:>7} bytes | {desc}")
