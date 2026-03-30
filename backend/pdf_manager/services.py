import tabula
import pandas as pd
from typing import List, Dict, Any
from .models import PDFDocument

def extract_tables_from_pdf(pdf_id: int, pages: str = "all") -> List[Dict[str, Any]]:
    """
    Extracts tables from a PDF document using tabula-py and returns them as a list of dictionaries.
    """
    pdf_doc = PDFDocument.objects.get(pk=pdf_id)
    if not pdf_doc.file:
        return []

    # Use tabula to read the PDF
    # tabula.read_pdf returns a list of DataFrames
    dfs = tabula.read_pdf(pdf_doc.file.path, pages=pages, multiple_tables=True)
    
    results = []
    for i, df in enumerate(dfs):
        # Convert DataFrame to a list of records (dictionaries)
        table_data = df.to_dict(orient="records")
        results.append({
            "table_index": i,
            "columns": list(df.columns),
            "data": table_data
        })
    
    return results
