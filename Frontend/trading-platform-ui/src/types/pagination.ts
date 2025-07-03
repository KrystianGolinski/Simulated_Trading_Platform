// Pagination interface for improved type safety and scalability

export interface PaginationInfo {
  page: number;
  page_size: number;
  total_count: number;
  total_pages: number;
  has_next: boolean;
  has_previous: boolean;
}

export interface PaginationRequest {
  page?: number;
  page_size?: number;
}

export interface PaginatedResponse<T> {
  data: T[];
  pagination: PaginationInfo;
}

export interface PaginationControls {
  currentPage: number;
  pageSize: number;
  totalCount: number;
  totalPages: number;
  hasNext: boolean;
  hasPrevious: boolean;
  onPageChange: (page: number) => void;
  onPageSizeChange: (pageSize: number) => void;
}

// Standard page size options for consistency across the application
export const PAGE_SIZE_OPTIONS = [10, 25, 50, 100, 250, 500] as const;
export type PageSizeOption = typeof PAGE_SIZE_OPTIONS[number];

// Default pagination configuration
export const DEFAULT_PAGINATION: Required<PaginationRequest> = {
  page: 1,
  page_size: 100,
};

// Utility functions for pagination
export class PaginationUtils {
  // Calculate offset from page and page size
  static calculateOffset(page: number, pageSize: number): number {
    return (page - 1) * pageSize;
  }

  // Calculate total pages from total count and page size
  static calculateTotalPages(totalCount: number, pageSize: number): number {
    return Math.ceil(totalCount / pageSize);
  }

  // Validate pagination parameters
  static validatePaginationRequest(request: PaginationRequest): {
    isValid: boolean;
    errors: string[];
    sanitized: Required<PaginationRequest>;
  } {
    const errors: string[] = [];
    const sanitized: Required<PaginationRequest> = {
      page: request.page ?? DEFAULT_PAGINATION.page,
      page_size: request.page_size ?? DEFAULT_PAGINATION.page_size,
    };

    // Validate page number
    if (sanitized.page < 1) {
      errors.push('Page number must be at least 1');
      sanitized.page = 1;
    }

    // Validate page size
    if (sanitized.page_size < 1) {
      errors.push('Page size must be at least 1');
      sanitized.page_size = DEFAULT_PAGINATION.page_size;
    }

    if (sanitized.page_size > 1000) {
      errors.push('Page size cannot exceed 1000');
      sanitized.page_size = 1000;
    }

    return {
      isValid: errors.length === 0,
      errors,
      sanitized,
    };
  }

  // Create pagination info from request and total count
  static createPaginationInfo(
    request: Required<PaginationRequest>,
    totalCount: number
  ): PaginationInfo {
    const totalPages = this.calculateTotalPages(totalCount, request.page_size);
    
    return {
      page: request.page,
      page_size: request.page_size,
      total_count: totalCount,
      total_pages: totalPages,
      has_next: request.page < totalPages,
      has_previous: request.page > 1,
    };
  }

  // Get page range for pagination controls (e.g., "1 2 3 ... 8 9 10")
  static getPageRange(
    currentPage: number,
    totalPages: number,
    maxVisible: number = 7
  ): (number | 'ellipsis')[] {
    if (totalPages <= maxVisible) {
      return Array.from({ length: totalPages }, (_, i) => i + 1);
    }

    const halfVisible = Math.floor(maxVisible / 2);
    let start = Math.max(1, currentPage - halfVisible);
    let end = Math.min(totalPages, start + maxVisible - 1);

    // Adjust start if we're near the end
    if (end - start < maxVisible - 1) {
      start = Math.max(1, end - maxVisible + 1);
    }

    const pages: (number | 'ellipsis')[] = [];

    // Add first page and ellipsis if needed
    if (start > 1) {
      pages.push(1);
      if (start > 2) {
        pages.push('ellipsis');
      }
    }

    // Add visible page range
    for (let i = start; i <= end; i++) {
      pages.push(i);
    }

    // Add ellipsis and last page if needed
    if (end < totalPages) {
      if (end < totalPages - 1) {
        pages.push('ellipsis');
      }
      pages.push(totalPages);
    }

    return pages;
  }
}

// Hook interface for pagination state management
export interface UsePaginationOptions {
  initialPage?: number;
  initialPageSize?: number;
  onPageChange?: (page: number) => void;
  onPageSizeChange?: (pageSize: number) => void;
}

export interface UsePaginationReturn {
  page: number;
  pageSize: number;
  setPage: (page: number) => void;
  setPageSize: (pageSize: number) => void;
  reset: () => void;
  createRequest: () => Required<PaginationRequest>;
}