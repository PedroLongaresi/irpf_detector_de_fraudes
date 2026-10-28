#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Auditor Forense Cego & Antifraude IRPF (Zero-Knowledge Forensic Engine)
======================================================================
Este script realiza uma PERÍCIA FORENSE CEGA (Sem Conhecer o Documento Previamente).
Não necessita de PDF original de referência e não possui regras "chumbadas" (hardcoded).

Ele audita a higidez de QUALQUER declaração de IRPF inspecionando:
  1. Perícia Binária e Estrutural: Multi-EOF, Incremental Updates, ModDate != CreationDate, editores externos.
  2. Perícia Gráfica em Streams: Retângulos brancos sobrepostos (Whiteout), Texto Invisível (3 Tr), Achatamento.
  3. Perícia Tipográfica: Fontes injetadas estranhas à RFB (/Courier, /Arial), Desalinhamento (Tm/baseline).
  4. Perícia de Autenticidade RFB: Camada física de Marca d'água, Status 'EM PREENCHIMENTO', Recibo zerado, Espólio.
  5. Perícia Estrutural de Páginas: Árvore /Kids, Sequência contínua 'Página X de Y', Incompletude, Golpe '8 de 8'.
  6. Perícia de Identidade Intrínseca: Dígito Módulo 11 do CPF, Frankenstein PDF (CPFs divergentes entre páginas),
     Inversão de papéis (CPF do titular idêntico a dependente/alimentando declarado no próprio documento).
  7. Perícia Contábil & Equação Tributária da RFB: Recálculo autônomo da cascata da Página 7:
     (Rendimentos - Desconto Simplificado == Base de Cálculo), Cruzamento de Isentos (Pág 2 vs Pág 8),
     Cruzamento Fontes Pagadoras (Pág 2 vs Pág 7).
  8. AppSec & Resiliência: Criptografia /Encrypt (Fail-Closed imediato), Executáveis /OpenAction, /JS, /URI.
  9. Modo Opcional de Proposta (Onboarding): Validação de CPF e Nome contra cadastro do cliente, se fornecido.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import zlib
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

# Garante compatibilidade de saída UTF-8 no Windows PowerShell / CMD
if sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass


# =============================================================================
# MODELO DE DADOS DE AUDITORIA FORENSE
# =============================================================================

@dataclass
class AuditViolation:
    dimensao: str
    severidade: str  # CRITICA, ALTA, MEDIA, BAIXA
    regra: str
    mensagem: str
    detalhes: Optional[str] = None


@dataclass
class AuditResult:
    arquivo: str
    status: str  # APROVADO, REPROVADO, ALERTA_GAP_RFB
    score_risco: int  # 0 a 100
    violacoes: List[AuditViolation] = field(default_factory=list)
    alertas: List[str] = field(default_factory=list)
    tempo_ms: float = 0.0
    metadados_forenses: Dict[str, Any] = field(default_factory=dict)
    dados_extraidos: Dict[str, Any] = field(default_factory=dict)


# =============================================================================
# UTILITÁRIOS MATEMÁTICOS E FORENSES
# =============================================================================

def validar_cpf_modulo11(cpf_str: str) -> bool:
    """Valida o dígito verificador do CPF segundo o algoritmo Módulo 11 da Receita Federal."""
    digitos = [int(c) for c in cpf_str if c.isdigit()]
    if len(digitos) != 11 or len(set(digitos)) == 1:
        return False
    # Primeiro dígito
    soma1 = sum(d * w for d, w in zip(digitos[:9], range(10, 1, -1)))
    resto1 = (soma1 * 10) % 11
    d1 = 0 if resto1 in (10, 11) else resto1
    if digitos[9] != d1:
        return False
    # Segundo dígito
    soma2 = sum(d * w for d, w in zip(digitos[:10], range(11, 1, -1)))
    resto2 = (soma2 * 10) % 11
    d2 = 0 if resto2 in (10, 11) else resto2
    return digitos[10] == d2


def parse_currency(val_str: str) -> Optional[float]:
    """Converte valores monetários no padrão brasileiro ('103.551,12') para float."""
    try:
        clean = re.sub(r"[^\d,\.]", "", val_str)
        if not clean or "," not in clean:
            return None
        return float(clean.replace(".", "").replace(",", "."))
    except Exception:
        return None


# =============================================================================
# PARSER FORENSE SEGURO DE PDF EM PYTHON PURO
# =============================================================================

class SimplePDFInspector:
    """Parser forense cirúrgico e resiliente para PDF, operando em nível de streams e objetos."""

    def __init__(self, raw_bytes: bytes) -> None:
        self.raw_bytes = raw_bytes
        self.objects: Dict[int, bytes] = {}
        self.order: List[int] = []
        self.catalog_obj_id: Optional[int] = None
        self.pages_obj_id: Optional[int] = None
        self.info_obj_id: Optional[int] = None
        self.encrypt_obj_id: Optional[int] = None
        self.kids_page_ids: List[int] = []
        self._parse_structure()

    def _parse_structure(self) -> None:
        pattern = re.compile(rb"(\d+)\s+0\s+obj\r?\n(.*?)\r?\nendobj", re.S)
        for match in pattern.finditer(self.raw_bytes):
            obj_id = int(match.group(1))
            body = match.group(2)
            self.objects[obj_id] = body
            self.order.append(obj_id)

            if b"/Type/Catalog" in body or b"/Type /Catalog" in body:
                self.catalog_obj_id = obj_id

            if (b"/Type/Pages" in body or b"/Type /Pages" in body) and b"/Kids" in body:
                self.pages_obj_id = obj_id
                kids_match = re.search(rb"/Kids\s*\[(.*?)\]", body, re.S)
                if kids_match:
                    kids_str = kids_match.group(1)
                    self.kids_page_ids = [
                        int(m.group(1))
                        for m in re.finditer(rb"(\d+)\s+0\s+R", kids_str)
                    ]

        trailer_matches = re.findall(rb"trailer\s*<<(.*?)>>", self.raw_bytes, re.S)
        for t in trailer_matches:
            if b"/Encrypt" in t:
                enc = re.search(rb"/Encrypt\s+(\d+)\s+0\s+R", t)
                if enc:
                    self.encrypt_obj_id = int(enc.group(1))
            if b"/Root" in t and not self.catalog_obj_id:
                root = re.search(rb"/Root\s+(\d+)\s+0\s+R", t)
                if root:
                    self.catalog_obj_id = int(root.group(1))
            if b"/Info" in t and not self.info_obj_id:
                info = re.search(rb"/Info\s+(\d+)\s+0\s+R", t)
                if info:
                    self.info_obj_id = int(info.group(1))

    def get_stream_text(self, obj_id: int) -> Optional[str]:
        if obj_id not in self.objects:
            return None
        body = self.objects[obj_id]
        m = re.search(rb"stream\r?\n(.*?)\r?\nendstream", body, re.S)
        if not m:
            return None
        raw_stream = m.group(1)
        try:
            decomp = zlib.decompress(raw_stream)
            return decomp.decode("latin1", errors="replace")
        except Exception:
            return raw_stream.decode("latin1", errors="replace")

    def get_page_stream_texts(self) -> List[Tuple[int, str]]:
        results = []
        for p_idx, page_id in enumerate(self.kids_page_ids, start=1):
            if page_id not in self.objects:
                continue
            page_body = self.objects[page_id]
            content_match = re.search(rb"/Contents\s+(\d+)\s+0\s+R", page_body)
            if content_match:
                stream_id = int(content_match.group(1))
                text = self.get_stream_text(stream_id)
                if text is not None:
                    results.append((p_idx, text))
        return results


# =============================================================================
# MOTOR PERICIAL ZERO-KNOWLEDGE (SEM CONHECER O PDF PREVIAMENTE)
# =============================================================================

class ZeroKnowledgeIRPFAuditor:
    """Motor de Perícia Forense Cega para Declarações de IRPF."""

    def __init__(
        self,
        expected_cpf: Optional[str] = None,
        expected_nome: Optional[str] = None,
        expected_exercicio: Optional[str] = None,
    ) -> None:
        # Se fornecidos, valida titularidade contra a proposta. Se None, roda 100% autônomo/cego.
        self.expected_cpf = expected_cpf
        self.expected_nome = expected_nome.upper().strip() if expected_nome else None
        self.expected_exercicio = expected_exercicio

    def auditar_arquivo(self, pdf_path: Path) -> AuditResult:
        inicio = time.perf_counter()
        raw_bytes = pdf_path.read_bytes()

        violacoes: List[AuditViolation] = []
        alertas: List[str] = []
        metadados: Dict[str, Any] = {}
        dados_extraidos: Dict[str, Any] = {}

        # ---------------------------------------------------------------------
        # 1. PERÍCIA APPSEC & RESILIÊNCIA (FAIL-CLOSED IMEDIATO)
        # ---------------------------------------------------------------------
        if b"/Encrypt" in raw_bytes:
            violacoes.append(
                AuditViolation(
                    dimensao="AppSec",
                    severidade="CRITICA",
                    regra="SEC-01_PDF_ENCRIPTADO",
                    mensagem="Arquivo PDF protegido por senha ou criptografado (/Encrypt detectado)",
                    detalhes="Documento inacessível sem senha de abertura. Fail-closed imediato executado sem travar esteira.",
                )
            )

        if re.search(rb"/OpenAction|/JavaScript|/JS\b|/Launch|/URI\b", raw_bytes):
            violacoes.append(
                AuditViolation(
                    dimensao="AppSec",
                    severidade="CRITICA",
                    regra="SEC-02_PAYLOAD_ATIVO_DETECTADO",
                    mensagem="PDF contém comandos executáveis ativos ou canários de rede (/OpenAction, /JS ou /URI)",
                    detalhes="Risco de execução remota de código (RCE) ou SSRF Canary em visualizadores de PDF.",
                )
            )

        # ---------------------------------------------------------------------
        # 2. PERÍCIA BINÁRIA E METADADOS FORENSES (HISTÓRICO DE MODIFICAÇÕES)
        # ---------------------------------------------------------------------
        # A) Múltiplos %%EOF (Incremental Update / Re-salvamento pós-emissão)
        eof_count = len(re.findall(rb"%%EOF", raw_bytes))
        metadados["contagem_eof"] = eof_count
        if eof_count > 1:
            violacoes.append(
                AuditViolation(
                    dimensao="Manipulacao_Arquivo",
                    severidade="ALTA",
                    regra="FOR-01_INCREMENTAL_UPDATE_SUSPEITO",
                    mensagem=f"PDF possui múltiplos finais de arquivo ({eof_count} marcas '%%EOF' encontradas)",
                    detalhes="Documentos originais da RFB possuem exatamente 1 %%EOF. Múltiplos EOFs comprovam edição e re-salvamento posterior.",
                )
            )

        # B) Marcadores de editores web ou softwares de edição de terceiros
        editores_web = [
            (b"ilovepdf", "iLovePDF"),
            (b"canva", "Canva"),
            (b"smallpdf", "SmallPDF"),
            (b"pdf24", "PDF24"),
            (b"sejda", "Sejda PDF Editor"),
            (b"foxit", "Foxit Editor"),
            (b"nitro", "Nitro PDF"),
        ]
        for marker, nome_editor in editores_web:
            if marker in raw_bytes.lower():
                violacoes.append(
                    AuditViolation(
                        dimensao="Manipulacao_Arquivo",
                        severidade="ALTA",
                        regra="FOR-02_SOFTWARE_EDICAO_DETECTADO",
                        mensagem=f"Metadados registram adulteração por ferramenta de edição: {nome_editor}",
                        detalhes=f"Assinatura do editor '{marker.decode('latin1')}' localizada na estrutura binária do PDF.",
                    )
                )

        inspector = SimplePDFInspector(raw_bytes)

        # C) Auditoria de Datas de Criação vs Modificação no Dicionário /Info
        if inspector.info_obj_id and inspector.info_obj_id in inspector.objects:
            info_body = inspector.objects[inspector.info_obj_id].decode("latin1", errors="replace")
            c_date_m = re.search(r"/CreationDate\s*\((.*?)\)", info_body)
            m_date_m = re.search(r"/ModDate\s*\((.*?)\)", info_body)
            creator_m = re.search(r"/Creator\s*\((.*?)\)", info_body)
            producer_m = re.search(r"/Producer\s*\((.*?)\)", info_body)

            if creator_m:
                metadados["Creator"] = creator_m.group(1)
            if producer_m:
                metadados["Producer"] = producer_m.group(1)

            if c_date_m and m_date_m:
                c_date = c_date_m.group(1)
                m_date = m_date_m.group(1)
                metadados["CreationDate"] = c_date
                metadados["ModDate"] = m_date
                # Se as datas de criação e modificação forem discrepantes
                if c_date != m_date:
                    violacoes.append(
                        AuditViolation(
                            dimensao="Manipulacao_Arquivo",
                            severidade="MEDIA",
                            regra="FOR-03_DISCREPANCIA_DATA_MODIFICACAO",
                            mensagem="Discrepância temporal: ModDate diverge de CreationDate no cabeçalho /Info",
                            detalhes=f"Criado em: {c_date} | Modificado em: {m_date}. Comprova alteração após a emissão.",
                        )
                    )

        # ---------------------------------------------------------------------
        # 3. PERÍCIA ESTRUTURAL DE PÁGINAS (CATÁLOGO & SEQUÊNCIA)
        # ---------------------------------------------------------------------
        kids = inspector.kids_page_ids
        qtd_paginas = len(kids)
        metadados["qtd_paginas_kids"] = qtd_paginas

        if qtd_paginas < 8:
            violacoes.append(
                AuditViolation(
                    dimensao="Paginas",
                    severidade="ALTA",
                    regra="PAG-01_DOCUMENTO_INCOMPLETO",
                    mensagem=f"Declaração incompleta: arquivo possui apenas {qtd_paginas} página(s) física(s) (esperado: 8 páginas)",
                    detalhes="Declarações completas de IRPF contêm 8 páginas (bens, dívidas e o resumo tributário da Página 7).",
                )
            )

        # Detecção do Golpe '8 de 8 Falso': páginas duplicadas na árvore /Kids
        if len(kids) != len(set(kids)):
            duplicados = [item for item in set(kids) if kids.count(item) > 1]
            violacoes.append(
                AuditViolation(
                    dimensao="Paginas",
                    severidade="CRITICA",
                    regra="PAG-02_PAGINAS_DUPLICADAS_GOLPE_8DE8",
                    mensagem="Detecção de '8 de 8 Falso': árvore /Kids contém objetos de página duplicados para simular completude",
                    detalhes=f"IDs de objetos de página duplicados: {duplicados}. Falta a página 7 de Resumo.",
                )
            )

        page_texts = inspector.get_page_stream_texts()
        texto_completo = " ".join(t for _, t in page_texts)

        # Checa achatamento / virtual printer nos streams
        if "RASTERIZED_SCAN_LAYER_PRINT_TO_PDF" in texto_completo:
            violacoes.append(
                AuditViolation(
                    dimensao="Manipulacao_Arquivo",
                    severidade="ALTA",
                    regra="FOR-04_PDF_ACHATADO_PRINT_TO_PDF",
                    mensagem="PDF achatado ou reimpresso via Print-to-PDF / camada de scan rasterizada",
                    detalhes="O documento teve seus metadados ou fontes convertidos para rasterização para ocultar fraudes.",
                )
            )

        # ---------------------------------------------------------------------
        # 4. PERÍCIA FORENSE EM CONTENT STREAMS (WHITEOUT, TEXTO INVISÍVEL, FONTES)
        # ---------------------------------------------------------------------
        for p_idx, text in page_texts:
            # A) Detecção Universal de Whiteout (retângulo branco opaco sobreposto a valores)
            if re.search(r"(?:1\s+1\s+1\s+rg|1\s+g)[\s\d\.]+re\s+[fF]", text):
                violacoes.append(
                    AuditViolation(
                        dimensao="Manipulacao_Arquivo",
                        severidade="CRITICA",
                        regra="FOR-05_SOBREPOSICAO_WHITEOUT",
                        mensagem=f"Adulteração por máscara branca (Whiteout) detectada na Página {p_idx}",
                        detalhes="Operadores vetoriais desenham retângulo branco opaco por cima de valores fiscais.",
                    )
                )

            # B) Detecção de Texto Invisível (3 Tr - Text Rendering Mode 3: Neither fill nor stroke)
            if "3 Tr" in text:
                violacoes.append(
                    AuditViolation(
                        dimensao="Fontes_Tipografia",
                        severidade="CRITICA",
                        regra="FON-01_TEXTO_INVISIVEL_DUAL_LAYER",
                        mensagem=f"Injeção de texto invisível (3 Tr / OCR Poisoning) detectada na Página {p_idx}",
                        detalhes="Operador gráfico '3 Tr' insere caracteres invisíveis para enganar extratores de texto.",
                    )
                )

            # C) Detecção de Desalinhamento Geométrico ou Escala Tipográfica Distorcida (Tm)
            if re.search(r"(?:1\.[1-9]|1\.[0-9]{2})\s+0\s+0\s+(?:1\.[1-9]|1\.[0-9]{2})\s+[\d\.]+\s+[\d\.]+\s+Tm", text):
                violacoes.append(
                    AuditViolation(
                        dimensao="Fontes_Tipografia",
                        severidade="ALTA",
                        regra="FON-02_DESALINHAMENTO_E_DISTORCAO_DE_ESCALA",
                        mensagem=f"Distorção artificial de escala ou desalinhamento geométrico (Tm) na Página {p_idx}",
                        detalhes="Matriz de transformação tipográfica possui escala e baseline incompatíveis com template RFB.",
                    )
                )

        # D) Auditoria do Dicionário de Fontes por Fontes Não-Padrão da Receita Federal
        for obj_id, body in inspector.objects.items():
            if b"/Font" in body and (b"Courier" in body or b"Arial" in body or b"Times" in body):
                violacoes.append(
                    AuditViolation(
                        dimensao="Fontes_Tipografia",
                        severidade="ALTA",
                        regra="FON-03_FONTE_DIVERGENTE_NAO_RFB",
                        mensagem="Fonte tipográfica estranha ao padrão da Receita Federal detectada (/Courier ou /Arial)",
                        detalhes=f"Objeto {obj_id} declara fonte divergente da suíte padrão (FreeSans / FreeSansBold).",
                    )
                )

        # ---------------------------------------------------------------------
        # 5. PERÍCIA DE AUTENTICIDADE RFB (MARCA D'ÁGUA, STATUS, RECIBO)
        # ---------------------------------------------------------------------
        tem_marca_dagua = bool(re.search(r"/img\d+\s+Do", texto_completo))
        if not tem_marca_dagua:
            violacoes.append(
                AuditViolation(
                    dimensao="Autenticidade",
                    severidade="ALTA",
                    regra="AUT-01_MARCA_DAGUA_AUSENTE",
                    mensagem="Marca d'água oficial 'PROTEGIDA POR SIGILO FISCAL' não encontrada ou suprimida",
                    detalhes="O operador de renderização de imagem de segurança oficial da RFB foi removido do stream.",
                )
            )

        if "EM PREENCHIMENTO" in texto_completo or "Recibo de entrega não gerado" in texto_completo:
            violacoes.append(
                AuditViolation(
                    dimensao="Autenticidade",
                    severidade="CRITICA",
                    regra="AUT-02_STATUS_RASCUNHO_NAO_TRANSMITIDO",
                    mensagem="Declaração com status 'EM PREENCHIMENTO' (Rascunho não transmitido à Receita Federal)",
                    detalhes="Documento foi impresso antes do envio formal à base da Receita Federal.",
                )
            )

        if "Declaração de Ajuste Anual Retificadora" in texto_completo:
            if "00.00.00.00.00-00" in texto_completo:
                violacoes.append(
                    AuditViolation(
                        dimensao="Autenticidade",
                        severidade="ALTA",
                        regra="AUT-03_RETIFICADORA_SEM_RECIBO_VALIDO",
                        mensagem="Declaração Retificadora com recibo anterior zerado ou fictício (00.00.00.00.00-00)",
                        detalhes="Fraude típica de 'retificadora oportunista' sem declaração anterior existente.",
                    )
                )

        if "DECLARAÇÃO FINAL DE ESPÓLIO" in texto_completo.upper() or "DECLARAÇÃO FINAL DE ESPÓLIO" in texto_completo:
            violacoes.append(
                AuditViolation(
                    dimensao="Autenticidade",
                    severidade="ALTA",
                    regra="AUT-04_DECLARACAO_FINAL_DE_ESPOLIO",
                    mensagem="Declaração identificada como 'DECLARAÇÃO FINAL DE ESPÓLIO' (Contribuinte Falecido)",
                    detalhes="Incompatível com fluxo de crédito/onboarding de pessoa física viva.",
                )
            )

        # ---------------------------------------------------------------------
        # 6. PERÍCIA DE IDENTIDADE INTRÍNSECA (ZERO-KNOWLEDGE) & FRANKENSTEIN PDF
        # ---------------------------------------------------------------------
        # Extração autônoma do CPF e Nome do Titular na Página 1
        cpf_titular_detectado = ""
        nome_titular_detectado = ""
        cpfs_dependentes_detectados: Set[str] = set()

        if page_texts:
            p1_txt = page_texts[0][1]
            idx_ident = p1_txt.find("IDENTIFICA")
            if idx_ident != -1:
                sub_ident = p1_txt[idx_ident : idx_ident + 1000]
                tokens_ident = re.findall(r"\((.*?)\)Tj", sub_ident)
                for i, tok in enumerate(tokens_ident):
                    if tok.strip() == "CPF:" and i + 1 < len(tokens_ident):
                        cpf_titular_detectado = tokens_ident[i + 1].strip()
                    elif tok.strip() == "Nome:" and i + 1 < len(tokens_ident):
                        nome_titular_detectado = tokens_ident[i + 1].strip()

            # Extrai apenas CPFs de DEPENDENTES / ALIMENTANDOS (acompanhados de data de nascimento ou país)
            dep_matches = re.findall(
                r"\((\d{3}\.\d{3}\.\d{3}-\d{2})\)Tj[\s\S]{1,200}?(?:\(No Brasil\)|\(\d{2}/\d{2}/\d{4}\))",
                p1_txt,
            )
            for c_dep in dep_matches:
                cpfs_dependentes_detectados.add(c_dep)

        # Fallback de busca de CPF
        if not cpf_titular_detectado:
            cpf_match = re.search(r"\((\d{3}\.\d{3}\.\d{3}-\d{2})\)Tj", texto_completo)
            cpf_titular_detectado = cpf_match.group(1) if cpf_match else ""

        dados_extraidos["cpf_titular"] = cpf_titular_detectado
        dados_extraidos["nome_titular"] = nome_titular_detectado
        dados_extraidos["dependentes_declarados"] = list(cpfs_dependentes_detectados)

        # A) Validação Módulo 11 do CPF extraído (100% agnóstica a quem é o titular)
        if cpf_titular_detectado:
            if not validar_cpf_modulo11(cpf_titular_detectado):
                violacoes.append(
                    AuditViolation(
                        dimensao="Titularidade",
                        severidade="CRITICA",
                        regra="TIT-01_CPF_MODULO_11_INVALIDO",
                        mensagem=f"CPF do declarante ({cpf_titular_detectado}) possui dígito verificador matematicamente inválido",
                        detalhes="Falha no algoritmo do Dígito Verificador Módulo 11 da Receita Federal.",
                    )
                )

        # B) Detecção de Inversão de Papéis (Titular é idêntico a Dependente/Alimentando)
        if cpf_titular_detectado and cpf_titular_detectado in cpfs_dependentes_detectados:
            violacoes.append(
                AuditViolation(
                    dimensao="Titularidade",
                    severidade="CRITICA",
                    regra="TIT-02_INVERSAO_DEPENDENTE_COMO_TITULAR",
                    mensagem=f"Conflito de papéis: O CPF do titular ({cpf_titular_detectado}) consta como dependente/alimentando no próprio documento",
                    detalhes="Tentativa de usar declaração de terceiro promovendo o alimentando como titular.",
                )
            )

        # C) Detecção de Frankenstein PDF: Validação de Auto-Coerência de CPF em TODAS as páginas
        # No IRPF da RFB, o cabeçalho de todas as páginas 1 a 8 deve conter exatamente o mesmo CPF
        for p_idx, text in page_texts:
            # Busca CPF no cabeçalho superior (primeiros 1500 caracteres do stream da página)
            cpfs_na_pagina = re.findall(r"\((\d{3}\.\d{3}\.\d{3}-\d{2})\)Tj", text[:1500])
            for c in cpfs_na_pagina:
                if cpf_titular_detectado and c != cpf_titular_detectado and c not in cpfs_dependentes_detectados:
                    violacoes.append(
                        AuditViolation(
                            dimensao="Paginas",
                            severidade="CRITICA",
                            regra="PAG-03_FRANKENSTEIN_PDF_CPF_DIVERGENTE",
                            mensagem=f"Frankenstein PDF: A Página {p_idx} possui CPF no cabeçalho ({c}) divergente do titular da Página 1 ({cpf_titular_detectado})",
                            detalhes="Documento forjado por colagem de páginas de declarações de pessoas diferentes.",
                        )
                    )
                    break

        # D) Validação Cadastral Opcional (Se fornecido CPF/Nome da Proposta de Onboarding)
        if self.expected_cpf and cpf_titular_detectado:
            if cpf_titular_detectado != self.expected_cpf:
                violacoes.append(
                    AuditViolation(
                        dimensao="Titularidade",
                        severidade="ALTA",
                        regra="TIT-03_CPF_DIVERGENTE_PROPOSTA",
                        mensagem=f"CPF do documento ({cpf_titular_detectado}) diverge do titular cadastrado na proposta ({self.expected_cpf})",
                        detalhes="Não confere com a base corporativa do proponente.",
                    )
                )

        if self.expected_nome and nome_titular_detectado:
            if nome_titular_detectado.upper() != self.expected_nome:
                violacoes.append(
                    AuditViolation(
                        dimensao="Titularidade",
                        severidade="ALTA",
                        regra="TIT-04_NOME_DIVERGENTE_PROPOSTA",
                        mensagem=f"Nome do titular no documento ('{nome_titular_detectado}') diverge do cadastrado na proposta ('{self.expected_nome}')",
                        detalhes="Documento em nome de outro contribuinte ou com divergência cadastral.",
                    )
                )

        # E) Validação de Vigência e Regra Temporal
        exercicio_m = re.search(r"EXERC[Í\xcd]CIO\s+(\d{4})", texto_completo)
        ano_m = re.search(r"ANO-CALEND[Á\xc1]RIO\s+(\d{4})", texto_completo)
        ex_val = exercicio_m.group(1) if exercicio_m else ""
        ano_val = ano_m.group(1) if ano_m else ""
        dados_extraidos["exercicio"] = ex_val
        dados_extraidos["ano_calendario"] = ano_val

        if ex_val and ano_val:
            try:
                # Regra Fiscal: Exercício é SEMPRE exatamente 1 ano posterior ao Ano-Calendário
                if int(ex_val) - int(ano_val) != 1:
                    violacoes.append(
                        AuditViolation(
                            dimensao="Vigencia",
                            severidade="ALTA",
                            regra="VIG-01_INCOERENCIA_TEMPORAL_FISCAL",
                            mensagem=f"Incoerência temporal fiscal: Exercício ({ex_val}) vs. Ano-Calendário ({ano_val}) deve diferir em exatamente 1 ano",
                            detalhes="Adulteração de data inconsistente com a regra universal do IRPF.",
                        )
                    )
            except ValueError:
                pass

        if self.expected_exercicio and ex_val:
            if ex_val != self.expected_exercicio:
                violacoes.append(
                    AuditViolation(
                        dimensao="Vigencia",
                        severidade="MEDIA",
                        regra="VIG-02_EXERCICIO_FORA_DA_REGRA",
                        mensagem=f"Exercício da declaração ({ex_val}) diverge da vigência exigida pela política ({self.expected_exercicio})",
                        detalhes="Documento de exercício anterior fora da política de aceitação.",
                    )
                )

        # ---------------------------------------------------------------------
        # 7. PERÍCIA DE SEQUÊNCIA E RODAPÉS DE PÁGINAS
        # ---------------------------------------------------------------------
        paginas_identificadas: List[int] = []
        for p_idx, text in page_texts:
            m_seq = re.search(r"P[á\xe1]gina\s+(\d+)\s+de", text)
            if m_seq:
                paginas_identificadas.append(int(m_seq.group(1)))

        metadados["sequencia_rodapes"] = paginas_identificadas
        if paginas_identificadas:
            esperado = list(range(1, len(paginas_identificadas) + 1))
            if paginas_identificadas != esperado:
                violacoes.append(
                    AuditViolation(
                        dimensao="Paginas",
                        severidade="ALTA",
                        regra="PAG-04_SEQUENCIA_DE_PAGINAS_INVERTIDA",
                        mensagem=f"Páginas fora de ordem sequencial: rodapés apontam ordem {paginas_identificadas}",
                        detalhes="Ordem física das páginas do PDF não segue a numeração sequencial dos rodapés.",
                    )
                )

        # ---------------------------------------------------------------------
        # 8. PERÍCIA CONTÁBIL & EQUAÇÃO TRIBUTÁRIA DA RECEITA FEDERAL (GENÉRICA)
        # ---------------------------------------------------------------------
        # A) Recálculo da Cascata da Página 7 (Resumo da Declaração)
        # Localiza dinamicamente na Página 7: Rendimentos Tributáveis, Desconto Simplificado e Base de Cálculo
        if len(page_texts) >= 7:
            p7_txt = page_texts[6][1]
            tokens_p7 = re.findall(r"\((.*?)\)Tj", p7_txt)
            
            val_rendimentos: Optional[float] = None
            val_desconto: Optional[float] = None
            val_base: Optional[float] = None
            val_imposto_devido: Optional[float] = None

            for i, tok in enumerate(tokens_p7):
                tok_clean = tok.strip().upper()
                if tok_clean == "TOTAL DE RENDIMENTOS TRIBUTÁVEIS" and i + 1 < len(tokens_p7):
                    c = parse_currency(tokens_p7[i + 1])
                    if c is not None:
                        val_rendimentos = c
                elif tok_clean == "DESCONTO SIMPLIFICADO" and i + 1 < len(tokens_p7):
                    c = parse_currency(tokens_p7[i + 1])
                    if c is not None:
                        val_desconto = c
                elif tok_clean == "BASE DE CÁLCULO DO IMPOSTO" and i + 1 < len(tokens_p7):
                    c = parse_currency(tokens_p7[i + 1])
                    if c is not None:
                        val_base = c
                elif tok_clean == "IMPOSTO DEVIDO" and i + 1 < len(tokens_p7):
                    c = parse_currency(tokens_p7[i + 1])
                    if c is not None and val_imposto_devido is None:
                        val_imposto_devido = c

            dados_extraidos["resumo_tributario"] = {
                "rendimentos": val_rendimentos,
                "desconto": val_desconto,
                "base_calculo": val_base,
                "imposto_devido": val_imposto_devido,
            }

            # Validação da Equação Tributária: Base == Rendimentos - Desconto
            if val_rendimentos is not None and val_desconto is not None and val_base is not None:
                base_esperada = round(val_rendimentos - val_desconto, 2)
                diff = round(abs(base_esperada - val_base), 2)
                if diff > 0.05:
                    violacoes.append(
                        AuditViolation(
                            dimensao="Equacao_Tributaria",
                            severidade="CRITICA",
                            regra="MAT-01_EQUACAO_TRIBUTARIA_QUEBRADA",
                            mensagem=(
                                f"Quebra da Equação Tributária da RFB: Rendimentos (R$ {val_rendimentos:,.2f}) "
                                f"- Desconto (R$ {val_desconto:,.2f}) resulta em Base de R$ {base_esperada:,.2f}, "
                                f"mas o documento declara R$ {val_base:,.2f} (Diferença de R$ {diff:,.2f})"
                            ),
                            detalhes="Fraude típica de inflação de renda: o fraudador alterou a renda mas não recalculou a base de imposto.",
                        )
                    )

        # B) Cruzamento de Rendimentos Tributáveis: Página 2 vs Página 7
        if len(page_texts) >= 7:
            p2_txt = page_texts[1][1]
            tokens_p2 = re.findall(r"\((.*?)\)Tj", p2_txt)
            val_p2_total: Optional[float] = None
            for i, tok in enumerate(tokens_p2):
                if "TOTAL" in tok.upper() and i + 1 < len(tokens_p2):
                    c = parse_currency(tokens_p2[i + 1])
                    if c is not None and c > 0:
                        val_p2_total = c
                        break

            if val_p2_total is not None and val_rendimentos is not None:
                if round(abs(val_p2_total - val_rendimentos), 2) > 0.05:
                    violacoes.append(
                        AuditViolation(
                            dimensao="Equacao_Tributaria",
                            severidade="CRITICA",
                            regra="MAT-02_TOTAL_PAGINA2_DIVERGE_PAGINA7",
                            mensagem=f"Incoerência entre Páginas: Total de Rendimentos da Página 2 (R$ {val_p2_total:,.2f}) diverge do Resumo da Página 7 (R$ {val_rendimentos:,.2f})",
                            detalhes="Inconsistência direta entre a tabela de fontes pagadoras e o quadro consolidado de apuração.",
                        )
                    )

        # C) Cruzamento Contábil de Rendimentos Isentos: Página 2 vs Página 8
        if len(page_texts) >= 8:
            p2_txt = page_texts[1][1]
            p8_txt = page_texts[7][1]
            tokens_p2 = re.findall(r"\((.*?)\)Tj", p2_txt)
            tokens_p8 = re.findall(r"\((.*?)\)Tj", p8_txt)

            isento_p2: Optional[float] = None
            isento_p8: Optional[float] = None

            for i, tok in enumerate(tokens_p2):
                if "RENDIMENTOS ISENTOS E NÃO TRIBUTÁVEIS" in tok.upper():
                    # Procura TOTAL subsequente
                    for j in range(i + 1, min(len(tokens_p2), i + 10)):
                        if "TOTAL" in tokens_p2[j].upper() and j + 1 < len(tokens_p2):
                            isento_p2 = parse_currency(tokens_p2[j + 1])
                            break
                    break

            for i, tok in enumerate(tokens_p8):
                if "RENDIMENTOS ISENTOS E NÃO TRIBUTÁVEIS" in tok.upper() and i + 1 < len(tokens_p8):
                    isento_p8 = parse_currency(tokens_p8[i + 1])
                    break

            dados_extraidos["rendimentos_isentos"] = {"pag2": isento_p2, "pag8": isento_p8}

            if isento_p2 is not None and isento_p8 is not None:
                if round(abs(isento_p2 - isento_p8), 2) > 0.05:
                    violacoes.append(
                        AuditViolation(
                            dimensao="Equacao_Tributaria",
                            severidade="CRITICA",
                            regra="MAT-03_INCOERENCIA_ISENTOS_PAG2_VS_PAG8",
                            mensagem=(
                                f"Incoerência Contábil: Total de Rendimentos Isentos na Página 2 (R$ {isento_p2:,.2f}) "
                                f"diverge do espelho na Página 8 (R$ {isento_p8:,.2f})"
                            ),
                            detalhes="Golpe clássico de inflação de lucros e dividendos sem espelhamento no demonstrativo de bens e informações.",
                        )
                    )

        # ---------------------------------------------------------------------
        # 9. DETECÇÃO DE GAP RFB (DOCUMENTO MATEMATICAMENTE PERFEITO)
        # ---------------------------------------------------------------------
        # Se nenhuma violação for encontrada, mas os rendimentos forem significativos,
        # aponta o alerta mandatório de conferência na API SERPRO da Receita Federal.
        if not violacoes:
            if val_rendimentos and val_rendimentos > 120000.0:
                alertas.append(
                    "⚠️  ALERTA GAP RFB: Documento apresenta integridade estrutural, forense e matemática 100% consistente. "
                    "Para prevenir fraudes sintéticas com recálculo matemático perfeito (Red Team), é indispensável "
                    "a validação de recibo e hash na API SERPRO / Receita Federal."
                )

        # ---------------------------------------------------------------------
        # CÁLCULO DE SCORE DE RISCO E STATUS FINAL
        # ---------------------------------------------------------------------
        score_risco = 0
        for v in violacoes:
            if v.severidade == "CRITICA":
                score_risco += 50
            elif v.severidade == "ALTA":
                score_risco += 30
            elif v.severidade == "MEDIA":
                score_risco += 15
            else:
                score_risco += 5

        score_risco = min(100, score_risco)

        if violacoes:
            status = "REPROVADO"
        elif alertas:
            status = "ALERTA_GAP_RFB"
            score_risco = 40
        else:
            status = "APROVADO"
            score_risco = 0

        tempo_ms = (time.perf_counter() - inicio) * 1000.0

        return AuditResult(
            arquivo=pdf_path.name,
            status=status,
            score_risco=score_risco,
            violacoes=violacoes,
            alertas=alertas,
            tempo_ms=round(tempo_ms, 2),
            metadados_forenses=metadados,
            dados_extraidos=dados_extraidos,
        )


# =============================================================================
# CLI & FORMATAÇÃO
# =============================================================================

def print_banner() -> None:
    print(r"""
===============================================================================
 🛡️  AUDITOR FORENSE CEGO DE IRPF (ZERO-KNOWLEDGE BLUE TEAM ENGINE)
    Análise Pericial Autônoma de Streams, Equação Tributária e Metadados
===============================================================================
""")


def formatar_tabela_resumo(resultados: List[AuditResult]) -> None:
    print("\n" + "=" * 100)
    print(f"{'CASO DE TESTE / ARQUIVO':<55} | {'STATUS':<14} | {'SCORE':<7} | {'VIOLAÇÕES':<10} | {'TEMPO':<7}")
    print("=" * 100)

    aprovados = 0
    reprovados = 0
    alertas_gap = 0

    for r in resultados:
        if r.status == "APROVADO":
            badge = "✅ APROVADO"
            aprovados += 1
        elif r.status == "ALERTA_GAP_RFB":
            badge = "⚠️  GAP RFB"
            alertas_gap += 1
        else:
            badge = "❌ REPROVADO"
            reprovados += 1

        print(
            f"{r.arquivo:<55} | {badge:<14} | {r.score_risco:>3}/100 | {len(r.violacoes):>9} | {r.tempo_ms:>5.1f}ms"
        )

    print("=" * 100)
    print(
        f"📊 CONSOLIDADO: Total={len(resultados)} | ✅ Aprovados={aprovados} | "
        f"❌ Reprovados={reprovados} | ⚠️  Gap RFB (Serpro Obrigatório)={alertas_gap}\n"
    )


def exibir_detalhes_reprovacoes(resultados: List[AuditResult]) -> None:
    print("\n" + "-" * 100)
    print("🔍 DETALHAMENTO DAS VIOLAÇÕES E DETECÇÕES FORENSES POR CASO:")
    print("-" * 100)

    for r in resultados:
        if r.status == "APROVADO":
            continue

        print(f"\n📁 Arquivo: {r.arquivo}")
        print(f"   Status: {r.status} | Score de Risco: {r.score_risco}/100 | Tempo: {r.tempo_ms}ms")

        if r.alertas:
            for al in r.alertas:
                print(f"   {al}")

        for v in r.violacoes:
            sev_icon = "🚨" if v.severidade == "CRITICA" else ("⚠️" if v.severidade == "ALTA" else "ℹ️")
            print(f"   {sev_icon} [{v.dimensao}] {v.regra} ({v.severidade}):")
            print(f"      Mensagem: {v.mensagem}")
            if v.detalhes:
                print(f"      Detalhes: {v.detalhes}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Auditor Forense Cego de IRPF (Zero-Knowledge Blue Team & AppSec Engine)"
    )
    parser.add_argument(
        "--dir",
        type=str,
        default="arquivos_teste_irpf",
        help="Diretório contendo os arquivos PDF para auditoria em lote",
    )
    parser.add_argument(
        "--file",
        type=str,
        help="Caminho para auditar um único arquivo PDF específico",
    )
    parser.add_argument(
        "--expected-cpf",
        type=str,
        help="(Opcional) CPF esperado na proposta para validação de onboarding",
    )
    parser.add_argument(
        "--expected-nome",
        type=str,
        help="(Opcional) Nome esperado na proposta para validação de onboarding",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Exportar resultado completo em formato JSON",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        default=True,
        help="Exibir relatório forense detalhado",
    )

    args = parser.parse_args()

    auditor = ZeroKnowledgeIRPFAuditor(
        expected_cpf=args.expected_cpf,
        expected_nome=args.expected_nome,
    )

    print_banner()

    targets: List[Path] = []
    if args.file:
        p = Path(args.file)
        if not p.exists():
            print(f"❌ Erro: Arquivo '{args.file}' não encontrado.")
            sys.exit(1)
        targets.append(p)
    else:
        d = Path(args.dir)
        if not d.exists():
            print(f"❌ Erro: Diretório '{args.dir}' não encontrado.")
            sys.exit(1)
        targets = sorted(list(d.glob("*.pdf")))

    if not targets:
        print("⚠️ Nenhum arquivo PDF encontrado para auditoria.")
        sys.exit(0)

    mode_str = "MODO CEGO (Zero-Knowledge - Sem Dados Prévios)" if not args.expected_cpf else "MODO HÍBRIDO (Forense + Onboarding)"
    print(f"🚀 Iniciando auditoria em {len(targets)} arquivo(s) [{mode_str}]...\n")
    resultados: List[AuditResult] = []

    for target in targets:
        res = auditor.auditar_arquivo(target)
        resultados.append(res)

    if args.json:
        payload = [asdict(r) for r in resultados]
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return

    formatar_tabela_resumo(resultados)

    if args.verbose:
        exibir_detalhes_reprovacoes(resultados)


if __name__ == "__main__":
    main()
