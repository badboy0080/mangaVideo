"""AgentScope-based agent wrappers for the manga pipeline steps.

多智能体协作体系（v3）：
- DirectorAgent：创意总监，流水线启动前分析需求输出创意指导
- ReviewerAgent：质量审核员，对 Step2/3/4 产出进行全流程质量把关
- PipelineOrchestrator：统一编排 5 步执行、条件分支、并发、审核
- middleware 模块：Hook 监控（日志、进度、停止检查）
"""

from agents.research_agent import ResearchAgent
from agents.storyboard_agent import StoryboardAgent
from agents.image_gen_agent import ImageGenAgent
from agents.video_gen_agent import VideoGenAgent
from agents.concat_agent import ConcatAgent
from agents.cover_agent import CoverAgent
from agents.director_agent import DirectorAgent
from agents.reviewer_agent import ReviewerAgent
from agents.pipeline import PipelineOrchestrator

__all__ = [
    "ResearchAgent",
    "StoryboardAgent",
    "ImageGenAgent",
    "VideoGenAgent",
    "ConcatAgent",
    "CoverAgent",
    "DirectorAgent",
    "ReviewerAgent",
    "PipelineOrchestrator",
]
