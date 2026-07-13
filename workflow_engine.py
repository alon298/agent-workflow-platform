#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Agent Workflow Platform - 多智能体工作流编排引擎（对标 Dify/Langflow）。"""
import json, time
from pathlib import Path

# ---------------- 工具注册表 ----------------
class ToolRegistry:
    def __init__(self):
        self._tools = {}

    def register(self, name, desc, params, func):
        self._tools[name] = {"desc": desc, "params": params, "func": func}

    def call(self, name, **kw):
        if name not in self._tools:
            raise KeyError(f"工具未注册: {name}")
        return self._tools[name]["func"](**kw)

    def schema(self):
        return {n: {"desc": t["desc"], "params": t["params"]} for n, t in self._tools.items()}

# ---------------- 节点定义 ----------------
class Node:
    kind = "base"
    def run(self, state, ctx): raise NotImplementedError

class StartNode(Node):
    kind = "start"
    def __init__(self, **inputs): self.inputs = inputs
    def run(self, state, ctx): return dict(self.inputs)

class EndNode(Node):
    kind = "end"
    def run(self, state, ctx): return {"done": True}

class ToolNode(Node):
    kind = "tool"
    def __init__(self, tool, args=None, out=None):
        self.tool, self.args, self.out = tool, args or {}, out or tool
    def run(self, state, ctx):
        kw = {k: state.get(v[1:], v) if isinstance(v, str) and v.startswith("$") else v for k, v in self.args.items()}
        result = ctx["tools"].call(self.tool, **kw)
        return {self.out: result}

class LLMNode(Node):
    kind = "llm"
    def __init__(self, out="text", system="", template=""):
        self.out, self.system, self.template = out, system, template
    def run(self, state, ctx):
        prompt = self.template.format(**{k: state.get(k, "") for k in _keys(self.template)})
        if ctx.get("llm"):
            text = ctx["llm"](self.system, prompt)
        else:  # 无 LLM 时模板降级
            text = prompt
        return {self.out: text}

class HumanConfirmNode(Node):
    kind = "human_confirm"
    def __init__(self, question="确认继续？", out="confirmed"):
        self.question, self.out = question, out
    def run(self, state, ctx):
        if ctx.get("auto_approve"):
            return {self.out: True}
        if ctx.get("interactive"):
            ans = input(f"[人工确认] {self.question} (y/n) ").strip().lower()
            return {self.out: ans == "y"}
        return {self.out: False}

class ConditionalRouter(Node):
    kind = "route"
    def __init__(self, key, mapping, default=None):
        self.key, self.mapping, self.default = key, mapping, default
    def run(self, state, ctx):
        val = state.get(self.key)
        for cond, target in self.mapping.items():
            if _match(cond, val):
                ctx["next_override"] = target
                return {}
        if self.default:
            ctx["next_override"] = self.default
        return {}

def _keys(template):
    import string
    return [fn for _, fn, _, _ in string.Formatter().parse(template) if fn]

def _match(cond, val):
    if cond == "*": return True
    if cond.startswith("=="): return str(val) == cond[2:]
    if cond.startswith("!="): return str(val) != cond[2:]
    return str(val) == cond

# ---------------- 执行引擎（日志 + 检查点回溯）----------------
class Graph:
    def __init__(self, name="workflow"):
        self.name, self.nodes, self.edges = name, {}, {}

    def add(self, nid, node, nxt=None):
        self.nodes[nid] = node
        if nxt: self.edges[nid] = nxt
        return self

    def execute(self, state=None, ctx=None, checkpoint_dir="checkpoints"):
        state, ctx = state or {}, ctx or {}
        ctx.setdefault("tools", ToolRegistry())
        ctx.setdefault("trace", [])
        nid = "start"
        step = 0
        cp = Path(checkpoint_dir) / self.name
        cp.mkdir(parents=True, exist_ok=True)
        while nid and nid in self.nodes:
            node = self.nodes[nid]
            patch = node.run(state, ctx) or {}
            state.update(patch)
            ctx["trace"].append({"step": step, "node": nid, "kind": node.kind,
                                 "patch": {k: str(v)[:120] for k, v in patch.items()}, "ts": time.time()})
            (cp / f"step{step:03d}.json").write_text(json.dumps(state, ensure_ascii=False, default=str), encoding="utf-8")
            step += 1
            nid = ctx.pop("next_override", None) or self.edges.get(nid)
        return state, ctx["trace"]

# ---------------- 内置示例工具 ----------------
def default_registry():
    reg = ToolRegistry()
    reg.register("sensitive_check", "敏感词检查，返回命中词列表",
                 {"text": "待检查文本"}, lambda text: [w for w in ["最", "第一", "国家级", "秒杀"] if w in text])
    reg.register("word_count", "统计字数", {"text": "文本"}, lambda text: len(text))
    return reg

if __name__ == "__main__":
    import sys
    reg = default_registry()
    g = Graph("demo")
    g.add("start", StartNode(topic="冰感内裤上新"), "check").add("check", ToolNode("sensitive_check", {"text": "$topic"}, out="hits"), "end").add("end", EndNode())
    state, trace = g.execute(ctx={"tools": reg})
    print(json.dumps(state, ensure_ascii=False))
    for t in trace:
        print(f"step{t['step']} {t['node']}({t['kind']}) -> {t['patch']}")
