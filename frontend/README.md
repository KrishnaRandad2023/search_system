# Flipkart Search Frontend

A modern, responsive Next.js frontend for the Flipkart Grid 7.0 Advanced Search System, featuring intelligent autosuggest, semantic search, and ML-powered product ranking.

## 🚀 Features

- **Intelligent Autosuggest**: Real-time search suggestions with typo tolerance
- **Advanced Search Results**: ML-powered product ranking and filtering
- **Professional UI**: Flipkart-inspired design with modern UX patterns
- **Responsive Design**: Mobile-first approach with Tailwind CSS
- **Fast Performance**: Sub-100ms autosuggest, optimized rendering
- **TypeScript**: Full type safety and excellent developer experience

## 🛠️ Tech Stack

- **Framework**: Next.js 15 with App Router
- **Language**: TypeScript
- **Styling**: Tailwind CSS with custom Flipkart theme
- **API Client**: Custom fetch-based client with error handling
- **State Management**: React Hooks (useState, useEffect)
- **Icons**: Heroicons via SVG

## 📦 Project Structure

```
frontend/
├── app/                    # Next.js App Router pages
│   ├── layout.tsx         # Root layout with theme setup
│   ├── page.tsx           # Home page with categories
│   └── search/
│       └── page.tsx       # Search results page
├── components/            # Reusable UI components
│   ├── ui/
│   │   └── Header.tsx     # Main navigation with autosuggest
│   └── search/
│       └── ProductCard.tsx # Product display component
├── lib/                   # Utility libraries
│   └── api.ts            # API client and type definitions
└── public/               # Static assets
```

## 🚦 Getting Started

### Prerequisites

- Node.js 18+
- npm or yarn
- FastAPI backend running on port 8002

### Installation

1. **Clone and navigate to frontend directory**:

   ```bash
   cd frontend
   ```

2. **Install dependencies**:

   ```bash
   npm install
   ```

3. **Set up environment variables**:

   ```bash
   # Create .env.local file
   NEXT_PUBLIC_API_URL=http://localhost:8002
   ```

4. **Start development server**:

   ```bash
   npm run dev
   ```

5. **Open in browser**:
   ```
   http://localhost:3000
   ```

## 🎯 Core Components

### Header Component

- Intelligent search bar with autosuggest
- Popular queries and trending suggestions
- Category navigation
- Responsive design with mobile support

### Product Card Component

- Professional product display
- Rating and price information
- Availability status
- Click tracking for analytics
- Hover effects and animations

### Search Results Page

- Advanced filtering and sorting
- Pagination with performance optimization
- Error handling and loading states
- SEO-friendly URLs and metadata

## 🔌 API Integration

The frontend integrates with the FastAPI backend through a custom API client:

```typescript
// Example usage
const suggestions = await apiClient.getAutosuggest("laptop", 10);
const results = await apiClient.search("smartphone", filters, page);
await apiClient.trackClick({ query, product_id, position });
```

### API Features

- Automatic error handling and retry logic
- TypeScript types for all responses
- Request/response logging in development
- Performance monitoring and analytics

## 🎨 Design System

### Colors

- **Primary Blue**: #2874f0 (Flipkart brand color)
- **Secondary Orange**: #ff6161 (Accent color)
- **Success Green**: #388e3c (Positive actions)
- **Warning Yellow**: #ff9f00 (Alerts)

### Typography

- **Font**: Inter (modern, readable web font)
- **Hierarchy**: Clear heading and body text scales
- **Weights**: 400 (regular), 500 (medium), 600 (semibold), 700 (bold)

### Components

- Consistent spacing using Tailwind's scale
- Professional shadows and hover effects
- Accessible color contrasts and focus states
- Mobile-first responsive breakpoints

## 📱 Responsive Design

- **Mobile**: 320px - 767px (single column, touch-optimized)
- **Tablet**: 768px - 1023px (2-column grid, hybrid navigation)
- **Desktop**: 1024px+ (multi-column, full feature set)

## ⚡ Performance Features

- **Next.js Optimizations**: Automatic code splitting and SSR
- **Image Optimization**: Next.js Image component with lazy loading
- **Bundle Analysis**: Webpack bundle analyzer for size optimization
- **Caching Strategy**: API response caching and request deduplication

## 🔧 Development Commands

```bash
# Development server with hot reload
npm run dev

# Production build
npm run build

# Start production server
npm start

# TypeScript type checking
npm run type-check

# Linting with ESLint
npm run lint

# Format code with Prettier
npm run format
```

## 🌐 Environment Configuration

### Development (.env.local)

```bash
NEXT_PUBLIC_API_URL=http://localhost:8002
NEXT_PUBLIC_APP_NAME=Flipkart Search
NEXT_PUBLIC_APP_VERSION=1.0.0
```

### Production

```bash
NEXT_PUBLIC_API_URL=https://api.flipkart-search.com
NEXT_PUBLIC_APP_NAME=Flipkart Search
NEXT_PUBLIC_APP_VERSION=1.0.0
```

## 🚀 Deployment

### Vercel (Recommended)

```bash
# Deploy to Vercel
npm run build
npx vercel --prod
```

### Docker

```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["npm", "start"]
```

## 🧪 Features Showcase

### Landing Page

- Hero section with feature highlights
- Category grid with icons and descriptions
- Trending categories with progress indicators
- Popular search queries
- Feature explanations with benefits

### Search Results

- Real-time filtering and sorting
- Advanced pagination
- Product cards with rich information
- Loading states and error handling
- SEO-optimized URLs

### Autosuggest

- Sub-100ms response time
- Typo tolerance and correction
- Category-based suggestions
- Popular and trending queries
- Keyboard navigation support

## 🎯 Future Enhancements

- **Voice Search**: Speech-to-text integration
- **Visual Search**: Image-based product search
- **Personalization**: User preference learning
- **A/B Testing**: Feature experimentation
- **PWA Support**: Offline functionality
- **Analytics Dashboard**: Search insights

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is part of the Flipkart Grid 7.0 submission and is for demonstration purposes.

---

**Built with ❤️ for Flipkart Grid 7.0**

_Demonstrating next-generation e-commerce search capabilities with modern web technologies_
