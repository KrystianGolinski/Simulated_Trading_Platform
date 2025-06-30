import { useState, useCallback } from 'react';
import {
  UsePaginationOptions,
  UsePaginationReturn,
  DEFAULT_PAGINATION,
  PaginationRequest,
} from '../types/pagination';

// Custom hook for managing pagination state
export function usePagination(options: UsePaginationOptions = {}): UsePaginationReturn {
  const {
    initialPage = DEFAULT_PAGINATION.page,
    initialPageSize = DEFAULT_PAGINATION.page_size,
    onPageChange,
    onPageSizeChange,
  } = options;

  const [page, setPageState] = useState(initialPage);
  const [pageSize, setPageSizeState] = useState(initialPageSize);

  const setPage = useCallback(
    (newPage: number) => {
      setPageState(newPage);
      onPageChange?.(newPage);
    },
    [onPageChange]
  );

  const setPageSize = useCallback(
    (newPageSize: number) => {
      setPageSizeState(newPageSize);
      // Reset to first page when page size changes
      setPageState(1);
      onPageSizeChange?.(newPageSize);
      onPageChange?.(1);
    },
    [onPageChange, onPageSizeChange]
  );

  const reset = useCallback(() => {
    setPageState(initialPage);
    setPageSizeState(initialPageSize);
    onPageChange?.(initialPage);
  }, [initialPage, initialPageSize, onPageChange]);

  const createRequest = useCallback((): Required<PaginationRequest> => ({
    page,
    page_size: pageSize,
  }), [page, pageSize]);

  return {
    page,
    pageSize,
    setPage,
    setPageSize,
    reset,
    createRequest,
  };
}