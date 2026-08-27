"use client";
import React from 'react';

import { Input } from "@/components/ui/input";
import { useSearchSuggestions } from "@/hooks/use-suggestions";
import { cn } from "@/lib/utils";
import { Search, X } from "lucide-react";
import { useRouter } from "next/navigation";
import { useRef, useState } from "react";

export const SearchInput = ({ q }: { q?: string }) => {

    const router = useRouter();
    const [query, setQuery] = useState(q ?? "");
    const [selectedIndex, setSelectedIndex] = useState(-1);
    const [suggestionQuery, setSuggestionQuery] = useState("");
    const [isFocused, setIsFocused] = useState(false);
    const inputRef = useRef<HTMLInputElement>(null);

    const hasQuery = query.trim().length > 0;
    const suggestions = useSearchSuggestions(suggestionQuery);

    const handleSubmit = (e: React.SubmitEvent<HTMLFormElement>) => {
        e.preventDefault();

        const formData = new FormData(e.currentTarget);
        const params = new URLSearchParams();

        formData.forEach((value, key) => {
            const stringValue = typeof value === "string" ? value.trim() : "";

            if (stringValue) {
                params.set(key, stringValue);
            }
        });

        if (!params.get("q")) {
            inputRef.current?.focus();
            return;
        }

        router.push(`/search?${params.toString()}&tab=general`);
    };


    const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
        if (!suggestions.data?.length) return;

        if (e.key == "ArrowDown") {
            e.preventDefault();
            setSelectedIndex((prev) => {
                const next = prev < suggestions.data.length - 1 ? prev + 1 : 0;

                setQuery(suggestions.data[next]);

                return next;
            });
        }

        if (e.key == "ArrowUp") {
            e.preventDefault();
            setSelectedIndex((prev) => {
                const next = prev > 0 ? prev - 1 : suggestions.data.length - 1;

                setQuery(suggestions.data[next]);

                return next;
            });
        }

        if (e.key === " " && selectedIndex >= 0) {
            const newQuery = suggestions.data[selectedIndex] + " ";
            setQuery(newQuery);
            setSuggestionQuery(newQuery);
            setSelectedIndex(-1);
        }
    }
    return (
        <div className='relative w-full'>
            <form onSubmit={handleSubmit} className="">
                <Input
                    ref={inputRef}
                    id="search"
                    name="q"
                    type="text"
                    placeholder="Search privately"
                    autoComplete="off"
                    value={query}
                    onChange={(e) => {
                        setQuery(e.target.value);
                        setSuggestionQuery(e.target.value);
                        setSelectedIndex(-1);
                    }}
                    onFocus={() => setIsFocused(true)}
                    onBlur={() => {
                        setTimeout(() => {
                            setIsFocused(false);
                        }, 150);
                    }}
                    onKeyDown={handleKeyDown}
                    className={`h-14 border-none bg-accent pl-6 font-semibold text-neutral-200 shadow-none focus-visible:ring-0 ${query.length > 0 ? "pr-24" : "pr-16"} ${suggestions.data?.length && hasQuery && isFocused ? "rounded-t-3xl rounded-b-none" : "rounded-full"}`}
                />

                {hasQuery && (
                    <button
                        type="button"
                        aria-label="Clear search"
                        onClick={() => {
                            setQuery("");
                            inputRef.current?.focus();
                        }}
                        className="absolute right-14 top-1/2 z-10 -translate-y-1/2 rounded-full p-1 text-neutral-400 transition-colors hover:text-neutral-200"
                    >
                        <X className="h-5 w-5" />
                    </button>
                )}

                <button
                    type="submit"
                    aria-label="Search"
                    className={`absolute right-3 top-1/2 z-10 flex h-9 w-9 -translate-y-1/2 cursor-pointer items-center justify-center rounded-full transition-colors ${hasQuery
                        ? "bg-blue-400 text-white hover:bg-blue-500"
                        : "text-neutral-400 hover:text-neutral-200"
                        }`}
                >
                    <Search className="h-5 w-5" />
                </button>
            </form>
            {isFocused && suggestions.data && query && (
                <ul className="absolute w-full overflow-hidden rounded-b-xl bg-accent p-2 text-accent-foreground">
                    {suggestions.data?.map((suggestion, index) => (
                        <li
                            key={index}
                            aria-selected={index === selectedIndex}
                            onClick={() => {
                                setQuery(suggestion);

                                const params = new URLSearchParams();
                                params.set("q", suggestion);

                                router.push(`/search?${params.toString()}&tab=general`);
                            }}
                            className={cn(
                                "flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                                index === selectedIndex
                                    ? "bg-accent-foreground/10 text-accent-foreground"
                                    : "text-accent-foreground/70 hover:bg-accent-foreground/10 hover:text-muted-foreground"
                            )}
                        >
                            <Search className="h-4 w-4 shrink-0 text-muted-foreground" />
                            <span className="truncate">{suggestion}</span>
                        </li>
                    ))}
                </ul>
            )}
        </div>
    )
}
