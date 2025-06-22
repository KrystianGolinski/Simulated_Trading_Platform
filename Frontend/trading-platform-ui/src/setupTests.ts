
// Import polyfills first
import './jest.polyfills.js';

import '@testing-library/jest-dom';
import { beforeAll, afterEach, afterAll } from '@jest/globals';
import { server } from './__mocks__/server';

// Global test configuration

// Establish API mocking before all tests
beforeAll(() => server.listen({ onUnhandledRequest: 'warn' }));

// Reset any request handlers that are declared during tests
afterEach(() => server.resetHandlers());

// Clean up after all tests are finished
afterAll(() => server.close());

// Mock window.matchMedia (required for components using media queries)
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: jest.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(), // deprecated
    removeListener: jest.fn(), // deprecated
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  })),
});

// Mock ResizeObserver (Chart.js)
global.ResizeObserver = jest.fn().mockImplementation(() => ({
  observe: jest.fn(),
  unobserve: jest.fn(),
  disconnect: jest.fn(),
}));

// Mock IntersectionObserver
global.IntersectionObserver = jest.fn().mockImplementation(() => ({
  observe: jest.fn(),
  unobserve: jest.fn(),
  disconnect: jest.fn(),
}));

// Suppress console warnings in tests unless explicitly needed
const originalWarn = console.warn;
beforeAll(() => {
  console.warn = (...args: any[]) => {
    if (!args[0]?.includes?.('Warning:')) {
      originalWarn(...args);
    }
  };
});

afterAll(() => {
  console.warn = originalWarn;
});

// Set test environment variables
process.env.REACT_APP_API_URL = 'http://localhost:8000';