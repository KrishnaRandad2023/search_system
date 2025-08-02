"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { apiClient, AutosuggestItem } from "@/lib/api";

interface HeaderProps {
  initialQuery?: string;
  showCategories?: boolean;
}

export default function Header({
  initialQuery = "",
  showCategories = true,
}: HeaderProps) {
  const [query, setQuery] = useState(initialQuery);
  const [suggestions, setSuggestions] = useState<AutosuggestItem[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [popularQueries, setPopularQueries] = useState<string[]>([]);

  const searchInputRef = useRef<HTMLInputElement>(null);
  const suggestionsRef = useRef<HTMLDivElement>(null);
  const router = useRouter();

  // Debounce timer
  const debounceRef = useRef<NodeJS.Timeout | null>(null);

  // Load popular queries on mount
  useEffect(() => {
    const loadPopularQueries = async () => {
      try {
        const queries = await apiClient.getPopularQueries(6);
        setPopularQueries(queries);
      } catch (error) {
        console.error("Failed to load popular queries:", error);
      }
    };
    loadPopularQueries();
  }, []);

  // Handle autosuggest
  const handleAutosuggest = async (searchQuery: string) => {
    if (!searchQuery.trim()) {
      setSuggestions([]);
      setShowSuggestions(false);
      return;
    }

    setIsLoading(true);
    try {
      const response = await apiClient.getAutosuggest(searchQuery, 8);
      setSuggestions(response.suggestions);
      setShowSuggestions(true);
    } catch (error) {
      console.error("Autosuggest failed:", error);
      setSuggestions([]);
    } finally {
      setIsLoading(false);
    }
  };

  // Debounced search
  const debouncedAutosuggest = (searchQuery: string) => {
    if (debounceRef.current) {
      clearTimeout(debounceRef.current);
    }

    debounceRef.current = setTimeout(() => {
      handleAutosuggest(searchQuery);
    }, 200);
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setQuery(value);
    debouncedAutosuggest(value);
  };

  const handleSearch = (searchQuery: string = query) => {
    if (!searchQuery.trim()) return;

    setShowSuggestions(false);
    router.push(`/search?q=${encodeURIComponent(searchQuery.trim())}`);
  };

  const handleSuggestionClick = (suggestion: AutosuggestItem) => {
    setQuery(suggestion.text);
    handleSearch(suggestion.text);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      e.preventDefault();
      handleSearch();
    } else if (e.key === "Escape") {
      setShowSuggestions(false);
    }
  };

  // Close suggestions when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        suggestionsRef.current &&
        !suggestionsRef.current.contains(event.target as Node) &&
        !searchInputRef.current?.contains(event.target as Node)
      ) {
        setShowSuggestions(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const categories = [
    "Electronics",
    "Fashion",
    "Home & Kitchen",
    "Books",
    "Sports",
    "Beauty",
    "Automotive",
    "Grocery",
  ];

  return (
    <>
      {/* Main Header */}
      <header className="bg-white shadow-sm border-b border-gray-200 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Logo */}
            <div className="flex-shrink-0">
              <button
                onClick={() => router.push("/")}
                className="flex items-center space-x-2 text-blue-600 hover:text-blue-700 transition-colors"
              >
                <div className="w-8 h-8 bg-blue-600 rounded flex items-center justify-center">
                  <span className="text-white font-bold text-sm">F</span>
                </div>
                <span className="text-xl font-bold hidden sm:block">
                  Flipkart
                </span>
              </button>
            </div>

            {/* Search Bar */}
            <div className="flex-1 max-w-2xl mx-4 relative">
              <div className="relative">
                <input
                  ref={searchInputRef}
                  type="text"
                  value={query}
                  onChange={handleInputChange}
                  onKeyDown={handleKeyDown}
                  onFocus={() => query && setShowSuggestions(true)}
                  placeholder="Search for products, brands and more"
                  className="w-full px-4 py-2 pl-4 pr-12 text-gray-900 placeholder-gray-500 border border-gray-300 rounded-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
                <button
                  onClick={() => handleSearch()}
                  className="absolute right-0 top-0 h-full px-4 bg-blue-600 text-white rounded-r-sm hover:bg-blue-700 transition-colors flex items-center justify-center"
                >
                  <svg
                    className="w-5 h-5"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                    />
                  </svg>
                </button>

                {isLoading && (
                  <div className="absolute right-14 top-1/2 transform -translate-y-1/2">
                    <div className="animate-spin h-4 w-4 border-2 border-blue-600 border-t-transparent rounded-full"></div>
                  </div>
                )}
              </div>

              {/* Autosuggest Dropdown */}
              {showSuggestions && (
                <div
                  ref={suggestionsRef}
                  className="absolute top-full left-0 right-0 bg-white border border-gray-200 border-t-0 rounded-b-sm shadow-lg z-50 max-h-96 overflow-y-auto animate-slide-up"
                >
                  {suggestions.length > 0 ? (
                    <div className="py-2">
                      {suggestions.map((suggestion, index) => (
                        <button
                          key={index}
                          onClick={() => handleSuggestionClick(suggestion)}
                          className="w-full px-4 py-2 text-left hover:bg-gray-50 flex items-center justify-between group transition-colors"
                        >
                          <div className="flex items-center space-x-3">
                            <svg
                              className="w-4 h-4 text-gray-400"
                              fill="none"
                              stroke="currentColor"
                              viewBox="0 0 24 24"
                            >
                              <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth={2}
                                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                              />
                            </svg>
                            <span className="text-gray-900">
                              {suggestion.text}
                            </span>
                            {suggestion.category && (
                              <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">
                                {suggestion.category}
                              </span>
                            )}
                          </div>
                          {suggestion.is_trending && (
                            <span className="text-xs text-orange-500 font-medium">
                              Trending
                            </span>
                          )}
                        </button>
                      ))}
                    </div>
                  ) : query.trim() && !isLoading ? (
                    <div className="py-4 px-4 text-gray-500 text-center">
                      No suggestions found for "{query}"
                    </div>
                  ) : null}

                  {/* Show popular queries when input is empty */}
                  {!query.trim() && popularQueries.length > 0 && (
                    <div className="py-2 border-t border-gray-100">
                      <div className="px-4 py-2 text-xs font-medium text-gray-500 uppercase tracking-wide">
                        Popular Searches
                      </div>
                      {popularQueries.map((popularQuery, index) => (
                        <button
                          key={index}
                          onClick={() =>
                            handleSuggestionClick({ text: popularQuery })
                          }
                          className="w-full px-4 py-2 text-left hover:bg-gray-50 flex items-center space-x-3 transition-colors"
                        >
                          <svg
                            className="w-4 h-4 text-gray-400"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"
                            />
                          </svg>
                          <span className="text-gray-700">{popularQuery}</span>
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* User Actions */}
            <div className="flex items-center space-x-4">
              <button className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors">
                <svg
                  className="w-6 h-6"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
                  />
                </svg>
              </button>

              <button className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors">
                <svg
                  className="w-6 h-6"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"
                  />
                </svg>
              </button>

              <button className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors relative">
                <svg
                  className="w-6 h-6"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M3 3h2l.4 2M7 13h10l4-8H5.4m0 0L7 13m0 0l-2.5 5M7 13l2.5 5m10-5v6a1 1 0 01-1 1H9a1 1 0 01-1-1v-6m10 0V9a1 1 0 00-1-1H9a1 1 0 00-1 1v4.01"
                  />
                </svg>
                <span className="absolute -top-1 -right-1 bg-orange-500 text-white text-xs rounded-full h-5 w-5 flex items-center justify-center">
                  0
                </span>
              </button>
            </div>
          </div>
        </div>

        {/* Categories Bar */}
        {showCategories && (
          <div className="bg-white border-t border-gray-100">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
              <div className="flex items-center space-x-8 py-2 overflow-x-auto">
                {categories.map((category) => (
                  <button
                    key={category}
                    onClick={() =>
                      router.push(
                        `/search?category=${encodeURIComponent(category)}`
                      )
                    }
                    className="whitespace-nowrap text-sm text-gray-600 hover:text-blue-600 py-2 transition-colors"
                  >
                    {category}
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}
      </header>
    </>
  );
}
