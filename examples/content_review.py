#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""示例：内容审核工作流 生成 → 敏感词检查 → 条件路由 → 人工确认/改写 → 发布。"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from workflow_engine import Graph, StartNode, ToolNode, LLMNode, HumanConfirmNode, EndNode, ConditionalRouter, default_registry

g = Graph("content_review")
g.add("start", StartNode(topic="全网最强冰感内裤，国家级舒适体验"), "gen") \
  .add("gen", LLMNode(out="copy", system="你是电商文案",
    template="为{topic}写一条30字内的带货文案"), "check") \
  .add("check", ToolNode("sensitive_check", {"text": "$copy"}, out="hits"), "route") \
  .add("route", ConditionalRouter("hits", {"!=[]": "human", "==[]": "publish"}, default="publish")) \
  .add("human", HumanConfirmNode("文案命中敏感词，是否人工改写后发布？", out="confirmed"), "publish") \
  .add("publish", EndNode())

state, trace = g.execute(ctx={"tools": default_registry(), "auto_approve": False})
print("最终状态:", json.dumps(state, ensure_ascii=False))
print("执行轨迹:")
for t in trace:
    print(f"  step{t['step']} {t['node']}({t['kind']}) {t['patch']}")
