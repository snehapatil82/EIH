from typing import List, Dict, Any

class CitationBuilder:
    @staticmethod
    def build_citations(retrieved_chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Formats retrieved repository chunks into standardized citations
        with verified file paths, line ranges, and snippet previews.
        """
        citations = []
        seen = set()

        for chunk in retrieved_chunks:
            file_path = chunk.get("file_path", "unknown")
            start_line = chunk.get("start_line")
            end_line = chunk.get("end_line")
            key = f"{file_path}:{start_line}-{end_line}"

            if key in seen:
                continue
            seen.add(key)

            # Extract a concise representative snippet (max 10 lines)
            content_lines = chunk.get("content", "").splitlines()
            preview = "\n".join(content_lines[:10])
            if len(content_lines) > 10:
                preview += f"\n... ({len(content_lines) - 10} more lines)"

            citations.append({
                "file_path": file_path,
                "start_line": start_line,
                "end_line": end_line,
                "snippet": preview,
                "score": chunk.get("score")
            })

        return citations
