#!/usr/bin/env python3
"""
Documentation & Help Router
Handles user guide, API docs, processor guide, help search, and help index endpoints.
Extracted from monolithic main.py for better modularity.
"""

from fastapi import APIRouter, HTTPException, Query
import logging
import markdown
from pathlib import Path
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)

# Docs directory (project root / docs)
DOCS_DIR = Path(__file__).resolve().parent.parent.parent.parent / "docs"

# Create router instance
router = APIRouter(prefix="/api/docs", tags=["Documentation"])


@router.get("/user-guide")
async def get_user_guide():
    """Get user guide documentation in HTML format."""
    try:
        docs_path = DOCS_DIR / "user-guide.md"

        if not docs_path.exists():
            raise HTTPException(status_code=404, detail="User guide not found")

        with open(docs_path, 'r', encoding='utf-8') as f:
            markdown_content = f.read()

        # Convert markdown to HTML
        html_content = markdown.markdown(
            markdown_content,
            extensions=['toc', 'tables', 'fenced_code']
        )

        return {
            "title": "Catalynx User Guide",
            "content": html_content,
            "format": "html",
            "last_updated": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to serve user guide: {e}")
        raise HTTPException(status_code=500, detail="Failed to load user guide")


@router.get("/api-documentation")
async def get_api_documentation():
    """Get API documentation in HTML format."""
    try:
        docs_path = DOCS_DIR / "api-documentation.md"

        if not docs_path.exists():
            raise HTTPException(status_code=404, detail="API documentation not found")

        with open(docs_path, 'r', encoding='utf-8') as f:
            markdown_content = f.read()

        # Convert markdown to HTML
        html_content = markdown.markdown(
            markdown_content,
            extensions=['toc', 'tables', 'fenced_code', 'codehilite']
        )

        return {
            "title": "Catalynx API Documentation",
            "content": html_content,
            "format": "html",
            "last_updated": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to serve API documentation: {e}")
        raise HTTPException(status_code=500, detail="Failed to load API documentation")


@router.get("/processor-guide")
async def get_processor_guide():
    """Get processor guide documentation in HTML format."""
    try:
        docs_path = DOCS_DIR / "processor-guide.md"

        if not docs_path.exists():
            raise HTTPException(status_code=404, detail="Processor guide not found")

        with open(docs_path, 'r', encoding='utf-8') as f:
            markdown_content = f.read()

        # Convert markdown to HTML
        html_content = markdown.markdown(
            markdown_content,
            extensions=['toc', 'tables', 'fenced_code']
        )

        return {
            "title": "Catalynx Processor Guide",
            "content": html_content,
            "format": "html",
            "last_updated": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to serve processor guide: {e}")
        raise HTTPException(status_code=500, detail="Failed to load processor guide")


@router.get("/help-search")
async def search_help_documentation(q: str = Query(..., min_length=2)):
    """Search across all help documentation."""
    try:
        search_results = []

        # Files to search
        help_files = [
            ("user-guide.md", "User Guide"),
            ("api-documentation.md", "API Documentation"),
            ("processor-guide.md", "Processor Guide")
        ]

        search_term = q.lower()

        for filename, title in help_files:
            file_path = DOCS_DIR / filename
            if file_path.exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                    # Simple search implementation
                    lines = content.split('\n')
                    matches = []

                    for i, line in enumerate(lines):
                        if search_term in line.lower():
                            # Get context around the match
                            start = max(0, i-2)
                            end = min(len(lines), i+3)
                            context = '\n'.join(lines[start:end])

                            matches.append({
                                "line_number": i+1,
                                "line": line.strip(),
                                "context": context,
                                "relevance": line.lower().count(search_term)
                            })

                    if matches:
                        # Sort by relevance (number of matches in line)
                        matches.sort(key=lambda x: x['relevance'], reverse=True)

                        search_results.append({
                            "document": title,
                            "file": filename,
                            "matches": matches[:5],  # Top 5 matches per document
                            "total_matches": len(matches)
                        })

                except Exception as e:
                    logger.warning(f"Error searching {filename}: {e}")

        return {
            "query": q,
            "results": search_results,
            "total_documents": len(search_results),
            "total_matches": sum(r["total_matches"] for r in search_results)
        }

    except Exception as e:
        logger.error(f"Help search failed: {e}")
        raise HTTPException(status_code=500, detail="Help search failed")


@router.get("/help-index")
async def get_help_index():
    """Get index of all available help documentation."""
    try:
        help_index = []

        # Main documentation files
        main_docs = [
            {
                "id": "user-guide",
                "title": "User Guide",
                "description": "Comprehensive guide to using Catalynx platform features",
                "file": "user-guide.md",
                "endpoint": "/api/docs/user-guide",
                "category": "User Documentation"
            },
            {
                "id": "api-documentation",
                "title": "API Documentation",
                "description": "Complete API reference with endpoints and examples",
                "file": "api-documentation.md",
                "endpoint": "/api/docs/api-documentation",
                "category": "Technical Documentation"
            },
            {
                "id": "processor-guide",
                "title": "Processor Guide",
                "description": "Detailed guide to all 18 processors and their capabilities",
                "file": "processor-guide.md",
                "endpoint": "/api/docs/processor-guide",
                "category": "Technical Documentation"
            }
        ]

        # Check which files actually exist and get metadata
        for doc in main_docs:
            file_path = DOCS_DIR / doc["file"]
            if file_path.exists():
                stat = file_path.stat()
                doc.update({
                    "exists": True,
                    "size_bytes": stat.st_size,
                    "last_modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                })

                # Get first few lines for preview
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()[:10]
                        doc["preview"] = ''.join(lines).strip()[:200] + "..."
                except:
                    doc["preview"] = "Preview not available"

                help_index.append(doc)
            else:
                doc.update({
                    "exists": False,
                    "preview": "File not found"
                })
                help_index.append(doc)

        return {
            "available_docs": help_index,
            "categories": list(set(doc["category"] for doc in help_index)),
            "search_endpoint": "/api/docs/help-search",
            "last_updated": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to generate help index: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate help index")
