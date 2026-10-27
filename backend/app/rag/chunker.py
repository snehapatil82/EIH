from typing import List, Dict, Any, Optional

class CodeAwareChunker:
    """
    Splits source code and documentation into semantically meaningful chunks
    preserving file paths, language, and exact line number ranges (start_line, end_line).
    """
    def __init__(self, target_chunk_lines: int = 50, overlap_lines: int = 10):
        self.target_chunk_lines = target_chunk_lines
        self.overlap_lines = overlap_lines

    def chunk_file(self, file_path: str, content: str, language: Optional[str] = None, entities: Optional[List[Dict]] = None) -> List[Dict[str, Any]]:
        chunks: List[Dict[str, Any]] = []
        lines = content.splitlines()
        total_lines = len(lines)

        if total_lines == 0:
            return []

        # If entities (classes/functions) are provided and cover parts of the file, create entity chunks
        if entities and language == "Python":
            # Sort entities by start_line
            sorted_entities = sorted(entities, key=lambda x: x.get("start_line", 0))
            for ent in sorted_entities:
                s_line = max(1, ent["start_line"])
                e_line = min(total_lines, ent["end_line"])
                chunk_text = "\n".join(lines[s_line - 1:e_line])
                
                if chunk_text.strip():
                    chunks.append({
                        "file_path": file_path,
                        "start_line": s_line,
                        "end_line": e_line,
                        "content": chunk_text,
                        "entity_name": ent.get("name"),
                        "entity_type": ent.get("entity_type"),
                        "language": language or "text"
                    })

        # If no entities or file has remaining portions, use sliding window over the full file
        # Also ensures full coverage for non-Python or files without parsed entities
        if not chunks or len(chunks) < 2:
            chunks = []
            curr_line = 0
            while curr_line < total_lines:
                end_line = min(total_lines, curr_line + self.target_chunk_lines)
                chunk_text = "\n".join(lines[curr_line:end_line])

                if chunk_text.strip():
                    chunks.append({
                        "file_path": file_path,
                        "start_line": curr_line + 1,
                        "end_line": end_line,
                        "content": chunk_text,
                        "entity_name": None,
                        "entity_type": "file_chunk",
                        "language": language or "text"
                    })

                if end_line >= total_lines:
                    break
                curr_line += (self.target_chunk_lines - self.overlap_lines)

        return chunks
