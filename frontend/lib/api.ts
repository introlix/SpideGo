const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8889/api/v1";

export interface SearchResult {
    title: string;
    content: string;
    url: string;
    engine: string;
    thumbnail_src: string | null;
    thumbnail: string | null;
    img_src: string;
    publishedDate: string | null;
}

export interface SearchResponse {
    results: SearchResult[];
}

export interface FeaturedSnippet {
    _id: string;
    title: string;
    description: string;
    url: string;
    chunk_id: number;
    chunk_text: string;
}



export async function getSearchSuggestions(query: string): Promise<string[]> {
    const res = await fetch(`${BASE_URL}/search/suggestions/?query=${query}`);
    if (!res.ok) throw new Error("Failed to fetch workspaces");
    return res.json();
}

export async function getSearchResults(query: string, tab: string): Promise<SearchResponse> {
    const res = await fetch(`${BASE_URL}/search/?query=${query}&tab=${tab}`);
    if (!res.ok) {
        throw new Error(`Search request failed: ${res.status}`);
    }

    return res.json();
}


export async function getFeaturedSnippets(
  query: string,
  urls: string[]
): Promise<FeaturedSnippet[]> {
  const res = await fetch(
    `${BASE_URL}/search/featured_snippets/?query=${encodeURIComponent(query)}`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(urls),
    }
  );

  if (!res.ok) {
    throw new Error(`Featured snippets request failed: ${res.status}`);
  }

  return res.json();
}