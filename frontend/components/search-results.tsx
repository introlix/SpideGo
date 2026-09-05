"use client";

import { ExternalLink, Globe } from "lucide-react";

import { Skeleton } from "@/components/ui/skeleton";
import { SearchResult } from "@/lib/api";
import { useFeaturedSnippets, useSearch } from "@/hooks/use-search";
import Link from "next/link";
import { Card, CardContent } from "./ui/card";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";


function hostname(url: string) {
  try {
    return new URL(url).hostname.replace(/^www\./, "");
  } catch {
    return url;
  }
}

function ResultItem({ result }: { result: SearchResult }) {
  const image = result.thumbnail_src || result.img_src || result.thumbnail;

  return (
    <article className="mb-5">
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-1.5 text-xs text-neutral-500">
          <Globe className="h-3.5 w-3.5" />
          <span className="truncate">{result.url.slice(0, 100)}</span>
        </div>
        <Link
          href={result.url}
          target="_blank"
          className="mt-1 block truncate text-lg text-blue-400 hover:underline"
        >
          {result.title}
        </Link>
        <div className="sm:flex gap-4">
          {image && (
            <Link
              href={result.url}
              target="_blank">
              <img
                src={image}
                alt=""
                loading="lazy"
                className="aspect-video max-w-52 rounded-xl border border-white/5 object-cover transition"
              />
            </Link>
          )}
          <div className="text-neutral-400">
            <p>
              {result.content.slice(0, 100)}
            </p>
          </div>
        </div>
      </div>
    </article>
  );
}

function ImageGrid({ results }: { results: SearchResult[] }) {
  return (
    <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-7 sm:mt-0 mt-10">
      {results.map((result, index) => (
        <Link
          key={`${result.url}_${index}`}
          href={result.url}
          target="_blank"
        >
          <img
            src={result.img_src || result.thumbnail_src || ""}
            alt={result.title}
            loading="lazy"
            className="aspect-square w-full rounded-xl border border-white/5 object-cover transition"
          />
          <p className="mt-2 truncate text-sm text-neutral-300 hover:underline">
            {result.title}
          </p>
        </Link>
      ))}
    </div>
  );
}

function LoadingSkeleton() {
  return (
    <div className="space-y-8 sm:ml-40 sm:max-w-2xl w-full sm:mt-0 mt-10">
      {Array.from({ length: 6 }).map((_, i) => (
        <div key={i} className="flex gap-4">
          <Skeleton className="h-24 w-24 bg-white/10" />
          <div className="flex-1 space-y-2">
            <Skeleton className="h-3 w-32 bg-white/10" />
            <Skeleton className="h-5 w-2/3 bg-white/10" />
            <Skeleton className="h-4 w-full bg-white/10" />
          </div>
        </div>
      ))}
    </div>
  );
}

function FeatureSnippets({ query, urls }: { query: string; urls: string[] }) {
  const { data: results, isPending, isError } = useFeaturedSnippets(query, urls.slice(0, 3))

  if (isPending) {
    return <p className="sm:mt-0 mt-10">Loading..</p>;
  }

  if (!results) {
    return <p></p>
  }

  return (
    <div className="max-h-96 overflow-y-auto snippets-scroll space-y-10 sm:mt-0 mt-10">
      {results?.map((data, index) => (
        <Card key={index} className="bg-accent">
          <CardContent>
            <div className="truncate text-neutral-400">
              {new URL(data.url).hostname}
            </div>
            <div className="text-[#3b9cff] hover:underline truncate">
              <Link href={data.url} target="_blank" className="text-lg truncate">{data.title}</Link>
            </div>
            <article
              className="prose prose-neutral max-w-none dark:prose-invert prose-headings:scroll-mt-20 prose-h2:mt-8 prose-h2:mb-3 prose-h3:mt-6 prose-h3:mb-2 prose-p:my-3 prose-ul:my-3 prose-ol:my-3 prose-li:my-1 prose-table:my-5 prose-a:no-underline hover:prose-a:underline overflow-x-auto"
              dangerouslySetInnerHTML={{ __html: data.chunk_text }}
            />
            <Link href={data.url} target="_blank" className="text-[#3b9cff] text-end">Read More...</Link>
          </CardContent>
        </Card>
      ))}
    </div>
  )
}


export function SearchResults({ query, tab }: { query: string; tab: string }) {
  const { data, isPending, isError } = useSearch(query, tab);

  const urls = data?.results?.map((result) => result.url) ?? [];

  if (isPending) return <LoadingSkeleton />;

  if (isError)
    return <p className="text-sm text-neutral-400">Something went wrong, please try again.</p>;

  const results = data?.results ?? [];

  if (results.length === 0)
    return <p className="text-sm text-neutral-400">No results found.</p>;

  if (tab === "images") {
    return <ImageGrid results={results.filter((r) => r.img_src || r.thumbnail_src)} />;
  }

  return (
    <div className="space-y-8 sm:ml-40 sm:max-w-2xl w-full">
      <FeatureSnippets query={query} urls={urls} />
      <div>
        {results.map((result, index) => (
          <ResultItem key={`${result.url}_${index}`} result={result} />
        ))}
      </div>
    </div >
  );
}