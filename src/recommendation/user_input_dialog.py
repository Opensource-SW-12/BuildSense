import json
import tkinter as tk
from tkinter import messagebox
from collections import defaultdict

from src.config import PROCESS_CATEGORIES_PATH

# ── 다크 테마 색상 (app.py 화면들과 통일) ─────────────────────────
_BG     = "#1A1F2E"
_CARD   = "#1E2438"
_TEAL   = "#00C9A7"
_WHITE  = "#E8EAF0"
_GRAY   = "#9AA1C2"
_DIVIDER = "#252D45"

_IMPACT_MIN_RATIO = 0.05  # 전체 스냅샷 중 5% 이상 등장
_IMPACT_MIN_CPU   = 3.0   # 평균 CPU 사용률 3% 이상
_IMPACT_MIN_MEM   = 50.0  # 평균 메모리 50 MB 이상
_MAX_UNKNOWN_PROCS = 5    # 최대 질문 개수

_MIN_REASONABLE_BUDGET = 100_000  # 부품 한 개 업그레이드에 필요한 최소 권장 예산(원) — 이보다 낮으면 경고
_BUDGET_MAX = 999_999_999
_BUDGET_PLACEHOLDER = "맞춤 설정"

# 예산 모드 정의 (값, 라벨, 설명)
_BUDGET_MODES = [
    ("recommended", "맞춤 설정 (추천)",
     "시스템 분석 결과와 예산 효율을 고려해 가장 적절한 수준으로 제품을 추천합니다."),
    ("max",         "최고 가격",
     "예산 제한 없이 가장 훌륭한 성능의 제품을 추천합니다."),
    ("custom",      "직접 설정",
     "추천 부품별로 직접 예산 상한을 설정합니다. 설정하지 않은 부품은 제한 없음으로 처리됩니다."),
]

# 사용자 프로필 부품명(한국어) → 파이프라인 부품 키 매핑
_PROFILE_TO_PIPELINE: dict[str, str] = {
    "CPU":   "CPU",
    "GPU":   "GPU",
    "RAM":   "RAM",
    "SSD":   "SSD",
    "HDD":   "HDD",
    "메인보드": "Motherboard",
    "파워":   "PSU",
}

def _rrect(c, x1, y1, x2, y2, r, fill):
    """Canvas에 둥근 모서리 사각형을 그린다."""
    kw = dict(fill=fill, outline=fill)
    c.create_arc(x1,     y1,     x1+2*r, y1+2*r, start=90,  extent=90,  **kw)
    c.create_arc(x2-2*r, y1,     x2,     y1+2*r, start=0,   extent=90,  **kw)
    c.create_arc(x2-2*r, y2-2*r, x2,     y2,     start=270, extent=90,  **kw)
    c.create_arc(x1,     y2-2*r, x1+2*r, y2,     start=180, extent=90,  **kw)
    c.create_rectangle(x1+r, y1,   x2-r, y2,   **kw)
    c.create_rectangle(x1,   y1+r, x2,   y2-r, **kw)


def _hex_mix(c1: str, c2: str, t: float) -> str:
    r1, g1, b1 = int(c1[1:3], 16), int(c1[3:5], 16), int(c1[5:7], 16)
    r2, g2, b2 = int(c2[1:3], 16), int(c2[3:5], 16), int(c2[5:7], 16)
    return "#{:02x}{:02x}{:02x}".format(
        int(r1 + (r2-r1)*t), int(g1 + (g2-g1)*t), int(b1 + (b2-b1)*t)
    )


def _make_pill_btn(parent, text, command, bg_color, fg_color, width=140, height=38):
    """캔버스 기반 알약형 버튼을 생성하고 반환한다."""
    c = tk.Canvas(parent, width=width, height=height,
                  bg=parent.cget("bg"), highlightthickness=0, cursor="hand2")
    r = height // 2

    def _draw(color=None):
        c.delete("all")
        _rrect(c, 0, 0, width, height, r, color or bg_color)
        c.create_text(width // 2, height // 2, text=text,
                      fill=fg_color, font=("Segoe UI", 10, "bold"))

    c.bind("<Button-1>", lambda e: command())
    c.bind("<Enter>", lambda e: _draw(_hex_mix(bg_color, "#ffffff", 0.12)))
    c.bind("<Leave>", lambda e: _draw())
    _draw()
    return c


_RGB_DESCRIPTIONS = {
    "beginner":     "RGB 선호도란 본체 내부에 화려한 LED 조명 효과가 있는 부품을 선호하는지를 의미합니다. 추천 부품을 고를 때 디자인 취향을 반영하는 데 사용됩니다.",
    "intermediate": "RGB 선호도는 추천 후보를 고를 때 LED 조명 효과 유무를 고려할지 결정하는 항목입니다.",
}

_COLOR_DESCRIPTIONS = {
    "beginner":     "부품 색상 선호도입니다. 블랙 또는 화이트 계열 부품을 선택하면 RAM·메인보드·파워 검색 시 해당 색상을 우선 반영합니다.",
    "intermediate": "색상 선호도를 설정하면 RAM·메인보드·파워 검색 쿼리에 블랙 또는 화이트 키워드가 추가됩니다.",
}

_CATEGORY_LABELS = [
    ("게임",             "game"),
    ("개발·프로그래밍", "development"),
    ("영상·이미지 편집", "creative"),
    ("업무·생산성",     "business"),
    ("스트리밍·방송",   "streaming"),
    ("웹 브라우저",     "browser"),
    ("기타",             "etc"),
]
_DISPLAY_TEXTS = [t for t, _ in _CATEGORY_LABELS]
_TEXT_TO_VALUE = {t: v for t, v in _CATEGORY_LABELS}
_VALUE_TO_TEXT = {v: t for t, v in _CATEGORY_LABELS}


def _load_known_process_names() -> set[str] | None:
    try:
        if not PROCESS_CATEGORIES_PATH.exists():
            return None
        with open(PROCESS_CATEGORIES_PATH, "r", encoding="utf-8") as f:
            raw = json.load(f)
        known: set[str] = set()
        for names in raw.values():
            for name in names:
                known.add(name.lower())
        return known
    except Exception:
        return None


def find_impactful_unknown_processes(logs: list[dict]) -> list[dict]:
    """로그에서 process_categories에 없으면서 영향력 있는 프로세스를 반환한다."""
    known = _load_known_process_names()
    if known is None or not logs:
        return []

    total = len(logs)
    appearance: dict[str, int]   = defaultdict(int)
    cpu_sum:    dict[str, float]  = defaultdict(float)
    cpu_cnt:    dict[str, int]    = defaultdict(int)
    mem_sum:    dict[str, float]  = defaultdict(float)
    mem_cnt:    dict[str, int]    = defaultdict(int)

    for log in logs:
        seen: set[str] = set()
        for proc in log.get("processes", []):
            name = (proc.get("name") or "").lower().strip()
            if not name or name in seen:
                continue
            seen.add(name)
            appearance[name] += 1
            cpu = proc.get("cpu_percent")
            if cpu is not None:
                cpu_sum[name] += cpu
                cpu_cnt[name] += 1
            mem = proc.get("memory_mb")
            if mem is not None:
                mem_sum[name] += mem
                mem_cnt[name] += 1

    results = []
    for name in appearance:
        if name in known:
            continue
        ratio   = appearance[name] / total
        avg_cpu = cpu_sum[name] / cpu_cnt[name] if cpu_cnt[name] > 0 else 0.0
        avg_mem = mem_sum[name] / mem_cnt[name] if mem_cnt[name] > 0 else 0.0

        if ratio < _IMPACT_MIN_RATIO:
            continue
        if avg_cpu < _IMPACT_MIN_CPU and avg_mem < _IMPACT_MIN_MEM:
            continue

        results.append({
            "name":             name,
            "appearance_ratio": ratio,
            "avg_cpu_percent":  avg_cpu,
            "avg_memory_mb":    avg_mem,
        })

    results.sort(key=lambda x: x["appearance_ratio"], reverse=True)
    return results[:_MAX_UNKNOWN_PROCS]


class UserPreferenceDialog:
    """분석 시작 전 예산·RGB·미분류 프로세스 수집 다이얼로그."""

    def __init__(
        self,
        parent: tk.Tk,
        unknown_procs: list[dict],
        on_confirm,
        on_cancel,
        knowledge_level: str | None = None,
        parts: dict | None = None,
    ):
        self._parent          = parent
        self._unknown_procs   = unknown_procs
        self._on_confirm      = on_confirm
        self._on_cancel       = on_cancel
        self._knowledge_level = knowledge_level
        self._parts           = parts or {}
        self._proc_vars: dict[str, tk.StringVar] = {}
        self._part_budgets: dict[str, int] = {}  # 직접 설정 모드에서 부품별 예산

        self._dialog = tk.Toplevel(parent)
        self._dialog.title("추가 정보 입력")
        self._dialog.resizable(False, False)
        self._dialog.configure(bg=_BG)
        self._dialog.grab_set()
        self._dialog.protocol("WM_DELETE_WINDOW", self._handle_cancel)

        self._build_ui()
        self._place_dialog()

    # ------------------------------------------------------------------

    def _place_dialog(self):
        self._dialog.update_idletasks()
        px, py = self._parent.winfo_x(), self._parent.winfo_y()
        pw, ph = self._parent.winfo_width(), self._parent.winfo_height()
        dw = 500
        dh = self._dialog.winfo_reqheight() + 24
        x = px + (pw - dw) // 2
        y = py + (ph - dh) // 2
        self._dialog.geometry(f"{dw}x{dh}+{x}+{y}")

    def _build_ui(self):
        outer = tk.Frame(self._dialog, bg=_BG, padx=24, pady=20)
        outer.pack(fill=tk.BOTH, expand=True)

        def _divider(parent, pady=(0, 14)):
            tk.Frame(parent, height=1, bg=_DIVIDER).pack(fill=tk.X, pady=pady)

        def _section_title(text, pady=(0, 6)):
            tk.Label(outer, text=text, fg=_WHITE, bg=_BG,
                     font=("Segoe UI", 11, "bold"), anchor="w").pack(fill=tk.X, pady=pady)

        # ── 예산 ─────────────────────────────────────────────────
        _section_title("예산 설정")

        self._budget_mode_var = tk.StringVar(value="recommended")
        self._budget_desc_var = tk.StringVar(value=_BUDGET_MODES[0][2])

        mode_row = tk.Frame(outer, bg=_BG)
        mode_row.pack(fill=tk.X, pady=(0, 4))

        def _on_mode_change():
            mode = self._budget_mode_var.get()
            for val, _, desc in _BUDGET_MODES:
                if val == mode:
                    self._budget_desc_var.set(desc)
                    break
            state = tk.NORMAL if mode == "custom" else tk.DISABLED
            self._budget_detail_btn.config(
                state=state,
                fg=_WHITE if mode == "custom" else "#5A6080",
            )

        for val, label, _ in _BUDGET_MODES:
            tk.Radiobutton(
                mode_row,
                text=label,
                variable=self._budget_mode_var,
                value=val,
                font=("Segoe UI", 10),
                command=_on_mode_change,
                bg=_BG, fg=_GRAY, activebackground=_BG, activeforeground=_WHITE,
                selectcolor=_CARD, highlightthickness=0,
            ).pack(side=tk.LEFT, padx=(0, 8))

        self._budget_detail_btn = tk.Button(
            mode_row,
            text="부품별 설정 ▶",
            state=tk.DISABLED,
            command=self._open_budget_detail,
            font=("Segoe UI", 9),
            bg=_DIVIDER, fg="#5A6080", activebackground=_TEAL, activeforeground=_BG,
            relief=tk.FLAT, highlightthickness=0,
            disabledforeground="#5A6080",
        )
        self._budget_detail_btn.pack(side=tk.LEFT, padx=(4, 0))

        tk.Label(
            outer,
            textvariable=self._budget_desc_var,
            fg=_GRAY, bg=_BG, font=("Segoe UI", 9), anchor="w",
            wraplength=455, justify=tk.LEFT,
        ).pack(fill=tk.X, pady=(0, 14))

        _divider(outer)

        # ── RGB ──────────────────────────────────────────────────
        _section_title("RGB 선호도", pady=(0, 4))

        rgb_desc = _RGB_DESCRIPTIONS.get(self._knowledge_level or "")
        if rgb_desc:
            tk.Label(
                outer, text=rgb_desc, fg=_GRAY, bg=_BG, font=("Segoe UI", 9),
                anchor="w", wraplength=450, justify=tk.LEFT,
            ).pack(fill=tk.X, pady=(0, 6))

        self._rgb_var = tk.StringVar(value="none")
        rgb_row = tk.Frame(outer, bg=_BG)
        rgb_row.pack(fill=tk.X, pady=(0, 14))

        for text, value in [("선호함", "yes"), ("선호하지 않음", "no"), ("상관없음", "none")]:
            tk.Radiobutton(
                rgb_row,
                text=text,
                variable=self._rgb_var,
                value=value,
                font=("Segoe UI", 10),
                bg=_BG, fg=_GRAY, activebackground=_BG, activeforeground=_WHITE,
                selectcolor=_CARD, highlightthickness=0,
            ).pack(side=tk.LEFT, padx=(0, 16))

        _divider(outer)

        # ── 색상 ──────────────────────────────────────────────────
        _section_title("색상 선호도", pady=(0, 4))

        color_desc = _COLOR_DESCRIPTIONS.get(self._knowledge_level or "")
        if color_desc:
            tk.Label(
                outer, text=color_desc, fg=_GRAY, bg=_BG, font=("Segoe UI", 9),
                anchor="w", wraplength=450, justify=tk.LEFT,
            ).pack(fill=tk.X, pady=(0, 6))

        self._color_var = tk.StringVar(value="none")
        color_row = tk.Frame(outer, bg=_BG)
        color_row.pack(fill=tk.X, pady=(0, 14))

        for text, value in [("블랙", "black"), ("화이트", "white"), ("상관없음", "none")]:
            tk.Radiobutton(
                color_row,
                text=text,
                variable=self._color_var,
                value=value,
                font=("Segoe UI", 10),
                bg=_BG, fg=_GRAY, activebackground=_BG, activeforeground=_WHITE,
                selectcolor=_CARD, highlightthickness=0,
            ).pack(side=tk.LEFT, padx=(0, 16))

        # ── 미분류 프로세스 ───────────────────────────────────────
        if self._unknown_procs:
            _divider(outer)

            _section_title("미분류 프로그램 확인", pady=(0, 4))

            tk.Label(
                outer,
                text="자주 사용된 프로그램의 용도를 선택하면 사용자 유형 분석 정확도가 높아집니다.",
                fg=_GRAY, bg=_BG, font=("Segoe UI", 9), anchor="w",
                wraplength=450, justify=tk.LEFT,
            ).pack(fill=tk.X, pady=(0, 10))

            for proc in self._unknown_procs:
                row = tk.Frame(outer, bg=_CARD, padx=10, pady=6)
                row.pack(fill=tk.X, pady=(0, 6))

                ratio_pct = f"{proc['appearance_ratio'] * 100:.0f}%"
                cpu_text  = (
                    f"CPU {proc['avg_cpu_percent']:.1f}%"
                    if proc["avg_cpu_percent"] >= _IMPACT_MIN_CPU
                    else f"메모리 {proc['avg_memory_mb']:.0f}MB"
                )

                tk.Label(
                    row, text=proc["name"], fg=_WHITE, bg=_CARD,
                    font=("Segoe UI", 10), anchor="w", width=18,
                ).pack(side=tk.LEFT)

                tk.Label(
                    row, text=f"({ratio_pct}, {cpu_text})", fg=_GRAY, bg=_CARD,
                    font=("Segoe UI", 9), anchor="w", width=16,
                ).pack(side=tk.LEFT)

                var = tk.StringVar(value=_VALUE_TO_TEXT["etc"])
                self._proc_vars[proc["name"]] = var

                om = tk.OptionMenu(row, var, *_DISPLAY_TEXTS)
                om.config(bg=_DIVIDER, fg=_WHITE, activebackground=_TEAL,
                          activeforeground=_BG, highlightthickness=0,
                          relief=tk.FLAT, font=("Segoe UI", 9))
                om["menu"].config(bg=_CARD, fg=_WHITE,
                                  activebackground=_TEAL, activeforeground=_BG)
                om.pack(side=tk.LEFT, padx=(4, 0), fill=tk.X, expand=True)

        # ── 버튼 ─────────────────────────────────────────────────
        _divider(outer, pady=(14, 10))

        btn_row = tk.Frame(outer, bg=_BG)
        btn_row.pack(fill=tk.X)

        _make_pill_btn(
            btn_row, "분석 시작", self._handle_confirm, _TEAL, _BG, width=140, height=38,
        ).pack(side=tk.RIGHT)

    # ------------------------------------------------------------------

    def _open_budget_detail(self):
        recommend_parts = {
            name: data for name, data in self._parts.items()
            if isinstance(data, dict) and data.get("option") == "recommend"
        }
        if not recommend_parts:
            messagebox.showinfo(
                parent=self._dialog,
                title="설정할 부품 없음",
                message="추천 대상 부품이 없습니다.\n설정 화면에서 추천할 부품을 선택하세요.",
            )
            return
        _BudgetDetailDialog(
            parent=self._dialog,
            parts=recommend_parts,
            current_budgets=self._part_budgets,
            on_save=lambda budgets: self._part_budgets.update(budgets),
        )

    def _handle_confirm(self):
        mode = self._budget_mode_var.get()
        result = {
            "budget_mode": mode,
            "budgets": dict(self._part_budgets) if mode == "custom" else {},
            "budget": None,
            "rgb_preference":    self._rgb_var.get(),
            "color_preference":  self._color_var.get(),
            "unknown_process_categories": {
                name: _TEXT_TO_VALUE.get(var.get(), "etc")
                for name, var in self._proc_vars.items()
            },
        }
        self._dialog.destroy()
        self._on_confirm(result)

    def _handle_cancel(self):
        self._dialog.destroy()
        self._on_cancel()


class _BudgetDetailDialog:
    """직접 설정 모드에서 부품별 예산을 입력하는 서브 다이얼로그."""

    def __init__(
        self,
        parent: tk.Toplevel,
        parts: dict,
        current_budgets: dict,
        on_save,
    ):
        self._parent          = parent
        self._parts           = parts
        self._current_budgets = current_budgets
        self._on_save         = on_save
        self._entry_vars: dict[str, tk.StringVar] = {}

        self._dialog = tk.Toplevel(parent)
        self._dialog.title("부품별 예산 설정")
        self._dialog.resizable(False, False)
        self._dialog.configure(bg=_BG)
        self._dialog.grab_set()

        self._build_ui()
        self._place_dialog()

    def _place_dialog(self):
        self._dialog.update_idletasks()
        px, py = self._parent.winfo_x(), self._parent.winfo_y()
        pw, ph = self._parent.winfo_width(), self._parent.winfo_height()
        dw = 380
        dh = self._dialog.winfo_reqheight()
        x = px + (pw - dw) // 2
        y = py + (ph - dh) // 2
        self._dialog.geometry(f"{dw}x{dh}+{x}+{y}")

    def _build_ui(self):
        outer = tk.Frame(self._dialog, bg=_BG, padx=24, pady=20)
        outer.pack(fill=tk.BOTH, expand=True)

        tk.Label(
            outer, text="부품별 예산 설정",
            fg=_WHITE, bg=_BG, font=("Segoe UI", 12, "bold"), anchor="w",
        ).pack(fill=tk.X, pady=(0, 4))

        tk.Label(
            outer,
            text=(
                f"추천 대상 부품의 최대 예산을 입력하세요. (최대 {_BUDGET_MAX:,}원)\n"
                "빈칸('맞춤 설정')으로 두면 해당 부품은 예산 제한 없이 추천됩니다."
            ),
            fg=_GRAY, bg=_BG, font=("Segoe UI", 9), anchor="w",
            justify=tk.LEFT,
        ).pack(fill=tk.X, pady=(0, 12))

        tk.Frame(outer, height=1, bg=_DIVIDER).pack(fill=tk.X, pady=(0, 12))

        for part_name in self._parts:
            pipeline_key = _PROFILE_TO_PIPELINE.get(part_name, part_name)
            row = tk.Frame(outer, bg=_BG)
            row.pack(fill=tk.X, pady=(0, 8))

            tk.Label(
                row, text=part_name, fg=_WHITE, bg=_BG,
                font=("Segoe UI", 10), anchor="w", width=8,
            ).pack(side=tk.LEFT)

            current_val = self._current_budgets.get(pipeline_key)
            has_value = bool(current_val)
            var = tk.StringVar(value=str(current_val) if has_value else _BUDGET_PLACEHOLDER)
            self._entry_vars[pipeline_key] = var

            # 포맷 레이블 (오른쪽 고정, entry보다 먼저 pack해야 fill 공간 계산 올바름)
            fmt_var = tk.StringVar(
                value=f"{min(current_val, _BUDGET_MAX):,}원" if has_value else ""
            )

            def _on_write(*_, _v=var, _fv=fmt_var):
                full = _v.get()
                if not full or full == _BUDGET_PLACEHOLDER:
                    _fv.set("")
                    return
                raw = full.replace(",", "").replace(" ", "")
                if raw.isdigit() and int(raw) > 0:
                    _fv.set(f"{min(int(raw), _BUDGET_MAX):,}원")
                else:
                    _fv.set("")

            var.trace_add("write", _on_write)

            # 포맷 레이블 (RIGHT에 먼저 pack)
            tk.Label(
                row, textvariable=fmt_var,
                fg=_TEAL, bg=_BG, font=("Segoe UI", 9), anchor="e", width=14,
            ).pack(side=tk.RIGHT)

            entry = tk.Entry(
                row,
                textvariable=var,
                font=("Segoe UI", 10),
                bg=_CARD, fg=_GRAY if not has_value else _WHITE,
                insertbackground=_WHITE,
                relief=tk.FLAT, highlightthickness=1,
                highlightbackground=_DIVIDER, highlightcolor=_TEAL,
            )
            entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=4, ipadx=6, padx=(0, 6))

            def _on_focus_in(e, w=entry, v=var):
                if v.get() == _BUDGET_PLACEHOLDER:
                    v.set("")
                    w.config(fg=_WHITE)

            def _on_focus_out(e, w=entry, v=var):
                if not v.get():
                    v.set(_BUDGET_PLACEHOLDER)
                    w.config(fg=_GRAY)

            entry.bind("<FocusIn>",  _on_focus_in)
            entry.bind("<FocusOut>", _on_focus_out)

        tk.Frame(outer, height=1, bg=_DIVIDER).pack(fill=tk.X, pady=(8, 10))

        btn_row = tk.Frame(outer, bg=_BG)
        btn_row.pack(fill=tk.X)

        _make_pill_btn(
            btn_row, "취소", self._dialog.destroy, _DIVIDER, _GRAY, width=100, height=36,
        ).pack(side=tk.RIGHT, padx=(8, 0))

        _make_pill_btn(
            btn_row, "저장", self._handle_save, _TEAL, _BG, width=100, height=36,
        ).pack(side=tk.RIGHT)

    def _handle_save(self):
        budgets: dict[str, int] = {}
        for pipeline_key, var in self._entry_vars.items():
            full = var.get()
            if not full or full == _BUDGET_PLACEHOLDER:
                continue
            raw = full.replace(",", "").replace(" ", "")
            try:
                val = int(raw)
                if val <= 0:
                    messagebox.showwarning(
                        parent=self._dialog,
                        title="입력 오류",
                        message="예산은 0보다 큰 숫자를 입력하세요.",
                    )
                    return
                budgets[pipeline_key] = min(val, _BUDGET_MAX)
            except ValueError:
                messagebox.showwarning(
                    parent=self._dialog,
                    title="입력 오류",
                    message="숫자만 입력 가능합니다. 문자나 기호는 입력할 수 없습니다.",
                )
                return
        self._on_save(budgets)
        self._dialog.destroy()
