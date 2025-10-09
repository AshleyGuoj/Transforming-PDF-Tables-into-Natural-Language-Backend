import json
import os
import sys
from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient

endpoint = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT", "https://grand811.cognitiveservices.azure.com/")
api_key = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_KEY")

if not api_key:
    raise ValueError("AZURE_DOCUMENT_INTELLIGENCE_KEY environment variable is not set")

client = DocumentIntelligenceClient(endpoint=endpoint, credential=AzureKeyCredential(api_key))

# Get PDF file path from command line argument or use default
if len(sys.argv) > 1:
    pdf_file = sys.argv[1]
else:
    pdf_file = "Wholesale_Rate_Sheet_6.9.25.pdf"

print(f"Processing PDF: {pdf_file}")

with open(pdf_file, "rb") as f:
    poller = client.begin_analyze_document("prebuilt-layout", body=f)
    result = poller.result()

tables_data = []
merged_cells_found = False

# Tables are at the top level of result, not under pages
if result.tables:
    print(f"\n📊 Analyzing {len(result.tables)} table(s)...")
    
    for table_idx, table in enumerate(result.tables, 1):
        print(f"\n--- Table {table_idx} ---")
        # Get the page number from bounding regions
        page_number = table.bounding_regions[0].page_number if table.bounding_regions else None
        
        table_info = {
            "page_number": page_number,
            "table_coordinates": table.bounding_regions[0].polygon if table.bounding_regions else None,
            "rows": []
        }

        print(f"  Dimensions: {table.row_count} rows × {table.column_count} columns")
        print(f"  Total cells: {len(table.cells)}")
        
        # Initialize a matrix to hold the table content with cell metadata
        table_matrix = [[{"text": "", "row_span": 1, "column_span": 1} for _ in range(table.column_count)] for _ in range(table.row_count)]

        # Track merged cells for reporting
        table_merged_cells = []
        
        for cell in table.cells:
            row_span = getattr(cell, 'row_span', 1) or 1
            column_span = getattr(cell, 'column_span', 1) or 1
            
            # Check if this cell has merged spans
            if row_span > 1 or column_span > 1:
                merged_cells_found = True
                cell_text = cell.content[:30] + "..." if len(cell.content) > 30 else cell.content
                table_merged_cells.append({
                    "position": f"[{cell.row_index}, {cell.column_index}]",
                    "text": cell_text,
                    "row_span": row_span,
                    "column_span": column_span
                })
            
            table_matrix[cell.row_index][cell.column_index] = {
                "text": cell.content,
                "row_span": row_span,
                "column_span": column_span
            }
        
        # Report merged cells found in this table
        if table_merged_cells:
            print(f"  ✅ Found {len(table_merged_cells)} merged cell(s):")
            for mc in table_merged_cells:
                spans = []
                if mc["row_span"] > 1:
                    spans.append(f"rowspan={mc['row_span']}")
                if mc["column_span"] > 1:
                    spans.append(f"colspan={mc['column_span']}")
                span_text = ", ".join(spans)
                print(f"     • Position {mc['position']}: \"{mc['text']}\" ({span_text})")
        else:
            print(f"  ℹ️  No merged cells detected")

        # Convert the matrix to a list of rows with headers and cells
        for row_index, row in enumerate(table_matrix):
            row_data = {
                "row_index": row_index,
                "cells": [
                    {
                        "column_index": col_index, 
                        "text": cell["text"],
                        "row_span": cell["row_span"],
                        "column_span": cell["column_span"]
                    } for col_index, cell in enumerate(row)
                ]
            }
            table_info["rows"].append(row_data)

        tables_data.append(table_info)

# Create output directory if it doesn't exist
output_dir = "output"
os.makedirs(output_dir, exist_ok=True)

# Generate output filename based on input PDF filename
pdf_basename = os.path.splitext(os.path.basename(pdf_file))[0]
output_file = os.path.join(output_dir, f"{pdf_basename}.json")

# Save the results to a JSON file in the output folder
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(tables_data, f, indent=4, ensure_ascii=False)

print(f"\n{'='*60}")
print(f"✅ Table extraction complete!")
print(f"📁 Results saved to: {output_file}")
print(f"📊 Total tables extracted: {len(tables_data)}")

if merged_cells_found:
    print(f"🔗 Merged cells detected - structure preserved in JSON")
    print(f"💡 Tip: Use visualize_table.py to view the table structure")
else:
    print(f"ℹ️  No merged cells found - simple table structure")
print(f"{'='*60}")
