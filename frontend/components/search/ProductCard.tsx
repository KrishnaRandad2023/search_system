"use client";

import { useState } from "react";
import { ProductResult, apiClient, formatPrice, formatRating } from "@/lib/api";

interface ProductCardProps {
  product: ProductResult;
  position: number;
  query: string;
  onProductClick?: (product: ProductResult) => void;
}

export default function ProductCard({
  product,
  position,
  query,
  onProductClick,
}: ProductCardProps) {
  const [imageError, setImageError] = useState(false);
  const [imageLoading, setImageLoading] = useState(true);

  const handleClick = async () => {
    // Track click for analytics
    try {
      await apiClient.trackClick({
        query,
        product_id: product.id,
        position,
      });
    } catch (error) {
      console.error("Failed to track click:", error);
    }

    // Call external click handler
    if (onProductClick) {
      onProductClick(product);
    }
  };

  const handleImageLoad = () => {
    setImageLoading(false);
  };

  const handleImageError = () => {
    setImageError(true);
    setImageLoading(false);
  };

  const getRatingColor = (rating: number) => {
    if (rating >= 4.0) return "bg-green-600";
    if (rating >= 3.0) return "bg-yellow-500";
    return "bg-orange-500";
  };

  const getAvailabilityStatus = (availability: string) => {
    switch (availability.toLowerCase()) {
      case "in_stock":
        return { text: "In Stock", color: "text-green-600" };
      case "low_stock":
        return { text: "Only few left", color: "text-orange-600" };
      case "out_of_stock":
        return { text: "Out of Stock", color: "text-red-600" };
      default:
        return { text: availability, color: "text-gray-600" };
    }
  };

  const availabilityStatus = getAvailabilityStatus(product.availability);

  return (
    <div
      onClick={handleClick}
      className="bg-white border border-gray-200 rounded-lg shadow-sm hover:shadow-md transition-all duration-200 cursor-pointer group card-shadow hover:card-shadow-hover"
    >
      {/* Product Image */}
      <div className="relative aspect-square overflow-hidden rounded-t-lg bg-gray-100">
        {!imageError ? (
          <>
            {imageLoading && (
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="animate-spin h-8 w-8 border-2 border-blue-600 border-t-transparent rounded-full"></div>
              </div>
            )}
            <img
              src={product.image_url || "/api/placeholder/300/300"}
              alt={product.title}
              className={`w-full h-full object-cover group-hover:scale-105 transition-transform duration-300 ${
                imageLoading ? "opacity-0" : "opacity-100"
              }`}
              onLoad={handleImageLoad}
              onError={handleImageError}
            />
          </>
        ) : (
          <div className="w-full h-full flex items-center justify-center bg-gray-100 text-gray-400">
            <svg className="w-16 h-16" fill="currentColor" viewBox="0 0 20 20">
              <path
                fillRule="evenodd"
                d="M4 3a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V5a2 2 0 00-2-2H4zm12 12H4l4-8 3 6 2-4 3 6z"
                clipRule="evenodd"
              />
            </svg>
          </div>
        )}

        {/* Wishlist Button */}
        <button
          onClick={(e) => {
            e.stopPropagation();
            // Handle wishlist toggle
          }}
          className="absolute top-2 right-2 p-2 bg-white rounded-full shadow-md opacity-0 group-hover:opacity-100 transition-opacity duration-200 hover:bg-gray-50"
        >
          <svg
            className="w-4 h-4 text-gray-600 hover:text-red-500 transition-colors"
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

        {/* Discount Badge */}
        {product.specifications?.discount_percentage && (
          <div className="absolute top-2 left-2 bg-green-600 text-white text-xs font-medium px-2 py-1 rounded">
            {product.specifications.discount_percentage}% OFF
          </div>
        )}
      </div>

      {/* Product Details */}
      <div className="p-4">
        {/* Brand */}
        {product.brand && (
          <div className="text-xs text-gray-500 uppercase tracking-wide mb-1">
            {product.brand}
          </div>
        )}

        {/* Title */}
        <h3 className="text-sm font-medium text-gray-900 line-clamp-2 mb-2 group-hover:text-blue-600 transition-colors">
          {product.title}
        </h3>

        {/* Rating */}
        <div className="flex items-center space-x-2 mb-2">
          <div
            className={`flex items-center space-x-1 px-2 py-1 rounded text-white text-xs font-medium ${getRatingColor(
              product.rating
            )}`}
          >
            <span>{formatRating(product.rating)}</span>
            <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
              <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
            </svg>
          </div>
          <span className="text-xs text-gray-500">
            ({product.num_ratings?.toLocaleString() || "0"})
          </span>
        </div>

        {/* Price */}
        <div className="flex items-center space-x-2 mb-2">
          <span className="text-lg font-semibold text-gray-900">
            {formatPrice(product.current_price)}
          </span>
          {product.original_price &&
            product.original_price > product.current_price && (
              <span className="text-sm text-gray-500 line-through">
                {formatPrice(product.original_price)}
              </span>
            )}
        </div>

        {/* Availability */}
        <div className={`text-xs font-medium mb-3 ${availabilityStatus.color}`}>
          {availabilityStatus.text}
        </div>

        {/* Features */}
        {product.features && product.features.length > 0 && (
          <div className="mb-3">
            <ul className="text-xs text-gray-600 space-y-1">
              {product.features.slice(0, 2).map((feature, index) => (
                <li key={index} className="flex items-start">
                  <span className="text-green-500 mr-1">•</span>
                  <span className="line-clamp-1">{feature}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Quick Actions */}
        <div className="flex space-x-2">
          <button
            onClick={(e) => {
              e.stopPropagation();
              // Handle add to cart
            }}
            className="flex-1 bg-blue-600 text-white text-sm font-medium py-2 px-3 rounded hover:bg-blue-700 transition-colors"
            disabled={product.availability === "out_of_stock"}
          >
            Add to Cart
          </button>
          <button
            onClick={(e) => {
              e.stopPropagation();
              // Handle buy now
            }}
            className="flex-1 bg-orange-500 text-white text-sm font-medium py-2 px-3 rounded hover:bg-orange-600 transition-colors"
            disabled={product.availability === "out_of_stock"}
          >
            Buy Now
          </button>
        </div>

        {/* Scoring Debug Info (Only in development) */}
        {process.env.NODE_ENV === "development" && (
          <div className="mt-3 pt-3 border-t border-gray-100">
            <div className="text-xs text-gray-400 space-y-1">
              <div>Relevance: {product.relevance_score.toFixed(2)}</div>
              <div>Business: {product.business_score.toFixed(2)}</div>
              <div>Final: {product.final_score.toFixed(2)}</div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
