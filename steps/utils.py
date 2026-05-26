"""共用工具函数 — 供 step_04 / step_06 等共享使用。"""
from __future__ import annotations

_SCENE_KEYWORDS = [
    "全景", "工位", "办公", "区", "背景", "环境", "小巷",
    "街道", "屋顶", "城市", "室内", "深夜", "清晨", "走廊",
]

_CHAR_PREFIXES = (
    "阿", "张", "王", "李", "刘", "陈", "杨", "赵", "黄", "周",
    "吴", "徐", "孙", "胡", "朱", "高", "林", "何", "郭", "马", "小",
)

_EXPLICIT_CHARS = frozenset([
    "主角", "配角", "反派", "同事A", "同事B", "主管", "领导", "小李",
    "阿强", "张主管",
])


def is_likely_character(name: str) -> bool:
    """判断 @ 引用名称是否对应角色（而非场景/道具）。

    合并自 step_04 与 step_06 的各自定义，step_06 版本额外覆盖了
    「阿强」「张主管」等显式名称，此处统一保留。
    """
    if any(kw in name for kw in _SCENE_KEYWORDS):
        return False
    if any(name.startswith(p) for p in _CHAR_PREFIXES):
        return True
    if name in _EXPLICIT_CHARS:
        return True
    return len(name) <= 4
