"use client";

import { getSearchSuggestions } from "@/lib/api";
import { keepPreviousData, useQuery } from "@tanstack/react-query";

export function useSearchSuggestions(query: string) {
  return useQuery({
    queryKey: ["search_suggestions", query],
    queryFn: () => getSearchSuggestions(query),
    enabled: query.trim().length > 0,
    placeholderData: keepPreviousData,
  });
}