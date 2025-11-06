from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# --------------------
# Create the FastAPI app
# --------------------
app = FastAPI()

# Allow CORS (so it works with frontend apps too)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------
# Define the model (schema)
# --------------------
class Book(BaseModel):
    title: str
    author: str
    year: int

# --------------------
# In-memory "database"
# --------------------
books = [
    {"id": 1, "title": "The Alchemist", "author": "Paulo Coelho", "year": 1988},
    {"id": 2, "title": "1984", "author": "George Orwell", "year": 1949},
    {"id": 3, "title": "Atomic Habits", "author": "James Clear", "year": 2018},
]
next_id = 4

# --------------------
# CRUD Endpoints
# --------------------

# 🟢 READ - Get all books
@app.get("/books")
def get_books():
    return {"books": books}

# 🟢 READ - Get a single book by ID
@app.get("/books/{book_id}")
def get_book(book_id: int):
    for book in books:
        if book["id"] == book_id:
            return {"book": book}
    raise HTTPException(status_code=404, detail="Book not found")

# 🟡 CREATE - Add a new book
@app.post("/books")
def add_book(new_book: Book):
    global next_id
    book_data = {"id": next_id, **new_book.dict()}
    books.append(book_data)
    next_id += 1
    return {"message": "Book added successfully", "book": book_data}

# 🔵 UPDATE - Edit an existing book
@app.put("/books/{book_id}")
def update_book(book_id: int, updated_book: Book):
    for book in books:
        if book["id"] == book_id:
            book.update(updated_book.dict())
            return {"message": "Book updated successfully", "book": book}
    raise HTTPException(status_code=404, detail="Book not found")

# 🔴 DELETE - Remove a book
@app.delete("/books/{book_id}")
def delete_book(book_id: int):
    for book in books:
        if book["id"] == book_id:
            books.remove(book)
            return {"message": "Book deleted successfully"}
    raise HTTPException(status_code=404, detail="Book not found")
