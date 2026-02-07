"""
Sample conversation data for testing.
Provides realistic conversation examples for different signal levels.
"""

# High-signal conversation about product decisions
HIGH_SIGNAL_CONVERSATION = [
    {
        "text": "I've been thinking about our pricing strategy. Should we go freemium or paid-only?",
        "user": "U001",
        "channel_id": "C001",
        "ts": "1234567890.001"
    },
    {
        "text": "The data is interesting - 60% of free users never upgrade. But here's what surprised me: 100% of our word-of-mouth growth comes from free users.",
        "user": "U002",
        "channel_id": "C001",
        "ts": "1234567890.002"
    },
    {
        "text": "That's a great point. What if we keep freemium but add usage caps? That way we're not subsidizing power users who never pay.",
        "user": "U001",
        "channel_id": "C001",
        "ts": "1234567890.003"
    },
    {
        "text": "I like that. We could also add a 'powered by' badge for free users to drive more viral growth. Let's prototype this next sprint.",
        "user": "U002",
        "channel_id": "C001",
        "ts": "1234567890.004"
    },
    {
        "text": "Agreed. The key insight here is: don't just look at conversion funnels, look at acquisition loops. Free users are our growth engine.",
        "user": "U001",
        "channel_id": "C001",
        "ts": "1234567890.005"
    }
]

# Low-signal conversation with scheduling talk
LOW_SIGNAL_CONVERSATION = [
    {
        "text": "Hey, can we schedule a call for tomorrow?",
        "user": "U001",
        "channel_id": "C002",
        "ts": "1234567890.001"
    },
    {
        "text": "Sure, what time works for you?",
        "user": "U002",
        "channel_id": "C002",
        "ts": "1234567890.002"
    },
    {
        "text": "How about 3pm?",
        "user": "U001",
        "channel_id": "C002",
        "ts": "1234567890.003"
    },
    {
        "text": "Works for me. I'll send a calendar invite.",
        "user": "U002",
        "channel_id": "C002",
        "ts": "1234567890.004"
    },
    {
        "text": "Cool, thanks!",
        "user": "U001",
        "channel_id": "C002",
        "ts": "1234567890.005"
    }
]

# Medium-signal conversation with technical discussion
MEDIUM_SIGNAL_CONVERSATION = [
    {
        "text": "We just spent 3 hours debugging the API integration. Turns out it was a missing comma in the JSON payload.",
        "user": "U001",
        "channel_id": "C003",
        "ts": "1234567890.001"
    },
    {
        "text": "Ugh, those are the worst. Did you add better error handling?",
        "user": "U002",
        "channel_id": "C003",
        "ts": "1234567890.002"
    },
    {
        "text": "Yeah, now we validate the JSON schema before sending. Should catch these issues earlier.",
        "user": "U001",
        "channel_id": "C003",
        "ts": "1234567890.003"
    },
    {
        "text": "Nice. We should document this in the engineering wiki.",
        "user": "U002",
        "channel_id": "C003",
        "ts": "1234567890.004"
    }
]

# Short conversation (below minimum threshold)
SHORT_CONVERSATION = [
    {
        "text": "Hey",
        "user": "U001",
        "channel_id": "C004",
        "ts": "1234567890.001"
    },
    {
        "text": "What's up?",
        "user": "U002",
        "channel_id": "C004",
        "ts": "1234567890.002"
    }
]

# Conversation with code blocks
CODE_HEAVY_CONVERSATION = [
    {
        "text": "Check out this function:\n```python\ndef process_data(data):\n    return data.strip()\n```",
        "user": "U001",
        "channel_id": "C005",
        "ts": "1234567890.001"
    },
    {
        "text": "```python\ndef better_process(data):\n    return data.strip().lower()\n```",
        "user": "U002",
        "channel_id": "C005",
        "ts": "1234567890.002"
    }
]
