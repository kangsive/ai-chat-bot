#!/usr/bin/env python
"""
Generate a database schema diagram using SQLAlchemy models.

This script uses SQLAlchemy metadata to create a Graphviz-based
visualization of the database schema.

Requirements:
- Graphviz must be installed: `sudo apt-get install -y graphviz`
- Python must be able to find the Graphviz executable

Usage:
    python generate_alembic_diagram.py [output_file] [dpi]

Arguments:
    output_file: Optional path for the output file. Defaults to 'alembic_schema.png'
    dpi: Optional resolution in DPI. Defaults to 300
"""

import os
import sys
from pathlib import Path
import subprocess
import tempfile

# Add the current directory to the Python path
sys.path.append(str(Path(__file__).parent))

# Import SQLAlchemy models
from app.models.base import Base

def generate_schema_diagram(output_file='alembic_schema.png', dpi=300):
    """Generate a database schema diagram using SQLAlchemy metadata.
    
    Args:
        output_file: Path to save the output image
        dpi: Resolution in dots per inch (higher for better quality)
    """
    print(f"Generating database schema diagram to {output_file} at {dpi} DPI...")
    
    # Create temporary DOT file
    with tempfile.NamedTemporaryFile(suffix='.dot', delete=False) as tmp:
        dot_file = tmp.name
    
    try:
        # Generate DOT file from SQLAlchemy metadata
        dot_content = """
        digraph G {
            rankdir=LR;
            node [shape=record, fontname="Helvetica", fontsize=10];
            edge [fontname="Helvetica", fontsize=8];
            
            // Database schema from SQLAlchemy models
        """
        
        # Add nodes (tables)
        for table in Base.metadata.sorted_tables:
            attributes = []
            for column in table.columns:
                nullable = "" if column.nullable else " NOT NULL"
                default = f" DEFAULT {column.default.arg}" if column.default and not callable(column.default.arg) else ""
                pk = " PK" if column.primary_key else ""
                
                # Handle foreign keys more carefully
                fk_info = ""
                if column.foreign_keys:
                    fk_refs = []
                    for fk in column.foreign_keys:
                        fk_refs.append(f"{fk.column.table.name}.{fk.column.name}")
                    fk_info = f" FK→{', '.join(fk_refs)}"
                
                attributes.append(f"{column.name} : {column.type}{nullable}{default}{pk}{fk_info}")
            
            attributes_str = "|".join(attributes)
            dot_content += f'    {table.name} [label="{table.name}|{attributes_str}"];\n'
        
        # Add edges (foreign keys)
        for table in Base.metadata.sorted_tables:
            for column in table.columns:
                if column.foreign_keys:
                    for fk in column.foreign_keys:
                        target_table = fk.column.table.name
                        dot_content += f'    {table.name} -> {target_table} [label="{column.name} → {fk.column.name}"];\n'
        
        dot_content += "}"
        
        with open(dot_file, 'w') as f:
            f.write(dot_content)
            
        # Convert DOT file to PNG using Graphviz with increased DPI
        subprocess.run(['dot', '-Tpng', f'-Gdpi={dpi}', dot_file, '-o', output_file], check=True)
        
        print(f"Database schema diagram generated successfully at {output_file}")
        print(f"Full path: {os.path.abspath(output_file)}")
    
    finally:
        # Clean up temporary files
        if os.path.exists(dot_file):
            os.remove(dot_file)

if __name__ == "__main__":
    # 
    # Use in command line: python generate_alembic_diagram.py [output_filename] [dpi]
    # Get the output file path from the command line argument, if provided
    output_file = sys.argv[1] if len(sys.argv) > 1 else 'alembic_schema.png'
    
    # Get the DPI setting from the command line argument, if provided
    dpi = int(sys.argv[2]) if len(sys.argv) > 2 else 300
    
    generate_schema_diagram(output_file, dpi) 