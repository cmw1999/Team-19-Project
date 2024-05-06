'''
main API file
'''
from fastapi import FastAPI, HTTPException, Query, Depends, Response
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Text, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from sqlalchemy.future import select
import requests
from bs4 import BeautifulSoup
import urllib.parse
from urllib.parse import urlparse
# Start API
app = FastAPI()

# Database Configuration
DATABASE_URL = "insert database url here"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Models
class URL(Base):
    __tablename__ = 'urls'
    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, unique=True, index=True)
    is_crawled = Column(Boolean, default=False)
    links = relationship('Link', back_populates='parent')

class Link(Base):
    __tablename__ = 'links'
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    url = Column(String, index=True)
    parent_id = Column(Integer, ForeignKey('urls.id'))
    parent = relationship('URL', back_populates='links')

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def fetch_page(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None

def parse_links(html):
    soup = BeautifulSoup(html, 'html.parser')
    links = soup.find_all('a', href=True)
    return [{"title": a.text.strip(), "url": a['href']} for a in links if a.text.strip() != '']

def make_absolute_url(base_url, link):
    return urllib.parse.urljoin(base_url, link)

def get_base_url(url):
    parsed_url = urlparse(url)
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
    return base_url

def recursive_crawl(db, base_url, url, depth):
    if depth < 1:
        return []
    
    # Make sure the URL is absolute
    absolute_url = make_absolute_url(base_url, url)

    # Fetch the HTML content of the page
    html = fetch_page(absolute_url)
    if not html:
        return []

    # Parse links from the HTML content
    links = parse_links(html)

    # Check if the URL already exists in the database
    existing_url = db.query(URL).filter_by(url=absolute_url).first()
    if not existing_url:
        url_entry = URL(url=absolute_url, is_crawled=True)
        db.add(url_entry)
        try:
            db.commit()
            db.refresh(url_entry)
        except Exception as e:
            print(f"Error inserting URL: {e}")
            db.rollback()
            return []
    else:
        url_entry = existing_url

    for link in links:
        # Convert link to absolute before storing or recursing
        absolute_link_url = make_absolute_url(base_url, link['url'])
        link_entry = Link(title=link['title'], url=absolute_link_url, parent_id=url_entry.id)
        db.add(link_entry)
    try:
        db.commit()
    except Exception as e:
        print(f"Error committing link entries: {e}")
        db.rollback()

    if depth > 1:
        for link in links:
            link['children'] = recursive_crawl(db, base_url, link['url'], depth - 1)
    return links

@app.get("/", response_class=Response)
async def base():
    content = """
    200: OK
    Paths:
    /crawl/
        url=http://example.com
        depth=2
    /search/
        query=query
    search
    Examples:
    /crawl/?url=http://example.com&depth=2
    /search/?query=books
    """
    return Response(content=content, media_type="text/plain")

@app.get("/crawl/")
async def crawl_endpoint(url: str = Query(..., description="The URL to start crawling from"),
                         depth: int = Query(1, description="The depth to crawl, 1 being only the given URL"),
                         db: Session = Depends(get_db)):
    # Dynamically determine the base URL
    base_url = get_base_url(url)
    if depth > 3:
        raise HTTPException(status_code=400, detail="Depth is too large. Maximum allowed depth is 3.")
    
    links = recursive_crawl(db, base_url, url, depth)
    return {"url": url, "depth": depth, "links": links}

@app.get("/search/")
def search(query: str = Query(None), db: Session = Depends(get_db)):
    if query:
        query = f"%{query}%"
        result = db.execute(select(URL).filter(URL.url.like(query)))
    else:
        result = db.execute(select(URL))
    urls = result.scalars().all()
    return [{"id": url.id, "url": url.url, "is_crawled": url.is_crawled} for url in urls]

@app.get("/reset/")
def reset_crawling_data(db: Session = Depends(get_db)):
    # Delete all Link entries
    db.query(Link).delete()
    # Delete all URL entries
    db.query(URL).delete()
    db.commit()
    return {"status": "success", "message": "Crawling data reset successfully"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)