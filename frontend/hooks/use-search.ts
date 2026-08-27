"use client";

import { getFeaturedSnippets, getSearchResults } from "@/lib/api";
import { useQuery } from "@tanstack/react-query";

export function useSearch(query: string, tab:string) {
  return useQuery({
    queryKey: ["search_results", query, tab],
    queryFn: () => getSearchResults(query, tab)
  });
}

export function useFeaturedSnippets(query: string, urls: string[]) {
  return useQuery({
    queryKey: ["featured_snippets", query, urls],
    queryFn: () => getFeaturedSnippets(query, urls)
  })
}