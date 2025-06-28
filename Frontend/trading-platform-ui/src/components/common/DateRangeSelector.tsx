import React, { useState, useEffect } from 'react';
import { Button } from './Button';
import { Card } from './Card';
import { apiService } from '../../services/api';

interface DateRange {
  min_date: string;
  max_date: string;
}

interface DateRangeSelectorProps {
  startDate: string;
  endDate: string;
  onStartDateChange: (date: string) => void;
  onEndDateChange: (date: string) => void;
  title?: string;
  variant?: 'compact' | 'card';
  className?: string;
  symbol?: string; // Optional symbol to fetch specific date range
  autoSetDatesOnSymbolChange?: boolean; // Automatically set dates when symbol date range is loaded
}

export const DateRangeSelector: React.FC<DateRangeSelectorProps> = ({
  startDate,
  endDate,
  onStartDateChange,
  onEndDateChange,
  title = 'Date Range',
  variant = 'compact',
  className = '',
  symbol,
  autoSetDatesOnSymbolChange = false
}) => {
  const [dateRange, setDateRange] = useState<DateRange>({
    min_date: '2015-06-17',
    max_date: '2025-06-13'
  });
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    const fetchDateRange = async () => {
      if (!symbol) {
        // No symbol provided, clear constraints and dates if auto-setting is enabled
        setDateRange({ min_date: '', max_date: '' });
        if (autoSetDatesOnSymbolChange) {
          onStartDateChange('');
          onEndDateChange('');
        }
        return;
      }

      try {
        setIsLoading(true);
        const range = await apiService.getStockDateRange(symbol);
        setDateRange(range);
        
        // Optionally auto-set dates when range is loaded
        if (autoSetDatesOnSymbolChange) {
          onStartDateChange(range.min_date);
          onEndDateChange(range.max_date);
        }
      } catch (error) {
        console.error(`Failed to fetch date range for ${symbol}:`, error);
        // Clear constraints on error to allow any date input
        setDateRange({ min_date: '', max_date: '' });
      } finally {
        setIsLoading(false);
      }
    };

    fetchDateRange();
  }, [symbol]);

  const handleEarliestClick = () => {
    if (dateRange.min_date) {
      onStartDateChange(dateRange.min_date);
    }
  };

  const handleLatestClick = () => {
    if (dateRange.max_date) {
      onEndDateChange(dateRange.max_date);
    }
  };

  const renderDateInput = (
    label: string,
    value: string,
    onChange: (date: string) => void,
    shortcutLabel: string,
    onShortcut: () => void
  ) => {
    const showPlaceholder = !symbol && !value;
    
    if (variant === 'card') {
      return (
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <label style={{ fontSize: '0.875rem', fontWeight: '500', color: '#374151', width: '140px', textAlign: 'left' }}>
            {label}
          </label>
          <input
            type={showPlaceholder ? "text" : "date"}
            value={showPlaceholder ? "No stock chosen" : value}
            onChange={showPlaceholder ? undefined : (e) => onChange(e.target.value)}
            min={showPlaceholder ? undefined : (dateRange.min_date || undefined)}
            max={showPlaceholder ? undefined : (dateRange.max_date || undefined)}
            readOnly={showPlaceholder}
            disabled={isLoading}
            style={{
              padding: '8px 12px',
              border: '1px solid #d1d5db',
              borderRadius: '6px',
              fontSize: '14px',
              width: '200px',
              color: showPlaceholder ? '#9ca3af' : '#374151',
              backgroundColor: showPlaceholder ? '#f9fafb' : '#ffffff',
              textAlign: showPlaceholder ? 'center' : 'left',
              cursor: showPlaceholder ? 'default' : 'text'
            }}
          />
          <Button
            type="button"
            onClick={onShortcut}
            variant="secondary"
            style={{ fontSize: '0.75rem', padding: '4px 8px', width: '60px', textAlign: 'center' }}
            disabled={isLoading || !dateRange.min_date || !dateRange.max_date}
          >
            {shortcutLabel}
          </Button>
        </div>
      );
    }

    return (
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        <label style={{ fontSize: '13px', fontWeight: '500', color: '#374151', minWidth: '130px' }}>
          {label}
        </label>
        <input
          type={showPlaceholder ? "text" : "date"}
          value={showPlaceholder ? "No stock chosen" : value}
          onChange={showPlaceholder ? undefined : (e) => onChange(e.target.value)}
          min={showPlaceholder ? undefined : (dateRange.min_date || undefined)}
          max={showPlaceholder ? undefined : (dateRange.max_date || undefined)}
          readOnly={showPlaceholder}
          disabled={isLoading}
          style={{
            padding: '6px 10px',
            border: '1px solid #d1d5db',
            borderRadius: '4px',
            fontSize: '13px',
            outline: 'none',
            width: '140px',
            color: showPlaceholder ? '#9ca3af' : '#374151',
            backgroundColor: showPlaceholder ? '#f9fafb' : '#ffffff',
            textAlign: showPlaceholder ? 'center' : 'left',
            cursor: showPlaceholder ? 'default' : 'text',
            opacity: isLoading ? 0.5 : 1
          }}
        />
        <button
          type="button"
          onClick={onShortcut}
          disabled={isLoading || !dateRange.min_date || !dateRange.max_date}
          style={{
            padding: '4px 8px',
            fontSize: '12px',
            backgroundColor: (isLoading || !dateRange.min_date || !dateRange.max_date) ? '#9ca3af' : '#6b7280',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: (isLoading || !dateRange.min_date || !dateRange.max_date) ? 'not-allowed' : 'pointer',
            width: '60px',
            textAlign: 'center'
          }}
        >
          {shortcutLabel}
        </button>
      </div>
    );
  };

  const content = (
    <div style={{ display: 'flex', flexDirection: 'column', gap: variant === 'card' ? '0.25rem' : '12px' }}>
      {renderDateInput('Start Date', startDate, onStartDateChange, 'Earliest', handleEarliestClick)}
      {renderDateInput('End Date', endDate, onEndDateChange, 'Latest', handleLatestClick)}
    </div>
  );

  if (variant === 'card') {
    return (
      <div className={className} style={{ marginBottom: '1.5rem' }}>
        <h2 style={{ fontSize: '1.1rem', fontWeight: '600', marginBottom: '0.5rem', color: '#374151' }}>
          {title}
        </h2>
        <Card>
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.25rem', padding: '0' }}>
            {content}
          </div>
        </Card>
      </div>
    );
  }

  return (
    <div className={className}>
      {content}
    </div>
  );
};