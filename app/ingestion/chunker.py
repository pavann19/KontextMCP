"""Legal-aware hierarchical document chunker (P6.2).

Splits legal regulatory documents along semantic boundaries (Articles, Annex sections,
paragraphs, and sub-clauses) while prepending contextual breadcrumbs and maintaining
structured metadata.
"""

import re
from typing import Dict, List, Any
from pydantic import BaseModel, Field

class LegalChunk(BaseModel):
    chunk_id: str
    doc_id: str
    language: str
    article_id: str
    title: str
    chapter: str
    section: str = ""
    text: str
    context_header: str
    full_content: str  # context_header + text
    keywords: List[str] = Field(default_factory=list)
    token_count: int
    char_length: int

class LegalDocumentChunker:
    """Specialized chunker for EU regulatory texts."""
    
    def __init__(self, max_tokens: int = 350, overlap_tokens: int = 40):
        self.max_tokens = max_tokens
        self.overlap_tokens = overlap_tokens

    def estimate_tokens(self, text: str) -> int:
        """Heuristic token count estimation (~4 chars per token)."""
        words = text.split()
        return max(len(words), int(len(text) / 4))

    def _split_into_clauses(self, text: str, language: str) -> List[str]:
        """Splits article text into logical paragraph or lettered clause units."""
        lines = text.split("\n")
        title_line = lines[0] if lines else ""
        content_lines = lines[1:] if len(lines) > 1 else lines
        
        # Group lines by paragraphs or major subclauses (e.g. 1., 2., (a), a))
        blocks: List[str] = []
        current_block: List[str] = []
        
        # Regex patterns for numbered paragraphs or sub-clauses
        clause_pattern = re.compile(r"^(\d+\.|\([a-z]\)|[a-z]\))\s+")
        
        for line in content_lines:
            line_str = line.strip()
            if not line_str:
                continue
                
            if clause_pattern.match(line_str) and current_block:
                blocks.append("\n".join(current_block))
                current_block = [line_str]
            else:
                current_block.append(line_str)
                
        if current_block:
            blocks.append("\n".join(current_block))
            
        return blocks if blocks else [text]

    def chunk_document(self, doc: Dict[str, Any]) -> List[LegalChunk]:
        """Chunks a single document into legal chunks with breadcrumb headers."""
        doc_id = doc.get("doc_id", "doc_unknown")
        language = doc.get("language", "en")
        article_id = doc.get("article_id", "General")
        title = doc.get("title", "")
        chapter = doc.get("chapter", "")
        raw_text = doc.get("text", "")
        keywords = doc.get("keywords", [])
        
        original_clauses = self._split_into_clauses(raw_text, language)
        clauses = []
        budget = max(128, self.max_tokens * 4 - 240)
        for clause in original_clauses:
            if len(clause) <= budget:
                clauses.append(clause)
                continue
            # Oversized statutory clauses need bounded, contiguous word slices.
            start = 0
            while len(clause) - start > budget:
                end = clause.rfind(" ", start, start + budget)
                if end <= start:
                    end = start + budget
                clauses.append(clause[start:end].strip())
                start = end
                while start < len(clause) and clause[start].isspace():
                    start += 1
            if clause[start:].strip():
                clauses.append(clause[start:].strip())
        chunks: List[LegalChunk] = []
        
        # Build contextual breadcrumb prefix
        prefix_tag = "EU AI ACT" if language == "en" else "KI-VERORDNUNG"
        
        current_units: List[str] = []
        current_token_count = 0
        part_idx = 1
        
        for clause in clauses:
            clause_tokens = self.estimate_tokens(clause)
            
            # If adding this clause exceeds max_tokens and we already have content, flush
            if current_token_count + clause_tokens > self.max_tokens and current_units:
                chunk_body = "\n".join(current_units)
                context_header = f"[{prefix_tag} | {chapter} | {article_id}: {title} (Part {part_idx})]"
                full_content = f"{context_header}\n{chunk_body}"
                
                chunk = LegalChunk(
                    chunk_id=f"{doc_id}_p{part_idx}",
                    doc_id=doc_id,
                    language=language,
                    article_id=article_id,
                    title=title,
                    chapter=chapter,
                    section=f"Part {part_idx}",
                    text=chunk_body,
                    context_header=context_header,
                    full_content=full_content,
                    keywords=keywords,
                    token_count=self.estimate_tokens(full_content),
                    char_length=len(full_content)
                )
                chunks.append(chunk)
                part_idx += 1
                current_units = [clause]
                current_token_count = clause_tokens
            else:
                current_units.append(clause)
                current_token_count += clause_tokens
                
        if current_units:
            chunk_body = "\n".join(current_units)
            section_label = f"Part {part_idx}" if part_idx > 1 else "Complete"
            context_header = f"[{prefix_tag} | {chapter} | {article_id}: {title}]"
            full_content = f"{context_header}\n{chunk_body}"
            
            chunk = LegalChunk(
                chunk_id=f"{doc_id}_p{part_idx}",
                doc_id=doc_id,
                language=language,
                article_id=article_id,
                title=title,
                chapter=chapter,
                section=section_label,
                text=chunk_body,
                context_header=context_header,
                full_content=full_content,
                keywords=keywords,
                token_count=self.estimate_tokens(full_content),
                char_length=len(full_content)
            )
            chunks.append(chunk)
            
        return chunks

    def chunk_all(self, docs: List[Dict[str, Any]]) -> List[LegalChunk]:
        """Chunks a collection of documents."""
        all_chunks: List[LegalChunk] = []
        for doc in docs:
            all_chunks.extend(self.chunk_document(doc))
        return all_chunks

