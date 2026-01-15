import asyncio
from rich.console import Console

console = Console()

def fetch_url(url: str) -> str:
    """
    Fetch a URL and return its content as markdown using crawl4ai.
    This runs in a synchronous wrapper around the async crawler.
    
    Args:
        url: The URL to fetch
    """
    try:
        from crawl4ai import AsyncWebCrawler
        
        async def _crawl():
            async with AsyncWebCrawler(verbose=True) as crawler:
                result = await crawler.arun(url=url)
                return result.markdown

        # Run the async crawler
        console.print(f"[dim]Crawling {url}...[/dim]")
        
        # We need to use a new event loop for this operation to strictly isolate it
        # or use asyncio.run if not in an existing loop
        return asyncio.run(_crawl())
        
    except ImportError:
        return "Error: crawl4ai not configured. Please run 'space config' to configure crawl4ai"
    except Exception as e:
        return f"Error fetching URL: {e}"


def search_web(query: str, max_results: int = 5, deep_search: bool = False) -> str:
    """
    Search the web using DuckDuckGo.
    
    Args:
        query: Search query
        max_results: Maximum results to return
        deep_search: If True, fetches full content of top 3 results
    """
    try:
        from ddgs import DDGS
        
        results = []
        with DDGS() as ddgs:
            # text() returns an iterator
            for r in ddgs.text(query, max_results=max_results):
                results.append(r)
                
        if not results:
            return f"No results found for '{query}'"
            
        output = f"Search results for '{query}':\n\n"
        
        # Basic snippet output
        for i, r in enumerate(results, 1):
            title = r.get('title', 'No Title')
            href = r.get('href', '#')
            body = r.get('body', '')
            output += f"{i}. [{title}]({href})\n   {body}\n\n"
            
        # Deep search: fetch content of top results
        if deep_search:
            try:
                from crawl4ai import AsyncWebCrawler
                import asyncio
                
                output += "\n--- Deep Search Results (Full Content) ---\n"
                top_urls = [r.get('href') for r in results[:3] if r.get('href')]
                if not top_urls:
                    output += "\nNo valid URLs found for deep search."
                else:
                    console.print(f"[dim]Deep searching top {len(top_urls)} results...[/dim]")
                    
                    async def _crawl_many():
                        async with AsyncWebCrawler(verbose=False) as crawler:
                            crawled_results = await crawler.arun_many(urls=top_urls)
                            return crawled_results

                    crawled_data = asyncio.run(_crawl_many())
                    
                    for i, result in enumerate(crawled_data):
                        url = top_urls[i]
                        markdown = result.markdown if hasattr(result, 'markdown') else str(result)
                        output += f"\n\n### Content from {url}\n"
                        output += f"{'='*40}\n"
                        output += markdown
                        output += f"\n{'='*40}\n"
                        
            except ImportError:
                output += "\n[Warning: crawl4ai not installed, skipping deep search]"
            except Exception as e:
                output += f"\n[Error performing deep search: {e}]"
            
        return output
        
    except ImportError:
        return "Error: duckduckgo-search not installed. Please install with 'uv add duckduckgo-search'"
    except Exception as e:
        return f"Error searching web: {e}"
