import { useState } from 'react';
import { useToast } from '../components/Toast';

interface MarketplaceItem {
  id: number;
  name: string;
  description: string;
  category: string;
  author: string;
  price: string;
  rating: number;
  installs: number;
  icon: JSX.Element;
}

const marketplaceItems: MarketplaceItem[] = [
  {
    id: 1,
    name: 'Research Pro',
    description: 'Advanced web research agent that scours the internet for accurate, up-to-date information and compiles comprehensive reports.',
    category: 'Research',
    author: 'MultiAgent Labs',
    price: 'Free',
    rating: 4.8,
    installs: 1240,
    icon: (
      <svg className="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" />
      </svg>
    ),
  },
  {
    id: 2,
    name: 'Code Reviewer',
    description: 'Automated code review agent that analyzes pull requests, identifies bugs, and suggests improvements across multiple languages.',
    category: 'Coding',
    author: 'DevTools Inc',
    price: '$29/mo',
    rating: 4.6,
    installs: 892,
    icon: (
      <svg className="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M17.25 6.75L22.5 12l-5.25 5.25m-10.5 0L1.5 12l5.25-5.25m7.5-3l-4.5 16.5" />
      </svg>
    ),
  },
  {
    id: 3,
    name: 'Content Writer',
    description: 'Professional blog and article writing agent that creates engaging content tailored to your audience and SEO requirements.',
    category: 'Writing',
    author: 'ContentAI',
    price: 'Free',
    rating: 4.5,
    installs: 2105,
    icon: (
      <svg className="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0115.75 21H5.25A2.25 2.25 0 013 18.75V8.25A2.25 2.25 0 015.25 6H10" />
      </svg>
    ),
  },
  {
    id: 4,
    name: 'Data Analyst',
    description: 'Advanced data analysis and visualization agent that processes datasets and generates insightful charts and dashboards.',
    category: 'Analysis',
    author: 'DataWise',
    price: '$49/mo',
    rating: 4.7,
    installs: 756,
    icon: (
      <svg className="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" />
      </svg>
    ),
  },
  {
    id: 5,
    name: 'Customer Support',
    description: 'Intelligent customer service agent that handles inquiries, resolves issues, and escalates complex problems to human agents.',
    category: 'Custom',
    author: 'SupportAI',
    price: '$99/mo',
    rating: 4.4,
    installs: 543,
    icon: (
      <svg className="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M20.25 8.511c.884.284 1.5 1.128 1.5 2.097v4.286c0 1.136-.847 2.1-1.98 2.193-.34.027-.68.052-1.02.072v3.091l-3-3c-1.354 0-2.694-.055-4.02-.163a2.115 2.115 0 01-.825-.242m9.345-8.334a2.126 2.126 0 00-.476-.095 48.64 48.64 0 00-8.048 0c-1.131.094-1.976 1.057-1.976 2.192v4.286c0 .837.46 1.58 1.155 1.951m9.345-8.334V6.637c0-1.621-1.152-3.026-2.76-3.235A48.455 48.455 0 0011.25 3c-2.115 0-4.198.137-6.24.402-1.608.209-2.76 1.614-2.76 3.235v6.226c0 1.621 1.152 3.026 2.76 3.235.577.075 1.157.14 1.74.194V21l4.155-4.155" />
      </svg>
    ),
  },
  {
    id: 6,
    name: 'SEO Optimizer',
    description: 'Search engine optimization agent that analyzes content, suggests keywords, and optimizes pages for better search rankings.',
    category: 'Analysis',
    author: 'RankBoost',
    price: '$19/mo',
    rating: 4.3,
    installs: 1340,
    icon: (
      <svg className="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 21a9.004 9.004 0 008.716-6.747M12 21a9.004 9.004 0 01-8.716-6.747M12 21c2.485 0 4.5-4.03 4.5-9S14.485 3 12 3m0 18c-2.485 0-4.5-4.03-4.5-9S9.515 3 12 3m0 0a8.997 8.997 0 017.843 4.582M12 3a8.997 8.997 0 00-7.843 4.582m15.686 0A11.953 11.953 0 0112 10.5c-2.998 0-5.74-1.1-7.843-2.918m15.686 0A8.959 8.959 0 0121 12c0 .778-.099 1.533-.284 2.253m0 0A17.919 17.919 0 0112 16.5c-3.162 0-6.133-.815-8.716-2.247m0 0A9.015 9.015 0 013 12c0-1.605.42-3.113 1.157-4.418" />
      </svg>
    ),
  },
];

const categories = ['All', 'Research', 'Writing', 'Coding', 'Analysis', 'Custom'];

export function Marketplace() {
  const [search, setSearch] = useState('');
  const [activeCategory, setActiveCategory] = useState('All');
  const [installedIds, setInstalledIds] = useState<number[]>([]);
  const { toast } = useToast();

  const filtered = marketplaceItems.filter((item) => {
    const matchesSearch = item.name.toLowerCase().includes(search.toLowerCase()) ||
      item.description.toLowerCase().includes(search.toLowerCase());
    const matchesCategory = activeCategory === 'All' || item.category === activeCategory;
    return matchesSearch && matchesCategory;
  });

  const handleInstall = (item: MarketplaceItem) => {
    if (installedIds.includes(item.id)) return;
    setInstalledIds([...installedIds, item.id]);
    toast('success', `${item.name} installed successfully`);
  };

  const renderStars = (rating: number) => {
    return (
      <div className="flex items-center gap-0.5">
        {[1, 2, 3, 4, 5].map((star) => (
          <svg
            key={star}
            className={`w-3.5 h-3.5 ${star <= Math.floor(rating) ? 'text-amber-400' : 'text-gray-600'}`}
            fill="currentColor"
            viewBox="0 0 20 20"
          >
            <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
          </svg>
        ))}
        <span className="text-xs text-gray-400 ml-1">{rating}</span>
      </div>
    );
  };

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold">Agent Marketplace</h1>
        <p className="text-gray-400">Discover and install pre-built agents for your platform</p>
      </div>

      {/* Search */}
      <div className="relative max-w-xl">
        <svg className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" />
        </svg>
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search marketplace..."
          className="input pl-12"
        />
      </div>

      {/* Category Filters */}
      <div className="flex flex-wrap gap-2">
        {categories.map((cat) => (
          <button
            key={cat}
            onClick={() => setActiveCategory(cat)}
            className={`px-4 py-2 rounded-xl text-sm font-medium transition-all ${
              activeCategory === cat
                ? 'bg-gradient-to-r from-[#6366f1] to-[#8b5cf6] text-white'
                : 'bg-white/5 text-gray-400 hover:text-white hover:bg-white/10 border border-white/5'
            }`}
          >
            {cat}
          </button>
        ))}
      </div>

      {/* Grid */}
      {filtered.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-16 text-center">
          <div className="w-20 h-20 rounded-2xl bg-white/5 border border-white/10 flex items-center justify-center mb-6 text-gray-400">
            <svg className="w-10 h-10" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" />
            </svg>
          </div>
          <h3 className="text-xl font-semibold mb-2">No agents found</h3>
          <p className="text-gray-400 max-w-md">Try adjusting your search or filter criteria</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {filtered.map((item) => (
            <div
              key={item.id}
              className="card group hover:border-indigo-500/30 transition-all duration-300"
            >
              {/* Card Header */}
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-[#6366f1]/20 to-[#8b5cf6]/20 flex items-center justify-center text-[#8b5cf6] group-hover:scale-110 transition-transform">
                    {item.icon}
                  </div>
                  <div>
                    <h3 className="font-semibold">{item.name}</h3>
                    <p className="text-xs text-gray-500">{item.author}</p>
                  </div>
                </div>
                <span className="px-2.5 py-1 text-xs rounded-full font-medium bg-white/5 text-gray-300 border border-white/10">
                  {item.category}
                </span>
              </div>

              <p className="text-sm text-gray-400 mb-4 line-clamp-2">
                {item.description}
              </p>

              {/* Rating & Installs */}
              <div className="flex items-center justify-between mb-4">
                {renderStars(item.rating)}
                <div className="flex items-center gap-1 text-xs text-gray-500">
                  <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" />
                  </svg>
                  {item.installs.toLocaleString()} installs
                </div>
              </div>

              {/* Footer */}
              <div className="flex items-center justify-between pt-4 border-t border-white/5">
                <span className={`text-sm font-semibold ${
                  item.price === 'Free' ? 'text-emerald-400' : 'text-gray-200'
                }`}>
                  {item.price}
                </span>
                <button
                  onClick={() => handleInstall(item)}
                  disabled={installedIds.includes(item.id)}
                  className={`px-4 py-2 rounded-xl text-sm font-medium transition-all ${
                    installedIds.includes(item.id)
                      ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 cursor-default'
                      : 'bg-gradient-to-r from-[#6366f1] to-[#8b5cf6] text-white hover:opacity-90'
                  }`}
                >
                  {installedIds.includes(item.id) ? 'Installed' : 'Install'}
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
