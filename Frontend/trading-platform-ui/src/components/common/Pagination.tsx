import React from 'react';
import {
  PaginationInfo,
  PaginationUtils,
  PAGE_SIZE_OPTIONS,
} from '../../types/pagination';

interface PaginationProps {
  pagination: PaginationInfo;
  onPageChange: (page: number) => void;
  onPageSizeChange?: (pageSize: number) => void;
  showPageSize?: boolean;
  showInfo?: boolean;
  maxVisiblePages?: number;
  className?: string;
}

export const Pagination: React.FC<PaginationProps> = ({
  pagination,
  onPageChange,
  onPageSizeChange,
  showPageSize = true,
  showInfo = true,
  maxVisiblePages = 7,
  className = '',
}) => {
  const {
    page: currentPage,
    page_size: pageSize,
    total_count: totalCount,
    total_pages: totalPages,
    has_next: hasNext,
    has_previous: hasPrevious,
  } = pagination;

  const pageRange = PaginationUtils.getPageRange(currentPage, totalPages, maxVisiblePages);

  const handlePageClick = (page: number) => {
    if (page !== currentPage && page >= 1 && page <= totalPages) {
      onPageChange(page);
    }
  };

  const handlePageSizeChange = (newPageSize: number) => {
    if (onPageSizeChange && newPageSize !== pageSize) {
      onPageSizeChange(newPageSize);
    }
  };

  if (totalPages <= 1 && !showPageSize && !showInfo) {
    return null;
  }

  const startItem = totalCount === 0 ? 0 : (currentPage - 1) * pageSize + 1;
  const endItem = Math.min(currentPage * pageSize, totalCount);

  return (
    <div className={`flex flex-col sm:flex-row items-center justify-between gap-4 ${className}`}>
      {/* Page size selector */}
      {showPageSize && onPageSizeChange && (
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-600">Show:</span>
          <select
            value={pageSize}
            onChange={(e) => handlePageSizeChange(Number(e.target.value))}
            className="px-2 py-1 border border-gray-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            {PAGE_SIZE_OPTIONS.map((size) => (
              <option key={size} value={size}>
                {size}
              </option>
            ))}
          </select>
          <span className="text-sm text-gray-600">per page</span>
        </div>
      )}

      {/* Pagination info */}
      {showInfo && (
        <div className="text-sm text-gray-600">
          Showing {startItem.toLocaleString()} to {endItem.toLocaleString()} of{' '}
          {totalCount.toLocaleString()} results
        </div>
      )}

      {/* Page navigation */}
      {totalPages > 1 && (
        <div className="flex items-center gap-1">
          {/* Previous button */}
          <button
            onClick={() => handlePageClick(currentPage - 1)}
            disabled={!hasPrevious}
            className={`px-3 py-1 text-sm rounded transition-colors ${
              hasPrevious
                ? 'bg-gray-100 hover:bg-gray-200 text-gray-700'
                : 'bg-gray-50 text-gray-400 cursor-not-allowed'
            }`}
            aria-label="Previous page"
          >
            Previous
          </button>

          {/* Page numbers */}
          {pageRange.map((pageNum, index) => {
            if (pageNum === 'ellipsis') {
              return (
                <span key={`ellipsis-${index}`} className="px-2 py-1 text-gray-500">
                  ...
                </span>
              );
            }

            const isCurrentPage = pageNum === currentPage;
            return (
              <button
                key={pageNum}
                onClick={() => handlePageClick(pageNum)}
                className={`px-3 py-1 text-sm rounded transition-colors ${
                  isCurrentPage
                    ? 'bg-blue-500 text-white'
                    : 'bg-gray-100 hover:bg-gray-200 text-gray-700'
                }`}
                aria-label={`Page ${pageNum}`}
                aria-current={isCurrentPage ? 'page' : undefined}
              >
                {pageNum}
              </button>
            );
          })}

          {/* Next button */}
          <button
            onClick={() => handlePageClick(currentPage + 1)}
            disabled={!hasNext}
            className={`px-3 py-1 text-sm rounded transition-colors ${
              hasNext
                ? 'bg-gray-100 hover:bg-gray-200 text-gray-700'
                : 'bg-gray-50 text-gray-400 cursor-not-allowed'
            }`}
            aria-label="Next page"
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
};