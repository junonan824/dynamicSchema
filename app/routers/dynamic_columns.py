from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from .. import crud, schemas, database

router = APIRouter(
    prefix="/dynamic-columns",
    tags=["dynamic-columns"],
    responses={404: {"description": "Not found"}},
)

@router.get("/", response_model=List[schemas.DynamicColumns])
def read_dynamic_columns(skip: int = 0, limit: int = 100, db: Session = Depends(database.get_db)):
    columns = crud.get_dynamic_columns(db, skip=skip, limit=limit)
    return columns

@router.get("/{column_id}", response_model=schemas.DynamicColumns)
def read_dynamic_column(column_id: int, db: Session = Depends(database.get_db)):
    db_column = crud.get_dynamic_column(db, column_id=column_id)
    if db_column is None:
        raise HTTPException(status_code=404, detail="Dynamic column not found")
    return db_column

@router.post("/", response_model=schemas.DynamicColumns)
def create_dynamic_column(column: schemas.DynamicColumnsCreate, db: Session = Depends(database.get_db)):
    return crud.create_dynamic_column(db=db, column=column)

@router.patch("/{column_id}", response_model=schemas.DynamicColumns)
def update_dynamic_column(column_id: int, column: schemas.DynamicColumnsUpdate, db: Session = Depends(database.get_db)):
    db_column = crud.update_dynamic_column(db, column_id=column_id, column=column)
    if db_column is None:
        raise HTTPException(status_code=404, detail="Dynamic column not found")
    return db_column

@router.delete("/{column_id}", response_model=schemas.DynamicColumns)
def delete_dynamic_column(column_id: int, db: Session = Depends(database.get_db)):
    db_column = crud.delete_dynamic_column(db, column_id=column_id)
    if db_column is None:
        raise HTTPException(status_code=404, detail="Dynamic column not found")
    return db_column 