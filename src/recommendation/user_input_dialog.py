import json
import tkinter as tk
from tkinter import messagebox
from collections import defaultdict

from src.config import PROCESS_CATEGORIES_PATH

_IMPACT_MIN_RATIO = 0.05  # 전체 스냅샷 중 5% 이상 등장
_IMPACT_MIN_CPU   = 3.0   # 평균 CPU 사용률 3% 이상
_IMPACT_MIN_MEM   = 50.0  # 평균 메모리 50 MB 이상
_MAX_UNKNOWN_PROCS = 5    # 최대 질문 개수

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
    ):
        self._parent       = parent
        self._unknown_procs = unknown_procs
        self._on_confirm   = on_confirm
        self._on_cancel    = on_cancel
        self._proc_vars: dict[str, tk.StringVar] = {}

        self._dialog = tk.Toplevel(parent)
        self._dialog.title("추가 정보 입력")
        self._dialog.resizable(False, False)
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
        dh = self._dialog.winfo_reqheight()
        x = px + (pw - dw) // 2
        y = py + (ph - dh) // 2
        self._dialog.geometry(f"{dw}x{dh}+{x}+{y}")

    def _build_ui(self):
        outer = tk.Frame(self._dialog, padx=24, pady=20)
        outer.pack(fill=tk.BOTH, expand=True)

        # ── 예산 ─────────────────────────────────────────────────
        tk.Label(
            outer,
            text="예산 설정",
            font=("Segoe UI", 11, "bold"),
            anchor="w",
        ).pack(fill=tk.X, pady=(0, 6))

        budget_row = tk.Frame(outer)
        budget_row.pack(fill=tk.X, pady=(0, 2))

        self._no_budget_var = tk.BooleanVar(value=False)
        self._budget_var    = tk.StringVar()

        self._budget_entry = tk.Entry(
            budget_row,
            textvariable=self._budget_var,
            font=("Segoe UI", 10),
            width=18,
        )
        self._budget_entry.pack(side=tk.LEFT)
        tk.Label(budget_row, text=" 원", font=("Segoe UI", 10)).pack(side=tk.LEFT)

        def _toggle_budget():
            self._budget_entry.config(
                state=tk.DISABLED if self._no_budget_var.get() else tk.NORMAL
            )

        tk.Checkbutton(
            budget_row,
            text="설정 안 함",
            variable=self._no_budget_var,
            font=("Segoe UI", 10),
            command=_toggle_budget,
        ).pack(side=tk.LEFT, padx=(16, 0))

        tk.Label(
            outer,
            text="※ 부품 하나에 투자 가능한 최대 금액 (예: 500000)",
            font=("Segoe UI", 9),
            fg="#888888",
            anchor="w",
        ).pack(fill=tk.X, pady=(0, 14))

        tk.Frame(outer, height=1, bg="#cccccc").pack(fill=tk.X, pady=(0, 14))

        # ── RGB ──────────────────────────────────────────────────
        tk.Label(
            outer,
            text="RGB 선호도",
            font=("Segoe UI", 11, "bold"),
            anchor="w",
        ).pack(fill=tk.X, pady=(0, 8))

        self._rgb_var = tk.StringVar(value="none")
        rgb_row = tk.Frame(outer)
        rgb_row.pack(fill=tk.X, pady=(0, 14))

        for text, value in [("선호함", "yes"), ("선호하지 않음", "no"), ("상관없음", "none")]:
            tk.Radiobutton(
                rgb_row,
                text=text,
                variable=self._rgb_var,
                value=value,
                font=("Segoe UI", 10),
            ).pack(side=tk.LEFT, padx=(0, 16))

        tk.Frame(outer, height=1, bg="#cccccc").pack(fill=tk.X, pady=(0, 14))

        # ── 메인보드 업그레이드 ───────────────────────────────────
        tk.Label(
            outer,
            text="메인보드 업그레이드",
            font=("Segoe UI", 11, "bold"),
            anchor="w",
        ).pack(fill=tk.X, pady=(0, 8))

        self._motherboard_var = tk.StringVar(value="keep")
        mb_row = tk.Frame(outer)
        mb_row.pack(fill=tk.X, pady=(0, 4))

        for text, value in [("현재 메인보드 유지", "keep"), ("메인보드 교체 포함", "recommend")]:
            tk.Radiobutton(
                mb_row,
                text=text,
                variable=self._motherboard_var,
                value=value,
                font=("Segoe UI", 10),
            ).pack(side=tk.LEFT, padx=(0, 16))

        tk.Label(
            outer,
            text="※ '교체 포함' 선택 시 소켓 제약 없이 CPU를 추천하고 호환 메인보드도 함께 제안합니다",
            font=("Segoe UI", 9),
            fg="#888888",
            anchor="w",
            wraplength=450,
            justify=tk.LEFT,
        ).pack(fill=tk.X, pady=(0, 14))

        # ── 미분류 프로세스 ───────────────────────────────────────
        if self._unknown_procs:
            tk.Frame(outer, height=1, bg="#cccccc").pack(fill=tk.X, pady=(0, 14))

            tk.Label(
                outer,
                text="미분류 프로그램 확인",
                font=("Segoe UI", 11, "bold"),
                anchor="w",
            ).pack(fill=tk.X, pady=(0, 4))

            tk.Label(
                outer,
                text="자주 사용된 프로그램의 용도를 선택하면 사용자 유형 분석 정확도가 높아집니다.",
                font=("Segoe UI", 9),
                fg="#555555",
                anchor="w",
                wraplength=450,
                justify=tk.LEFT,
            ).pack(fill=tk.X, pady=(0, 10))

            for proc in self._unknown_procs:
                row = tk.Frame(outer)
                row.pack(fill=tk.X, pady=(0, 6))

                ratio_pct = f"{proc['appearance_ratio'] * 100:.0f}%"
                cpu_text  = (
                    f"CPU {proc['avg_cpu_percent']:.1f}%"
                    if proc["avg_cpu_percent"] >= _IMPACT_MIN_CPU
                    else f"메모리 {proc['avg_memory_mb']:.0f}MB"
                )

                tk.Label(
                    row,
                    text=proc["name"],
                    font=("Segoe UI", 10),
                    anchor="w",
                    width=24,
                ).pack(side=tk.LEFT)

                tk.Label(
                    row,
                    text=f"({ratio_pct}, {cpu_text})",
                    font=("Segoe UI", 9),
                    fg="#666666",
                    anchor="w",
                    width=20,
                ).pack(side=tk.LEFT)

                var = tk.StringVar(value=_VALUE_TO_TEXT["etc"])
                self._proc_vars[proc["name"]] = var

                tk.OptionMenu(row, var, *_DISPLAY_TEXTS).pack(
                    side=tk.LEFT, padx=(4, 0)
                )

        # ── 버튼 ─────────────────────────────────────────────────
        tk.Frame(outer, height=1, bg="#cccccc").pack(fill=tk.X, pady=(14, 10))

        btn_row = tk.Frame(outer)
        btn_row.pack(fill=tk.X)

        tk.Button(
            btn_row,
            text="취소",
            width=10,
            command=self._handle_cancel,
        ).pack(side=tk.RIGHT, padx=(8, 0))

        tk.Button(
            btn_row,
            text="확인",
            width=10,
            command=self._handle_confirm,
        ).pack(side=tk.RIGHT)

    # ------------------------------------------------------------------

    def _handle_confirm(self):
        budget = None
        if not self._no_budget_var.get():
            raw = self._budget_var.get().replace(",", "").replace(" ", "")
            if raw:
                try:
                    budget = int(raw)
                    if budget <= 0:
                        messagebox.showwarning(
                            parent=self._dialog,
                            title="입력 오류",
                            message="예산은 0보다 큰 숫자를 입력하세요.",
                        )
                        return
                except ValueError:
                    messagebox.showwarning(
                        parent=self._dialog,
                        title="입력 오류",
                        message="예산은 숫자만 입력 가능합니다.",
                    )
                    return

        result = {
            "budget": budget,
            "rgb_preference": self._rgb_var.get(),
            "upgrade_motherboard": self._motherboard_var.get() == "recommend",
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
