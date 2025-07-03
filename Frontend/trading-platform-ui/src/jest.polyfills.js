
// Polyfills for MSW v2 compatibility

// Core web APIs needed by MSW 
const { TextEncoder, TextDecoder } = require('util');

// Stream APIs for MSW interceptors
let ReadableStream, WritableStream, TransformStream;
try {
  ({ ReadableStream, WritableStream, TransformStream } = require('node:stream/web'));
} catch (e) {
  // Fallback for older Node versions
  ReadableStream = class ReadableStream {};
  WritableStream = class WritableStream {};
  TransformStream = class TransformStream {};
}

// Crypto API for MSW
const { webcrypto } = require('node:crypto');

// Apply all polyfills to global scope
Object.assign(global, {
  TextEncoder,
  TextDecoder,
  ReadableStream,
  WritableStream,
  TransformStream,
  crypto: webcrypto,
  
  // Mock fetch API if not available
  fetch: global.fetch || (() => Promise.reject(new Error('fetch not available in test environment'))),
  Request: global.Request || class Request {},
  Response: global.Response || class Response {},
  Headers: global.Headers || class Headers {},
  
  // Additional browser APIs that might be needed
  AbortController: global.AbortController || class AbortController {
    constructor() {
      this.signal = { aborted: false, addEventListener: () => {}, removeEventListener: () => {} };
    }
    abort() {
      this.signal.aborted = true;
    }
  },
  
  // Performance API
  performance: global.performance || {
    now: () => Date.now(),
    mark: () => {},
    measure: () => {},
  },
  
  // URL API
  URL: global.URL || class URL {
    constructor(url, base) {
      this.href = url;
      this.origin = '';
      this.protocol = '';
      this.host = '';
      this.pathname = '';
      this.search = '';
      this.hash = '';
    }
  },
  URLSearchParams: global.URLSearchParams || class URLSearchParams {
    constructor() {
      this.params = new Map();
    }
    append(key, value) {
      this.params.set(key, value);
    }
    get(key) {
      return this.params.get(key);
    }
    toString() {
      return '';
    }
  }
});

// Node.js environment fixes
if (typeof process !== 'undefined' && process.env.NODE_ENV === 'test') {
  const originalConsoleWarn = console.warn;
  console.warn = (...args) => {
    const message = args[0];
    if (typeof message === 'string' && (
      message.includes('MSW') ||
      message.includes('interceptor') ||
      message.includes('tough-cookie')
    )) {
      return; // Suppress MSW-related warnings
    }
    originalConsoleWarn.apply(console, args);
  };
}