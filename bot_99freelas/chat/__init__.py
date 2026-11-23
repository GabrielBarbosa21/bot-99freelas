"""Módulo de conversação e chat inteligente."""
from .models import MessageIntent, ChatMessage, IntentAnalysis
from .classifier import IntentClassifier
from .responder import ChatResponder

__all__ = ["MessageIntent", "ChatMessage", "IntentAnalysis", "IntentClassifier", "ChatResponder"]
