import os
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings
from backend.config import settings

DOC_DEPT_MAPPING = {
    "general_medicine.txt": "GEN_MED",
    "orthopaedics.txt": "ORTHO",
    "ent.txt": "ENT",
    "cardiology.txt": "CARDIO",
    "dermatology.txt": "DERM",
    "gastroenterology.txt": "GASTRO",
    "neurology.txt": "NEURO",
    "ophthalmology.txt": "OPHTH",
    "paediatrics.txt": "PAED",
    "gynaecology.txt": "GYNAE",
    "emergency.txt": "EMERG",
    "general_registration.txt": "GENERAL"
}

class HospitalRAGRetriever:
    """
    RAG Ingestion and Semantic Retrieval Engine for Hospital Intake.
    Uses ChromaDB with local embeddings, semantic search, and grounded fallback.
    """

    def __init__(self, persist_dir: Optional[str] = None, docs_dir: Optional[str] = None):
        self.persist_dir = persist_dir or settings.CHROMA_PERSIST_DIR
        self.docs_dir = Path(docs_dir or settings.DOCUMENTS_DIR)
        Path(self.persist_dir).mkdir(parents=True, exist_ok=True)

        self.client = chromadb.PersistentClient(path=self.persist_dir)
        self.collection_name = "hospital_documents"
        self.collection = self._get_or_create_collection()

    def _get_or_create_collection(self):
        """Retrieves or creates ChromaDB collection."""
        try:
            return self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"description": "Hospital intake instructions and department policies"}
            )
        except Exception as e:
            print(f"[RAG WARNING] Failed getting Chroma collection, recreating: {e}")
            return self.client.create_collection(name=self.collection_name)

    def load_and_index_documents(self, force_reload: bool = False) -> int:
        """
        Loads all hospital .txt documents, parses sections into chunks, and indexes into ChromaDB.
        """
        if not force_reload and self.collection.count() > 0:
            print(f"[RAG] Collection already contains {self.collection.count()} chunks. Skipping reload.")
            return self.collection.count()

        if force_reload and self.collection.count() > 0:
            # Clear existing entries
            try:
                self.client.delete_collection(self.collection_name)
                self.collection = self.client.create_collection(self.collection_name)
            except Exception as e:
                print(f"[RAG] Error resetting collection: {e}")

        all_docs = list(self.docs_dir.glob("*.txt"))
        if not all_docs:
            print(f"[RAG WARNING] No hospital text documents found in {self.docs_dir}")
            return 0

        chunks_to_add = []
        metadatas = []
        ids = []

        for doc_path in all_docs:
            filename = doc_path.name
            dept_code = DOC_DEPT_MAPPING.get(filename, "GENERAL")
            try:
                content = doc_path.read_text(encoding="utf-8")
            except Exception as e:
                print(f"[RAG ERROR] Reading {filename}: {e}")
                continue

            # Parse document into logical sections
            parsed_sections = self._split_document_by_sections(content, filename)
            for idx, sec in enumerate(parsed_sections):
                chunk_id = f"{filename}_{idx}"
                chunks_to_add.append(sec["text"])
                metadatas.append({
                    "document_name": filename,
                    "department_code": dept_code,
                    "section_title": sec["title"],
                    "chunk_index": idx
                })
                ids.append(chunk_id)

        if chunks_to_add:
            # Batch upsert into ChromaDB
            batch_size = 50
            for i in range(0, len(chunks_to_add), batch_size):
                self.collection.upsert(
                    documents=chunks_to_add[i:i + batch_size],
                    metadatas=metadatas[i:i + batch_size],
                    ids=ids[i:i + batch_size]
                )
            print(f"[RAG] Successfully indexed {len(chunks_to_add)} grounded chunks into ChromaDB.")

        return self.collection.count()

    def _split_document_by_sections(self, content: str, filename: str) -> List[Dict[str, str]]:
        """
        Splits a hospital policy document by numbered headings or major paragraphs.
        """
        lines = content.split("\n")
        sections = []
        current_title = "Overview & Header"
        current_lines = []

        header_pattern = re.compile(r"^(?:\[.*\]|\d+\.\s+[A-Za-z0-9\s,&/\-]+|Department:|Location:)")

        for line in lines:
            trimmed = line.strip()
            if not trimmed:
                continue

            # Check if this line marks a section header
            if re.match(r"^\d+\.\s+([A-Za-z0-9\s,&/\-]+)", trimmed):
                if current_lines:
                    sections.append({
                        "title": current_title,
                        "text": f"[{filename} - {current_title}]\n" + "\n".join(current_lines)
                    })
                    current_lines = []
                current_title = trimmed
                current_lines.append(trimmed)
            else:
                current_lines.append(trimmed)

        if current_lines:
            sections.append({
                "title": current_title,
                "text": f"[{filename} - {current_title}]\n" + "\n".join(current_lines)
            })

        return sections

    def query(
        self,
        query_text: str,
        department_code: Optional[str] = None,
        top_k: int = 4
    ) -> List[Dict[str, Any]]:
        """
        Executes semantic retrieval with metadata filtering and graceful fallback.
        """
        results = []
        where_filter = None

        if department_code and department_code != "ALL":
            # Target both department-specific documents and general registration
            where_filter = {
                "$or": [
                    {"department_code": department_code},
                    {"department_code": "GENERAL"}
                ]
            }

        try:
            query_kwargs = {
                "query_texts": [query_text],
                "n_results": top_k
            }
            if where_filter and self.collection.count() > 0:
                query_kwargs["where"] = where_filter

            res = self.collection.query(**query_kwargs)

            if res and res.get("documents") and res["documents"][0]:
                for doc_text, meta, dist, cid in zip(
                    res["documents"][0],
                    res["metadatas"][0],
                    res["distances"][0] if "distances" in res and res["distances"] else [0.0] * len(res["documents"][0]),
                    res["ids"][0]
                ):
                    results.append({
                        "chunk_id": cid,
                        "document_name": meta.get("document_name", "Unknown"),
                        "department_code": meta.get("department_code", "GEN_MED"),
                        "section_title": meta.get("section_title", "Intake Guide"),
                        "content": doc_text,
                        "distance": dist,
                        "relevance_score": max(0.0, round(1.0 - (dist / 2.0), 3)) if dist else 0.85
                    })

        except Exception as e:
            print(f"[RAG SEARCH WARNING] ChromaDB query error, executing fallback: {e}")

        # Fallback mechanism if no results or ChromaDB failed
        if not results:
            results = self._fallback_keyword_search(query_text, department_code, top_k)

        return results

    def _fallback_keyword_search(
        self,
        query_text: str,
        department_code: Optional[str],
        top_k: int
    ) -> List[Dict[str, Any]]:
        """Fallback grounded search reading local text documents directly."""
        fallback_results = []
        doc_filename = None

        # Find matching document filename
        for fname, code in DOC_DEPT_MAPPING.items():
            if code == department_code:
                doc_filename = fname
                break

        files_to_check = [doc_filename] if doc_filename else ["general_registration.txt", "general_medicine.txt"]

        for fname in files_to_check:
            if not fname:
                continue
            path = self.docs_dir / fname
            if path.exists():
                text = path.read_text(encoding="utf-8")
                sections = self._split_document_by_sections(text, fname)
                for s in sections[:top_k]:
                    fallback_results.append({
                        "chunk_id": f"fallback_{fname}",
                        "document_name": fname,
                        "department_code": department_code or "GENERAL",
                        "section_title": s["title"],
                        "content": s["text"],
                        "relevance_score": 0.80,
                        "is_fallback": True
                    })

        return fallback_results

# Global singleton retriever instance
rag_retriever = HospitalRAGRetriever()
