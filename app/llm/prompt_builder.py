from typing import List
from app.memory.manager import ChatMessage, Role
from app.retrieval.models import SearchResult

class PromptBuilder:
    def __init__(self, context_window: int = 4096):
        self.context_window = context_window
        self.system_template = """You are a helpful expert assistant in a Multimodal RAG system.
Answer the user's question based ONLY on the following context documents.
If the answer is not in the context, say "I don't have enough information to answer that."
Always cite your sources using [Source: filename].

Context:
{context_str}
"""

    def build_prompt(self, query: str, history: List[ChatMessage], retrieval_results: List[SearchResult]) -> List[ChatMessage]:
        # 1. Format Context
        context_str = ""
        for res in retrieval_results:
            source = res.metadata.get('source_filename', 'Unknown')
            page = res.metadata.get('page_number', '')
            timestamp = f"{res.metadata.get('timestamp_start', '')}-{res.metadata.get('timestamp_end', '')}" if 'timestamp_start' in res.metadata else ''
            
            ref = f"{source}"
            if page: ref += f" p.{page}"
            if timestamp: ref += f" ({timestamp}s)"
            
            context_str += f"---\nSource: {ref}\nContent: {res.content}\n"

        # 2. Build System Message
        system_content = self.system_template.format(context_str=context_str)
        
        messages = [
            ChatMessage(role=Role.SYSTEM, content=system_content)
        ]

        # 3. Add History (Simulate sliding window - simplistic for now)
        # We assume strict token counting is done elsewhere or we trust the model context for demo
        # A real implementation would count tokens here.
        # We'll take last 5 turns.
        for msg in history[-10:]: 
            messages.append(msg)

        # 4. Add Current Query
        messages.append(ChatMessage(role=Role.USER, content=query))

        return messages
