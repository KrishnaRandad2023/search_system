"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Header from "@/components/ui/Header";
import { apiClient } from "@/lib/api";

export default function HomePage() {
  const [trendingCategories, setTrendingCategories] = useState<
    Array<{ category: string; trend_score: number }>
  >([]);
  const [popularQueries, setPopularQueries] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    const loadHomeData = async () => {
      try {
        const [categories, queries] = await Promise.all([
          apiClient.getTrendingCategories(8),
          apiClient.getPopularQueries(12),
        ]);
        setTrendingCategories(categories);
        setPopularQueries(queries);
      } catch (error) {
        console.error("Failed to load home data:", error);
      } finally {
        setIsLoading(false);
      }
    };

    loadHomeData();
  }, []);

  const handleCategoryClick = (category: string) => {
    router.push(`/search?category=${encodeURIComponent(category)}`);
  };

  const handlePopularQueryClick = (query: string) => {
    router.push(`/search?q=${encodeURIComponent(query)}`);
  };

  const featuredCategories = [
    {
      name: "Electronics",
      icon: "📱",
      color: "bg-blue-500",
      description: "Mobiles, Laptops & More",
    },
    {
      name: "Fashion",
      icon: "👕",
      color: "bg-pink-500",
      description: "Clothing & Accessories",
    },
    {
      name: "Home & Kitchen",
      icon: "🏠",
      color: "bg-green-500",
      description: "Furniture & Appliances",
    },
    {
      name: "Books",
      icon: "📚",
      color: "bg-purple-500",
      description: "Literature & Education",
    },
    {
      name: "Sports",
      icon: "⚽",
      color: "bg-orange-500",
      description: "Fitness & Outdoor",
    },
    {
      name: "Beauty",
      icon: "💄",
      color: "bg-red-500",
      description: "Cosmetics & Personal Care",
    },
    {
      name: "Automotive",
      icon: "🚗",
      color: "bg-gray-600",
      description: "Cars & Accessories",
    },
    {
      name: "Grocery",
      icon: "🛒",
      color: "bg-yellow-500",
      description: "Food & Beverages",
    },
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      <Header showCategories={true} />

      {/* Hero Section */}
      <div className="bg-gradient-to-r from-blue-600 to-blue-800 text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
          <div className="text-center">
            <h1 className="text-4xl md:text-6xl font-bold mb-4">
              Next-Gen E-commerce Search
            </h1>
            <p className="text-xl md:text-2xl mb-8 text-blue-100">
              Powered by AI, ML Ranking & Semantic Understanding
            </p>
            <div className="flex flex-wrap justify-center gap-4 text-sm">
              <div className="bg-white/10 px-4 py-2 rounded-full backdrop-blur-sm">
                🚀 Intelligent Autosuggest
              </div>
              <div className="bg-white/10 px-4 py-2 rounded-full backdrop-blur-sm">
                🧠 Semantic Search
              </div>
              <div className="bg-white/10 px-4 py-2 rounded-full backdrop-blur-sm">
                📊 ML-Powered Ranking
              </div>
              <div className="bg-white/10 px-4 py-2 rounded-full backdrop-blur-sm">
                💡 Business Intelligence
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Featured Categories */}
        <section className="mb-16">
          <h2 className="text-2xl font-bold text-gray-900 mb-8 text-center">
            Shop by Category
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            {featuredCategories.map((category) => (
              <button
                key={category.name}
                onClick={() => handleCategoryClick(category.name)}
                className="group bg-white rounded-xl p-6 shadow-sm hover:shadow-md transition-all duration-200 border border-gray-200 hover:border-blue-300"
              >
                <div
                  className={`w-16 h-16 ${category.color} rounded-full flex items-center justify-center text-2xl mb-4 mx-auto group-hover:scale-110 transition-transform`}
                >
                  {category.icon}
                </div>
                <h3 className="font-semibold text-gray-900 mb-2 group-hover:text-blue-600 transition-colors">
                  {category.name}
                </h3>
                <p className="text-sm text-gray-500">{category.description}</p>
              </button>
            ))}
          </div>
        </section>

        {/* Trending Categories */}
        {!isLoading && trendingCategories.length > 0 && (
          <section className="mb-16">
            <h2 className="text-2xl font-bold text-gray-900 mb-8 text-center">
              Trending Now 🔥
            </h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {trendingCategories.map((item, index) => (
                <button
                  key={index}
                  onClick={() => handleCategoryClick(item.category)}
                  className="bg-white rounded-lg p-4 shadow-sm hover:shadow-md transition-all duration-200 border border-gray-200 hover:border-orange-300 group"
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-medium text-gray-900 group-hover:text-orange-600 transition-colors">
                      {item.category}
                    </span>
                    <span className="text-xs bg-orange-100 text-orange-600 px-2 py-1 rounded-full">
                      Hot
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-orange-500 h-2 rounded-full transition-all"
                      style={{
                        width: `${Math.min(100, item.trend_score * 100)}%`,
                      }}
                    ></div>
                  </div>
                </button>
              ))}
            </div>
          </section>
        )}

        {/* Popular Searches */}
        {!isLoading && popularQueries.length > 0 && (
          <section className="mb-16">
            <h2 className="text-2xl font-bold text-gray-900 mb-8 text-center">
              Popular Searches
            </h2>
            <div className="flex flex-wrap justify-center gap-3">
              {popularQueries.map((query, index) => (
                <button
                  key={index}
                  onClick={() => handlePopularQueryClick(query)}
                  className="bg-white text-gray-700 px-4 py-2 rounded-full border border-gray-300 hover:border-blue-500 hover:text-blue-600 hover:bg-blue-50 transition-all duration-200 text-sm"
                >
                  {query}
                </button>
              ))}
            </div>
          </section>
        )}

        {/* Features Showcase */}
        <section className="mb-16">
          <h2 className="text-2xl font-bold text-gray-900 mb-8 text-center">
            Advanced Search Features
          </h2>
          <div className="grid md:grid-cols-3 gap-8">
            <div className="text-center">
              <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg
                  className="w-8 h-8 text-blue-600"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M13 10V3L4 14h7v7l9-11h-7z"
                  />
                </svg>
              </div>
              <h3 className="text-xl font-semibold mb-3">Lightning Fast</h3>
              <p className="text-gray-600">
                Sub-100ms autosuggest and sub-500ms search results with
                intelligent caching
              </p>
            </div>

            <div className="text-center">
              <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg
                  className="w-8 h-8 text-green-600"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
                  />
                </svg>
              </div>
              <h3 className="text-xl font-semibold mb-3">
                Smart Understanding
              </h3>
              <p className="text-gray-600">
                BERT embeddings and semantic search understand context and
                intent
              </p>
            </div>

            <div className="text-center">
              <div className="w-16 h-16 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg
                  className="w-8 h-8 text-purple-600"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
                  />
                </svg>
              </div>
              <h3 className="text-xl font-semibold mb-3">ML-Powered Ranking</h3>
              <p className="text-gray-600">
                XGBoost models optimize results based on relevance, popularity,
                and business metrics
              </p>
            </div>
          </div>
        </section>

        {/* Loading State */}
        {isLoading && (
          <div className="text-center py-12">
            <div className="animate-spin h-12 w-12 border-4 border-blue-600 border-t-transparent rounded-full mx-auto mb-4"></div>
            <p className="text-gray-600">Loading personalized content...</p>
          </div>
        )}
      </div>

      {/* Footer */}
      <footer className="bg-gray-900 text-white py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <h3 className="text-xl font-bold mb-4">
              Flipkart Grid 7.0 - Advanced Search System
            </h3>
            <p className="text-gray-400 mb-4">
              Demonstrating next-generation e-commerce search capabilities with
              AI/ML integration
            </p>
            <div className="text-sm text-gray-500">
              Built with FastAPI, React, TypeScript, Tailwind CSS, and advanced
              ML models
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
