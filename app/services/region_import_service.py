"""
Service to import regions from CSV file
"""
import pandas as pd
from sqlalchemy.orm import Session
from app.models.region_model import Region
from typing import Dict, Any

def import_csv(file_path: str, db: Session) -> Dict[str, Any]:
    try:
        # Read CSV with multiple encoding attempts
        encodings = ['utf-8', 'cp1252', 'latin-1', 'iso-8859-1', 'utf-8-sig']
        df = None
        
        for encoding in encodings:
            try:
                df = pd.read_csv(file_path, encoding=encoding)
                break
            except UnicodeDecodeError:
                continue
        
        if df is None:
            return {
                "success": False,
                "error": "Không thể đọc file CSV. Vui lòng kiểm tra encoding của file."
            }
        
        # Validate columns
        required_cols = ['name']
        if not all(col in df.columns for col in required_cols):
            return {
                "success": False,
                "error": f"CSV phải có cột: {', '.join(required_cols)}"
            }
        
        success_count = 0
        error_count = 0
        errors = []
        
        # Create mapping of row index to region ID for parent lookup
        created_regions = {}
        
        for idx, row in df.iterrows():
            try:
                name = row.get('name', '').strip()
                parent_id = row.get('parent_id')
                
                if not name:
                    error_count += 1
                    errors.append(f"Row {idx + 2}: Tên region không được để trống")
                    continue
                
                # Handle parent_id
                if pd.isna(parent_id) or parent_id == '':
                    parent_id = None
                else:
                    parent_id = int(parent_id)
                    
                    # Check if parent exists
                    if parent_id and not db.query(Region).filter(Region.id == parent_id).first():
                        error_count += 1
                        errors.append(f"Row {idx + 2}: Parent ID {parent_id} không tồn tại")
                        continue
                
                # Check if region already exists
                existing = db.query(Region).filter(
                    Region.name == name,
                    Region.parent_id == parent_id
                ).first()
                
                if existing:
                    # Skip duplicate
                    created_regions[idx] = existing.id
                    success_count += 1
                    continue
                
                # Create new region
                region = Region(
                    name=name,
                    parent_id=parent_id
                )
                
                db.add(region)
                db.flush()  # Flush to get ID without committing
                
                created_regions[idx] = region.id
                success_count += 1
                
            except Exception as e:
                error_count += 1
                errors.append(f"Row {idx + 2}: {str(e)}")
        
        db.commit()
        
        return {
            "success": True,
            "total": len(df),
            "success_count": success_count,
            "error_count": error_count,
            "errors": errors
        }
        
    except Exception as e:
        db.rollback()
        return {
            "success": False,
            "error": str(e)
        }
