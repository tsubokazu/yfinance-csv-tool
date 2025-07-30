'use client';

import { useState, useEffect, useRef } from 'react';
import { Search, X, TrendingUp, Building2 } from 'lucide-react';

interface SearchSuggestion {
  symbol: string;
  name: string;
  sector: string;
  market: 'JP' | 'US';
}

// 検索候補データ
const searchSuggestions: SearchSuggestion[] = [
  // 日本株
  { symbol: '6723.T', name: 'ルネサス エレクトロニクス', sector: '半導体', market: 'JP' },
  { symbol: '7203.T', name: 'トヨタ自動車', sector: '自動車', market: 'JP' },
  { symbol: '6758.T', name: 'ソニーグループ', sector: 'エレクトロニクス', market: 'JP' },
  { symbol: '9984.T', name: 'ソフトバンクグループ', sector: '通信', market: 'JP' },
  { symbol: '8306.T', name: '三菱UFJフィナンシャル・グループ', sector: '金融', market: 'JP' },
  { symbol: '4689.T', name: 'Zホールディングス', sector: 'IT', market: 'JP' },
  { symbol: '6954.T', name: 'ファナック', sector: '機械', market: 'JP' },
  { symbol: '4063.T', name: '信越化学工業', sector: '化学', market: 'JP' },
  { symbol: '6981.T', name: '村田製作所', sector: '電子部品', market: 'JP' },
  { symbol: '9432.T', name: '日本電信電話', sector: '通信', market: 'JP' },
  { symbol: '7974.T', name: '任天堂', sector: 'ゲーム', market: 'JP' },
  { symbol: '6098.T', name: 'リクルートホールディングス', sector: 'サービス', market: 'JP' },
  { symbol: '4568.T', name: '第一三共', sector: '医薬品', market: 'JP' },
  { symbol: '8035.T', name: '東京エレクトロン', sector: '半導体製造装置', market: 'JP' },
  { symbol: '9983.T', name: 'ファーストリテイリング', sector: '小売', market: 'JP' },
  
  // 米国株
  { symbol: 'AAPL', name: 'Apple Inc.', sector: 'Technology', market: 'US' },
  { symbol: 'MSFT', name: 'Microsoft Corporation', sector: 'Technology', market: 'US' },
  { symbol: 'GOOGL', name: 'Alphabet Inc.', sector: 'Technology', market: 'US' },
  { symbol: 'AMZN', name: 'Amazon.com Inc.', sector: 'E-commerce', market: 'US' },
  { symbol: 'TSLA', name: 'Tesla Inc.', sector: 'Automotive', market: 'US' },
  { symbol: 'NVDA', name: 'NVIDIA Corporation', sector: 'Semiconductors', market: 'US' },
  { symbol: 'META', name: 'Meta Platforms Inc.', sector: 'Social Media', market: 'US' },
  { symbol: 'NFLX', name: 'Netflix Inc.', sector: 'Entertainment', market: 'US' },
  { symbol: 'CRM', name: 'Salesforce Inc.', sector: 'Software', market: 'US' },
  { symbol: 'ADBE', name: 'Adobe Inc.', sector: 'Software', market: 'US' },
];

interface SymbolSearchInputProps {
  value: string;
  onChange: (value: string) => void;
  onSelect: (symbol: string) => void;
  placeholder?: string;
  disabled?: boolean;
  loading?: boolean;
}

export function SymbolSearchInput({
  value,
  onChange,
  onSelect,
  placeholder = "銘柄コードまたは銘柄名を入力 (例: 6723.T, AAPL)",
  disabled = false,
  loading = false
}: SymbolSearchInputProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [filteredSuggestions, setFilteredSuggestions] = useState<SearchSuggestion[]>([]);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const inputRef = useRef<HTMLInputElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // 検索フィルタリング
  useEffect(() => {
    if (value.length >= 1) {
      const searchTerm = value.toLowerCase();
      const filtered = searchSuggestions.filter(
        (suggestion) =>
          suggestion.symbol.toLowerCase().includes(searchTerm) ||
          suggestion.name.toLowerCase().includes(searchTerm) ||
          suggestion.sector.toLowerCase().includes(searchTerm)
      ).slice(0, 8); // 最大8件まで表示

      setFilteredSuggestions(filtered);
      setIsOpen(filtered.length > 0);
      setSelectedIndex(-1);
    } else {
      setFilteredSuggestions([]);
      setIsOpen(false);
    }
  }, [value]);

  // クリック外しでドロップダウンを閉じる
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node) &&
        !inputRef.current?.contains(event.target as Node)
      ) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // キーボード操作
  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (!isOpen || filteredSuggestions.length === 0) {
      if (e.key === 'Enter' && value) {
        onSelect(value);
        setIsOpen(false);
      }
      return;
    }

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setSelectedIndex(prev => 
          prev < filteredSuggestions.length - 1 ? prev + 1 : prev
        );
        break;
      case 'ArrowUp':
        e.preventDefault();
        setSelectedIndex(prev => prev > 0 ? prev - 1 : -1);
        break;
      case 'Enter':
        e.preventDefault();
        if (selectedIndex >= 0) {
          const selectedSuggestion = filteredSuggestions[selectedIndex];
          onChange(selectedSuggestion.symbol);
          onSelect(selectedSuggestion.symbol);
          setIsOpen(false);
        } else if (value) {
          onSelect(value);
          setIsOpen(false);
        }
        break;
      case 'Escape':
        setIsOpen(false);
        setSelectedIndex(-1);
        break;
    }
  };

  // 候補選択
  const handleSuggestionClick = (suggestion: SearchSuggestion) => {
    onChange(suggestion.symbol);
    onSelect(suggestion.symbol);
    setIsOpen(false);
  };

  // クリア
  const handleClear = () => {
    onChange('');
    setIsOpen(false);
    inputRef.current?.focus();
  };

  return (
    <div className="relative">
      {/* 検索入力 */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
        <input
          ref={inputRef}
          type="text"
          placeholder={placeholder}
          className="w-full pl-10 pr-10 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={disabled}
        />
        
        {/* ローディング・クリアボタン */}
        <div className="absolute right-3 top-1/2 transform -translate-y-1/2 flex items-center space-x-2">
          {loading && (
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600" />
          )}
          {value && !loading && (
            <button
              onClick={handleClear}
              className="text-gray-400 hover:text-gray-600"
            >
              <X className="h-4 w-4" />
            </button>
          )}
        </div>
      </div>

      {/* ドロップダウン候補 */}
      {isOpen && filteredSuggestions.length > 0 && (
        <div
          ref={dropdownRef}
          className="absolute top-full left-0 right-0 mt-1 bg-white border border-gray-200 rounded-lg shadow-lg z-50 max-h-64 overflow-y-auto"
        >
          {filteredSuggestions.map((suggestion, index) => (
            <button
              key={suggestion.symbol}
              onClick={() => handleSuggestionClick(suggestion)}
              className={`w-full text-left px-4 py-3 hover:bg-gray-50 border-b border-gray-100 last:border-b-0 ${
                index === selectedIndex ? 'bg-blue-50 border-blue-100' : ''
              }`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <Building2 className="h-4 w-4 text-gray-400" />
                  <div>
                    <div className="flex items-center space-x-2">
                      <span className="font-medium text-gray-900">
                        {suggestion.symbol}
                      </span>
                      <span className={`text-xs px-2 py-1 rounded ${
                        suggestion.market === 'JP' 
                          ? 'bg-red-100 text-red-700' 
                          : 'bg-blue-100 text-blue-700'
                      }`}>
                        {suggestion.market}
                      </span>
                      <span className="text-xs px-2 py-1 bg-gray-100 text-gray-600 rounded">
                        {suggestion.sector}
                      </span>
                    </div>
                    <p className="text-sm text-gray-600 mt-1">{suggestion.name}</p>
                  </div>
                </div>
                <TrendingUp className="h-4 w-4 text-gray-300" />
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}