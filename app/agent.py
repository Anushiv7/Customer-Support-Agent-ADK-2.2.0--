# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from typing import Literal, TypedDict, Any
from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.genai import types
from google.adk.workflow import Workflow, Edge, FunctionNode, START

import os
import google.auth

_, project_id = google.auth.default()
os.environ["GOOGLE_CLOUD_PROJECT"] = project_id
os.environ["GOOGLE_CLOUD_LOCATION"] = "global"
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"


class SupportState(TypedDict):
    user_query: str
    classification: Literal["shipping", "unrelated"]
    response: str


def classifier_node_func(state: SupportState) -> SupportState:
    # Use LLM to classify query
    # Stub: simplified logic for now
    query = state["user_query"].lower()
    if any(
        word in query
        for word in ["rates", "tracking", "delivery", "returns", "shipping"]
    ):
        state["classification"] = "shipping"
    else:
        state["classification"] = "unrelated"
    return state


def shipping_faq_node_func(state: SupportState) -> SupportState:
    state["response"] = (
        "Our shipping FAQ covers rates, tracking, and returns. Please check our website for details."
    )
    return state


def decline_node_func(state: SupportState) -> SupportState:
    state["response"] = (
        "I am sorry, I can only assist with shipping-related queries for our shipping company."
    )
    return state


# Define Nodes
classifier = FunctionNode(func=classifier_node_func, name="classifier")
shipping_faq = FunctionNode(func=shipping_faq_node_func, name="shipping_faq")
decline = FunctionNode(func=decline_node_func, name="decline")

# Define Workflow using verified signatures
# 'nodes' argument removed as it's not supported by Workflow constructor
workflow = Workflow(
    name="support_workflow",
    edges=[
        Edge(from_node=START, to_node=classifier),
        Edge(from_node=classifier, to_node=shipping_faq, route="shipping"),
        Edge(from_node=classifier, to_node=decline, route="unrelated"),
    ],
)

# Workflow is a BaseNode, so it might need to be wrapped or treated specially in the Agent.
# Agent is an LLM agent, but based on the class inspection, it has a `_llm_flow`
# Maybe the Agent is intended to be used with an LlmAgent that delegates to a Workflow?

# Let's try wrapping the workflow in an Agent, or check if the workflow can run.

root_agent = Agent(
    name="customer_support_agent",
    model=Gemini(
        model="gemini-flash-latest",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction="You are a polite customer support representative for a shipping company.",
    # If the Agent class doesn't accept 'workflow', how do I run the workflow?
    # Maybe I shouldn't be defining a root_agent if I want to run a workflow?
)

app = App(
    root_agent=root_agent,
    name="app",
)
