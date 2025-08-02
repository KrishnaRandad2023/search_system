"use client";

import { useState, useEffect, useCallback } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import Header from "@/components/ui/Header";
import ProductCard from "@/components/search/ProductCard";
import {
  apiClient,
  SearchResponse,
  SearchFilters,
  ProductResult,
  handleApiError,
} from "@/lib/api";

export default function SearchPage() {
  const searchParams = useSearchParams();
  const router = useRouter();

  const [searchResults, setSearchResults] = useState<SearchResponse | null>(
    null
  );
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [sortBy, setSortBy] = useState("relevance");
  const [filters, setFilters] = useState<SearchFilters>({});

  // Get search parameters
  const query = searchParams.get("q") || "";
  const category = searchParams.get("category") || "";
  const brand = searchParams.get("brand") || "";

  // Perform search
  const performSearch = useCallback(
    async (
      searchQuery: string,
      page: number = 1,
      searchFilters: SearchFilters = {},
      sortOrder: string = "relevance"
    ) => {
      if (!searchQuery && !category) return;

      setIsLoading(true);
      setError(null);

      try {
        const finalQuery = searchQuery || category;
        const finalFilters = { ...searchFilters };

        if (category && !searchQuery) {
          finalFilters.category = category;
        }
        if (brand) {
          finalFilters.brand = brand;
        }

        const response = await apiClient.search(
          finalQuery,
          finalFilters,
          page,
          20,
          sortOrder
        );

        setSearchResults(response);
      } catch (err) {
        const errorMessage = handleApiError(err);
        setError(errorMessage);
        console.error("Search failed:", err);
      } finally {
        setIsLoading(false);
      }
    },
    [category, brand]
  );

  // Initial search on mount and when parameters change
  useEffect(() => {
    performSearch(query, currentPage, filters, sortBy);
  }, [query, category, brand, currentPage, sortBy, filters, performSearch]);

  // Handle filter changes
  const handleFilterChange = (newFilters: Partial<SearchFilters>) => {
    const updatedFilters = { ...filters, ...newFilters };
    setFilters(updatedFilters);
    setCurrentPage(1);
  };

  // Handle sort change
  const handleSortChange = (newSortBy: string) => {
    setSortBy(newSortBy);
    setCurrentPage(1);
  };

  // Handle pagination
  const handlePageChange = (page: number) => {
    setCurrentPage(page);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  // Handle product click
  const handleProductClick = (product: ProductResult) => {
    // In a real app, this would navigate to product detail page
    console.log("Product clicked:", product);
  };

  const sortOptions = [
    { value: "relevance", label: "Relevance" },
    { value: "price_low_high", label: "Price: Low to High" },
    { value: "price_high_low", label: "Price: High to Low" },
    { value: "rating", label: "Customer Rating" },
    { value: "popularity", label: "Popularity" },
    { value: "newest", label: "Newest First" },
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      <Header initialQuery={query} showCategories={false} />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Search Info */}
        <div className="mb-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                {query
                  ? `Search results for "${query}"`
                  : `${category} Products`}
              </h1>
              {searchResults && (
                <p className="text-gray-600 mt-1">
                  {searchResults.total_results.toLocaleString()} results found
                  in {searchResults.search_metadata.response_time_ms}ms
                </p>
              )}
              {searchResults?.search_metadata.has_typo_correction &&
                searchResults.search_metadata.corrected_query && (
                  <p className="text-sm text-blue-600 mt-1">
                    Showing results for "
                    {searchResults.search_metadata.corrected_query}"
                  </p>
                )}
            </div>

            {/* Sort Dropdown */}
            <div className="flex items-center space-x-4">
              <label
                htmlFor="sort"
                className="text-sm font-medium text-gray-700"
              >
                Sort by:
              </label>
              <select
                id="sort"
                value={sortBy}
                onChange={(e) => handleSortChange(e.target.value)}
                className="border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                {sortOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Applied Filters */}
          {Object.keys(filters).length > 0 && (
            <div className="mt-4 flex flex-wrap gap-2">
              <span className="text-sm font-medium text-gray-700">
                Filters:
              </span>
              {Object.entries(filters).map(([key, value]) => {
                if (!value) return null;
                return (
                  <span
                    key={key}
                    className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
                  >
                    {key}: {value}
                    <button
                      onClick={() => {
                        const newFilters = { ...filters };
                        delete newFilters[key as keyof SearchFilters];
                        setFilters(newFilters);
                      }}
                      className="ml-2 text-blue-600 hover:text-blue-800"
                    >
                      ×
                    </button>
                  </span>
                );
              })}
            </div>
          )}
        </div>

        <div className="flex gap-6">
          {/* Filters Sidebar */}
          {searchResults && (
            <div className="w-64 flex-shrink-0">
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 sticky top-24">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                  Filters
                </h3>

                {/* Price Range */}
                {searchResults.aggregations?.price_ranges &&
                  searchResults.aggregations.price_ranges.length > 0 && (
                    <div className="mb-6">
                      <h4 className="font-medium text-gray-900 mb-3">
                        Price Range
                      </h4>
                      <div className="space-y-2">
                        {searchResults.aggregations.price_ranges.map(
                          (range, index) => (
                            <label key={index} className="flex items-center">
                              <input
                                type="radio"
                                name="price"
                                className="mr-3 text-blue-600 focus:ring-blue-500"
                                onChange={() => {
                                  const [min, max] = range.range
                                    .split("-")
                                    .map((p) =>
                                      parseInt(p.replace(/[^\d]/g, ""))
                                    );
                                  handleFilterChange({
                                    min_price: min,
                                    max_price: max,
                                  });
                                }}
                              />
                              <span className="text-sm text-gray-700">
                                {range.range} ({range.count})
                              </span>
                            </label>
                          )
                        )}
                      </div>
                    </div>
                  )}

                {/* Categories */}
                {searchResults.aggregations?.categories &&
                  searchResults.aggregations.categories.length > 0 && (
                    <div className="mb-6">
                      <h4 className="font-medium text-gray-900 mb-3">
                        Categories
                      </h4>
                      <div className="space-y-2 max-h-48 overflow-y-auto">
                        {searchResults.aggregations.categories
                          .slice(0, 10)
                          .map((cat, index) => (
                            <label key={index} className="flex items-center">
                              <input
                                type="radio"
                                name="category"
                                className="mr-3 text-blue-600 focus:ring-blue-500"
                                onChange={() =>
                                  handleFilterChange({ category: cat.name })
                                }
                              />
                              <span className="text-sm text-gray-700">
                                {cat.name} ({cat.count})
                              </span>
                            </label>
                          ))}
                      </div>
                    </div>
                  )}

                {/* Brands */}
                {searchResults.aggregations?.brands &&
                  searchResults.aggregations.brands.length > 0 && (
                    <div className="mb-6">
                      <h4 className="font-medium text-gray-900 mb-3">Brands</h4>
                      <div className="space-y-2 max-h-48 overflow-y-auto">
                        {searchResults.aggregations.brands
                          .slice(0, 10)
                          .map((brandItem, index) => (
                            <label key={index} className="flex items-center">
                              <input
                                type="radio"
                                name="brand"
                                className="mr-3 text-blue-600 focus:ring-blue-500"
                                onChange={() =>
                                  handleFilterChange({ brand: brandItem.name })
                                }
                              />
                              <span className="text-sm text-gray-700">
                                {brandItem.name} ({brandItem.count})
                              </span>
                            </label>
                          ))}
                      </div>
                    </div>
                  )}

                {/* Rating */}
                <div className="mb-6">
                  <h4 className="font-medium text-gray-900 mb-3">Rating</h4>
                  <div className="space-y-2">
                    {[4, 3, 2, 1].map((rating) => (
                      <label key={rating} className="flex items-center">
                        <input
                          type="radio"
                          name="rating"
                          className="mr-3 text-blue-600 focus:ring-blue-500"
                          onChange={() =>
                            handleFilterChange({ min_rating: rating })
                          }
                        />
                        <span className="text-sm text-gray-700 flex items-center">
                          {rating}
                          <svg
                            className="w-4 h-4 text-yellow-400 ml-1"
                            fill="currentColor"
                            viewBox="0 0 20 20"
                          >
                            <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                          </svg>
                          {" & above"}
                        </span>
                      </label>
                    ))}
                  </div>
                </div>

                {/* Clear Filters */}
                <button
                  onClick={() => {
                    setFilters({});
                    setCurrentPage(1);
                  }}
                  className="w-full text-blue-600 text-sm font-medium hover:text-blue-700 transition-colors"
                >
                  Clear All Filters
                </button>
              </div>
            </div>
          )}

          {/* Main Content */}
          <div className="flex-1">
            {/* Loading State */}
            {isLoading && (
              <div className="text-center py-12">
                <div className="animate-spin h-12 w-12 border-4 border-blue-600 border-t-transparent rounded-full mx-auto mb-4"></div>
                <p className="text-gray-600">Searching for products...</p>
              </div>
            )}

            {/* Error State */}
            {error && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
                <svg
                  className="w-12 h-12 text-red-500 mx-auto mb-4"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"
                  />
                </svg>
                <h3 className="text-lg font-semibold text-red-800 mb-2">
                  Search Error
                </h3>
                <p className="text-red-600">{error}</p>
                <button
                  onClick={() =>
                    performSearch(query, currentPage, filters, sortBy)
                  }
                  className="mt-4 bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 transition-colors"
                >
                  Try Again
                </button>
              </div>
            )}

            {/* No Results */}
            {searchResults &&
              searchResults.products.length === 0 &&
              !isLoading && (
                <div className="text-center py-12">
                  <svg
                    className="w-16 h-16 text-gray-400 mx-auto mb-4"
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
                  <h3 className="text-xl font-semibold text-gray-900 mb-2">
                    No products found
                  </h3>
                  <p className="text-gray-600 mb-4">
                    Try adjusting your search or filters to find what you're
                    looking for.
                  </p>
                  <button
                    onClick={() => {
                      setFilters({});
                      setCurrentPage(1);
                    }}
                    className="text-blue-600 hover:text-blue-700 font-medium"
                  >
                    Clear all filters
                  </button>
                </div>
              )}

            {/* Products Grid */}
            {searchResults && searchResults.products.length > 0 && (
              <>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 mb-8">
                  {searchResults.products.map((product, index) => (
                    <ProductCard
                      key={product.id}
                      product={product}
                      position={(currentPage - 1) * 20 + index + 1}
                      query={query || category}
                      onProductClick={handleProductClick}
                    />
                  ))}
                </div>

                {/* Pagination */}
                {searchResults.total_pages > 1 && (
                  <div className="flex items-center justify-center space-x-2">
                    <button
                      onClick={() => handlePageChange(currentPage - 1)}
                      disabled={currentPage === 1}
                      className="px-3 py-2 text-sm font-medium text-gray-500 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      Previous
                    </button>

                    {/* Page Numbers */}
                    {Array.from(
                      { length: Math.min(5, searchResults.total_pages) },
                      (_, i) => {
                        const page = Math.max(1, currentPage - 2) + i;
                        if (page > searchResults.total_pages) return null;

                        return (
                          <button
                            key={page}
                            onClick={() => handlePageChange(page)}
                            className={`px-3 py-2 text-sm font-medium rounded-md ${
                              page === currentPage
                                ? "bg-blue-600 text-white"
                                : "text-gray-700 bg-white border border-gray-300 hover:bg-gray-50"
                            }`}
                          >
                            {page}
                          </button>
                        );
                      }
                    )}

                    <button
                      onClick={() => handlePageChange(currentPage + 1)}
                      disabled={currentPage === searchResults.total_pages}
                      className="px-3 py-2 text-sm font-medium text-gray-500 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      Next
                    </button>
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
