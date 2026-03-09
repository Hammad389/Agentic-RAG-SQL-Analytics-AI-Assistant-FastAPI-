from enum import Enum


class SenderType(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class FallbackReason(str, Enum):
    NOT_ENGLISH = "not_english"
    LOW_SIGNAL = "low_signal"
    EMPTY_MESSAGE = "empty_message"
    ILLEGAL_INPUT = "illegal_input"
    GREETING = "greeting"


class FallbackMessage(str, Enum):
    NOT_ENGLISH = ("not_english", "Sorry! I can only understand English queries at the moment.")
    LOW_SIGNAL = ("low_signal", "Sorry! I couldn't clearly understand your request. Please provide more details.")
    EMPTY_MESSAGE = ("empty_message", "It looks like your message was empty. Please enter a question.")
    ILLEGAL_INPUT = ("illegal_input", "Sorry! Your request contains unsupported or invalid input.")
    GREETING = (
        "greeting",
        "Hi! I am Agentic AI Assistant. I can help you with Analytics, Navigation, and general help about the platform.",
    )

    def __new__(cls, value, message):
        obj = str.__new__(cls, value)
        obj._value_ = value
        obj.message = message
        return obj
