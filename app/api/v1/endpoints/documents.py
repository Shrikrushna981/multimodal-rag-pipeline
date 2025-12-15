from fastapi import APIRouter, HTTPException
from app.db.vector_store_client import QdrantVectorStore

router = APIRouter()

@router.get("/documents")
async def list_documents():
    """
    List unique documents stored in the vector database.
    Since Qdrant is a vector store, we scroll and aggregate unique filenames.
    This is inefficient for large datasets but fine for a demo.
    """
    try:
        store = QdrantVectorStore()
        # Scroll through points (limit 1000 for demo)
        res, _ = store.client.scroll(
            collection_name="rag_collection",
            limit=1000,
            with_payload=True,
            with_vectors=False
        )
        
        # DEBUG LOGGING
        print(f"DEBUG: Found {len(res)} points in scroll.")
        if len(res) > 0:
            print(f"DEBUG: Sample Payload: {res[0].payload}")

        # Aggregate by filename
        docs = {}
        for point in res:
            payload = point.payload or {}
            # Check for source_filename and also 'source' (legacy?)
            filename = payload.get("source_filename") or payload.get("source") or "Unknown"
            
            if filename not in docs:
                docs[filename] = {
                    "filename": filename,
                    "type": payload.get("mime_type", "unknown"),
                    "category": payload.get("category", "Uncategorized"),
                    "chunks": 0
                }
            docs[filename]["chunks"] += 1
            
        print(f"DEBUG: Aggregated docs: {list(docs.keys())}")
        return {"documents": list(docs.values())}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/delete")
async def delete_document(filename: str):
    """
    Delete all chunks associated with a filename.
    """
    try:
        store = QdrantVectorStore()
        from qdrant_client.http import models as rest
        
        # Delete by filter
        store.client.delete(
            collection_name="rag_collection",
            points_selector=rest.FilterSelector(
                filter=rest.Filter(
                    must=[
                        rest.FieldCondition(
                            key="source_filename",
                            match=rest.MatchValue(value=filename)
                        )
                    ]
                )
            )
        )
        return {"status": "success", "deleted": filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from pydantic import BaseModel
from typing import List

class UpdateCategoryRequest(BaseModel):
    filenames: List[str]
    category: str

@router.patch("/update_category")
async def update_doc_category(req: UpdateCategoryRequest):
    """
    Batch update category for multiple documents.
    """
    try:
        store = QdrantVectorStore()
        from qdrant_client.http import models as rest
        
        # Update payload for all matching documents
        store.client.set_payload(
            collection_name="rag_collection",
            payload={"category": req.category},
            points=rest.FilterSelector(
                filter=rest.Filter(
                    must=[
                        rest.FieldCondition(
                            key="source_filename",
                            match=rest.MatchAny(any=req.filenames)
                        )
                    ]
                )
            )
        )
        return {"status": "success", "updated": len(req.filenames)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/category")
async def delete_category(category: str):
    """
    Delete all documents in a specific category.
    """
    try:
        store = QdrantVectorStore()
        from qdrant_client.http import models as rest
        
        store.client.delete(
            collection_name="rag_collection",
            points_selector=rest.FilterSelector(
                filter=rest.Filter(
                    must=[
                        rest.FieldCondition(
                            key="category",
                            match=rest.MatchValue(value=category)
                        )
                    ]
                )
            )
        )
        return {"status": "success", "deleted_category": category}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
