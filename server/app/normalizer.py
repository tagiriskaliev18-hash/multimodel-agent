import re
import json
from typing import Dict, Any, List, Optional

class HermesStreamNormalizer:
    """
    Normalizes streaming output from Hermes and other reasoning/tool-calling models:
    - Extracts <scratchpad>...</scratchpad> and <thinking>...</thinking> into delta.reasoning
    - Extracts <tool_call>...</tool_call> into delta.tool_calls in standard OpenAI format
    - Leaves clean user-facing text in delta.content
    """
    def __init__(self, model_name: str = "hermes-3"):
        self.model_name = model_name
        self.buffer = ""
        self.in_reasoning = False
        self.in_tool_call = False
        self.tool_call_buffer = ""
        self.tool_call_id_counter = 0

    def process_delta(self, raw_delta: str) -> List[Dict[str, Any]]:
        """
        Receives raw string chunk, returns a list of normalized SSE delta chunks.
        """
        if not raw_delta:
            return []

        self.buffer += raw_delta
        emitted_chunks = []

        # Process buffer statefully
        while self.buffer:
            # 1. State: inside reasoning (<scratchpad> or <thinking>)
            if self.in_reasoning:
                close_match = re.search(r"</(scratchpad|thinking)>", self.buffer, re.IGNORECASE)
                if close_match:
                    reasoning_text = self.buffer[:close_match.start()]
                    if reasoning_text:
                        emitted_chunks.append(self._make_reasoning_chunk(reasoning_text))
                    self.buffer = self.buffer[close_match.end():]
                    self.in_reasoning = False
                else:
                    # Check if potential closing tag is partially forming at the end
                    tail_idx = max(self.buffer.rfind("</s"), self.buffer.rfind("</t"))
                    if tail_idx != -1 and tail_idx > len(self.buffer) - 15:
                        reasoning_text = self.buffer[:tail_idx]
                        self.buffer = self.buffer[tail_idx:]
                    else:
                        reasoning_text = self.buffer
                        self.buffer = ""
                    if reasoning_text:
                        emitted_chunks.append(self._make_reasoning_chunk(reasoning_text))
                continue

            # 2. State: inside tool call (<tool_call>)
            if self.in_tool_call:
                close_match = re.search(r"</tool_call>", self.buffer, re.IGNORECASE)
                if close_match:
                    self.tool_call_buffer += self.buffer[:close_match.start()]
                    self.buffer = self.buffer[close_match.end():]
                    self.in_tool_call = False

                    tool_chunk = self._parse_tool_call_payload(self.tool_call_buffer)
                    if tool_chunk:
                        emitted_chunks.append(tool_chunk)
                    self.tool_call_buffer = ""
                else:
                    tail_idx = self.buffer.rfind("</tool_")
                    if tail_idx != -1 and tail_idx > len(self.buffer) - 14:
                        self.tool_call_buffer += self.buffer[:tail_idx]
                        self.buffer = self.buffer[tail_idx:]
                    else:
                        self.tool_call_buffer += self.buffer
                        self.buffer = ""
                continue

            # 3. State: normal content - check for opening tags
            open_reason = re.search(r"<(scratchpad|thinking)>", self.buffer, re.IGNORECASE)
            open_tool = re.search(r"<tool_call>", self.buffer, re.IGNORECASE)

            # Find closest tag
            earliest_tag = None
            earliest_pos = 999999
            tag_type = None

            if open_reason and open_reason.start() < earliest_pos:
                earliest_pos = open_reason.start()
                earliest_tag = open_reason
                tag_type = "reasoning"

            if open_tool and open_tool.start() < earliest_pos:
                earliest_pos = open_tool.start()
                earliest_tag = open_tool
                tag_type = "tool"

            if earliest_tag:
                # Content before the tag
                before_content = self.buffer[:earliest_pos]
                if before_content:
                    emitted_chunks.append(self._make_content_chunk(before_content))

                self.buffer = self.buffer[earliest_tag.end():]
                if tag_type == "reasoning":
                    self.in_reasoning = True
                else:
                    self.in_tool_call = True
                    self.tool_call_buffer = ""
            else:
                # Check if potential opening tag is incomplete at end of buffer
                tail_open = max(self.buffer.rfind("<scrat"), self.buffer.rfind("<think"), self.buffer.rfind("<tool"))
                if tail_open != -1 and tail_open > len(self.buffer) - 15:
                    emit_text = self.buffer[:tail_open]
                    self.buffer = self.buffer[tail_open:]
                else:
                    emit_text = self.buffer
                    self.buffer = ""

                if emit_text:
                    emitted_chunks.append(self._make_content_chunk(emit_text))

        return emitted_chunks

    def finalize(self) -> List[Dict[str, Any]]:
        """Flush any remaining buffer at end of stream"""
        chunks = []
        if self.in_reasoning and self.buffer:
            chunks.append(self._make_reasoning_chunk(self.buffer))
            self.buffer = ""
        elif self.in_tool_call and (self.tool_call_buffer or self.buffer):
            full_tool = self.tool_call_buffer + self.buffer
            parsed = self._parse_tool_call_payload(full_tool)
            if parsed:
                chunks.append(parsed)
            self.tool_call_buffer = ""
            self.buffer = ""
        elif self.buffer:
            chunks.append(self._make_content_chunk(self.buffer))
            self.buffer = ""
        return chunks

    def _make_content_chunk(self, text: str) -> Dict[str, Any]:
        return {
            "choices": [{
                "index": 0,
                "delta": {"content": text},
                "finish_reason": None
            }],
            "model": self.model_name
        }

    def _make_reasoning_chunk(self, text: str) -> Dict[str, Any]:
        return {
            "choices": [{
                "index": 0,
                "delta": {"reasoning": text},
                "finish_reason": None
            }],
            "model": self.model_name
        }

    def _parse_tool_call_payload(self, text: str) -> Optional[Dict[str, Any]]:
        text = text.strip()
        self.tool_call_id_counter += 1
        call_id = f"call_hermes_{self.tool_call_id_counter}"
        func_name = "unknown_function"
        func_args = text

        try:
            parsed = json.loads(text)
            if isinstance(parsed, dict):
                func_name = parsed.get("name", parsed.get("tool", "function"))
                args = parsed.get("arguments", parsed.get("parameters", {}))
                func_args = json.dumps(args) if not isinstance(args, str) else args
        except Exception:
            pass

        return {
            "choices": [{
                "index": 0,
                "delta": {
                    "tool_calls": [{
                        "id": call_id,
                        "type": "function",
                        "function": {
                            "name": func_name,
                            "arguments": func_args
                        }
                    }]
                },
                "finish_reason": None
            }],
            "model": self.model_name
        }
