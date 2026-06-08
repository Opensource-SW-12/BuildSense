"""
소켓/플랫폼 기반 하드웨어 호환성 매핑 유틸리티.

지원 소켓: AM4, AM5, LGA 1200, LGA 1700, LGA 1851
"""
import re

# ── 소켓 → PCIe 세대 ──────────────────────────────────────────────────

SOCKET_PCIE_GEN: dict[str, int] = {
    "AM5":      5,
    "LGA 1851": 5,
    "AM4":      4,
    "LGA 1700": 4,
    "LGA 1200": 4,
}

# ── 소켓 → RAM 타입 (None = 보드에 따라 DDR4/DDR5 혼용) ───────────────

SOCKET_RAM_TYPE: dict[str, str | None] = {
    "AM5":      "DDR5",
    "LGA 1851": "DDR5",
    "AM4":      "DDR4",
    "LGA 1200": "DDR4",
    "LGA 1700": None,
}

# ── 소켓 → 호환 CPU 이름 패턴 (PassMark 목록 필터용) ──────────────────

_SOCKET_CPU_PATTERNS: dict[str, list[re.Pattern]] = {
    "AM4": [
        re.compile(r"ryzen\s+[3579]\s+[1-5]\d{3}", re.I),
    ],
    "AM5": [
        re.compile(r"ryzen\s+[3579]\s+[7-9]\d{3}", re.I),
    ],
    "LGA 1200": [
        re.compile(r"core\s+i[3579]-1[01]\d{3}", re.I),
    ],
    "LGA 1700": [
        re.compile(r"core\s+i[3579]-1[234]\d{3}", re.I),
    ],
    "LGA 1851": [
        re.compile(r"core\s+ultra\s+[3579]\s+2\d{2}", re.I),
    ],
}


def socket_to_pcie_gen(socket: str | None) -> int | None:
    return SOCKET_PCIE_GEN.get(socket or "")


def socket_to_ram_type(socket: str | None) -> str | None:
    return SOCKET_RAM_TYPE.get(socket or "")


def cpu_patterns_for_socket(socket: str | None) -> list[re.Pattern]:
    return _SOCKET_CPU_PATTERNS.get(socket or "", [])


def infer_socket_from_cpu_name(cpu_name: str) -> str | None:
    """CPU 모델명 문자열에서 소켓 타입을 추론한다."""
    name = (cpu_name or "").lower()
    # OS가 보고하는 이름에는 "(R)", "(TM)" 같은 상표 표기가 토큰 사이에 끼어 있어
    # "core ultra"/"core i5" 같은 패턴 매칭을 방해하므로 제거한다
    name = re.sub(r"\(\s*[a-z]+\s*\)", " ", name)

    # Intel Core Ultra 2xx (Arrow Lake-S) → LGA 1851
    if re.search(r"core\s+ultra\s+[3579]\s+2\d{2}", name):
        return "LGA 1851"

    # Intel Core iX-NNNNN (5자리 모델번호)
    m = re.search(r"core\s+i[3579]-(\d{5})", name)
    if m:
        prefix = int(m.group(1)[:2])
        if 12 <= prefix <= 14:
            return "LGA 1700"
        if prefix in (10, 11):
            return "LGA 1200"

    # AMD Ryzen X NNNN
    m = re.search(r"ryzen\s+[3579]\s+(\d)\d{3}", name)
    if m:
        gen = int(m.group(1))
        if gen >= 7:
            return "AM5"
        if 1 <= gen <= 5:
            return "AM4"

    return None
