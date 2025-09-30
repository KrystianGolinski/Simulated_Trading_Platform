# Frontend Architecture Technical Documentation

## 1. Introduction

This document provides a technical overview of the React TypeScript frontend for the Simulated Trading Platform. It is intended for developers working on frontend development, maintenance, and feature enhancement.

**Frontend Version:** 0.1.0  
**Framework:** React 19.1.0 with TypeScript 4.9.5  
**Build System:** React Scripts 5.0.1 with Webpack  
**Styling:** Tailwind CSS 4.1.10 with utility-first approach  
**Testing:** Jest with React Testing Library and MSW for API mocking  
**Container:** Docker with Nginx for production deployment  

### 1.1. Core Design Principles

The frontend architecture emphasizes modern React patterns and engineering best practices:

- **Component Composition**: Modular, reusable components with clear separation of concerns
- **Custom Hooks**: Business logic extraction into reusable custom hooks
- **Service Layer Architecture**: Clean separation of API communication from UI components
- **Type Safety**: Comprehensive TypeScript integration with strict compiler settings
- **State Management**: Local state with React hooks and service-based state orchestration
- **Performance Optimization**: Lazy loading, memoization, and debouncing for optimal UX
- **Test Coverage**: Comprehensive testing with unit tests and integration tests
- **Responsive Design**: Mobile-first responsive design with Tailwind CSS utilities

### 1.2. Key Directory Structure

#### Core Application Structure
- `src/App.tsx`: Main application component with lazy loading and route management
- `src/index.tsx`: Application entry point with React 19 concurrent features
- `src/index.css`: Global styles and Tailwind CSS imports

#### Component Architecture
- `src/components/`: UI components organized by feature
  - `Dashboard.tsx`: Interactive stock data visualization dashboard
  - `SimulationSetup.tsx`: Simulation configuration and parameter input
  - `SimulationProgress.tsx`: Real-time simulation progress tracking
  - `SimulationResults.tsx`: Simulation results display with performance metrics
  - `StockChart.tsx`: Advanced charting component with multiple visualization types
  - `common/`: Reusable UI components and utilities
    - `Alert.tsx`, `Button.tsx`, `Card.tsx`: Base UI components
    - `DateRangeSelector.tsx`: Date range input component
    - `Pagination.tsx`: Data pagination component
    - `LoadingWrapper.tsx`, `Spinner.tsx`: Loading state components

#### Custom Hooks Layer
- `src/hooks/`: Custom React hooks for business logic
  - `useSimulation.ts`: Simulation lifecycle management and state coordination
  - `useStockData.ts`: Stock data fetching with caching and error handling
  - `useDebounce.ts`: Input debouncing for performance optimization
  - `usePagination.ts`: Pagination state management

#### Service Architecture
- `src/services/`: Service layer for external communication
  - `api.ts`: Core API client with TypeScript interfaces
  - `simulation/`: Simulation-specific service modules
    - `simulationService.ts`: Simulation orchestrator service
    - `simulationAPI.ts`: Simulation API communication layer
    - `simulationState.ts`: Simulation state management
    - `pollingService.ts`: Real-time status polling service

#### Type Definitions
- `src/types/`: TypeScript type definitions
  - `pagination.ts`: Pagination type definitions and utilities

#### Testing Infrastructure
- `src/__mocks__/`: Mock service workers and test handlers
- `src/components/__tests__/`: Component unit tests
- `src/services/__tests__/`: Service layer integration tests

## 2. Architecture

The frontend implements a modern React architecture with service-oriented design patterns and comprehensive state management.

### 2.1. Application Flow

1. **Application Bootstrap**: React 19 concurrent features initialization with error boundaries
2. **Route Management**: State-based navigation between Setup, Progress, Results, and Dashboard views
3. **Service Initialization**: API client initialization with environment configuration
4. **State Hydration**: Service layer state initialization and subscription setup
5. **Component Rendering**: Lazy-loaded components with Suspense boundaries
6. **Event Handling**: User interactions processed through custom hooks
7. **API Communication**: Service layer handles all external communication
8. **State Updates**: Reactive state updates propagated to subscribed components
9. **Real-time Updates**: Polling service provides live simulation progress updates

### 2.2. Component Architecture

The frontend uses a hierarchical component structure with clear data flow:

```
App (Main Router)
├── SimulationSetup (Configuration)
│   ├── FormInput (Reusable)
│   ├── DateRangeSelector (Common)
│   └── ErrorAlert (Common)
├── SimulationProgress (Real-time Monitoring)
│   ├── LoadingWrapper (Common)
│   └── Spinner (Common)
├── SimulationResults (Results Display)
│   ├── StockChart (Visualization)
│   ├── Pagination (Common)
│   └── Card (Common)
└── Dashboard (Data Exploration)
    ├── StockChart (Shared Visualization)
    ├── DateRangeSelector (Common)
    └── LoadingWrapper (Common)
```

### 2.3. State Management Strategy

**Local Component State:**
- Form inputs and UI state managed with `useState`
- Complex state logic extracted to custom hooks
- State updates optimized with `useCallback` and `useMemo`

**Service Layer State:**
- Simulation state centrally managed in `simulationService`
- Observer pattern with subscription/unsubscription lifecycle
- State persistence across component remounts

**Async State Management:**
- Loading states handled consistently across all async operations
- Error boundaries with user-friendly error messages
- Optimistic updates where appropriate

## 3. Component Reference

### 3.1. Core Application Components

#### SimulationSetup
**Purpose**: Simulation configuration and parameter input
**Features**:
- Dynamic strategy parameter validation
- Stock symbol selection with validation
- Date range selection with business rule validation
- Real-time form validation with error display
- Integration with simulation service for execution

#### SimulationProgress
**Purpose**: Real-time simulation monitoring
**Features**:
- Live progress percentage updates via polling service
- Estimated completion time calculation
- Current processing status display
- Cancellation support with confirmation
- Error state handling with retry options

#### SimulationResults
**Purpose**: Comprehensive results display and analysis
**Features**:
- Performance metrics visualization
- Trade history with pagination
- Interactive charts with multiple visualization modes
- Export functionality for further analysis
- Results comparison capabilities

#### Dashboard
**Purpose**: Interactive stock data exploration
**Features**:
- Stock symbol search and selection
- Multiple chart types (line, candlestick, OHLC)
- Date range filtering with presets
- Volume overlay capabilities
- Responsive design for all screen sizes

#### StockChart
**Purpose**: Advanced financial data visualization
**Features**:
- Chart.js integration with financial data adapters
- Multiple chart types with smooth transitions
- Zoom and pan functionality
- Tooltip with comprehensive data display
- Performance optimized for large datasets

### 3.2. Custom Hooks

#### useSimulation
**Purpose**: Simulation lifecycle management
**Features**:
- Simulation start/cancel/reset operations
- State subscription with automatic updates
- Error handling with user-friendly messages
- Service cleanup on component unmount

#### useStockData
**Purpose**: Stock data fetching and caching
**Features**:
- Debounced API calls for performance
- Automatic retry on failure
- Loading state management
- Error state with recovery options

#### useDebounce
**Purpose**: Input debouncing for performance optimization
**Features**:
- Configurable delay periods
- Automatic cleanup on unmount
- TypeScript generic support for any value type

### 3.3. Service Layer

#### SimulationService
**Purpose**: Simulation orchestration and state management
**Architecture**:
- Observer pattern for state updates
- Service composition with API and polling services
- Error handling with recovery strategies
- State persistence across sessions

#### PollingService
**Purpose**: Real-time status updates
**Features**:
- Configurable polling intervals
- Automatic backoff on errors
- Pause/resume capabilities
- Connection status monitoring

#### API Service
**Purpose**: HTTP client for API communication
**Features**:
- TypeScript interfaces for all API endpoints
- Request/response validation
- Error categorization and handling
- Environment-based configuration

## 4. Development Patterns

### 4.1. TypeScript Integration

**Strict Configuration:**
- `strict: true` for maximum type safety
- `noUnusedLocals` and `noUnusedParameters` for code quality
- `noFallthroughCasesInSwitch` for switch statement safety

**Type Definitions:**
- Interface definitions for all API responses
- Generic types for reusable components
- Union types for state enums and status values

### 4.2. Performance Optimization

**Component Optimization:**
- `React.memo` for expensive rendering components
- `useCallback` and `useMemo` for expensive calculations
- Lazy loading with `React.lazy` and `Suspense`

**Network Optimization:**
- Request debouncing for user input
- Response caching for frequently accessed data
- Pagination for large datasets

### 4.3. Error Handling

**Error Boundaries:**
- Global error boundary for unhandled exceptions
- Service-level error handling with categorization
- User-friendly error messages with recovery actions

**Validation:**
- Client-side form validation before submission
- API response validation with TypeScript interfaces
- Input sanitization for security

## 5. Testing Strategy

### 5.1. Unit Testing

**Component Testing:**
- React Testing Library for user-interaction testing
- Jest for test runner and assertion library
- MSW (Mock Service Worker) for API mocking

**Hook Testing:**
- Custom hook testing with `@testing-library/react-hooks`
- Mock service dependencies for isolated testing
- Async behavior testing with proper cleanup

### 5.2. Integration Testing

**Service Integration:**
- End-to-end service communication testing
- Error scenario testing with network failures
- State management testing across service boundaries

### 5.3. Test Infrastructure

**Mock Service Workers:**
- API response mocking for consistent testing
- Error simulation for error handling validation
- Performance testing with delayed responses

## 6. Build and Deployment

### 6.1. Development Environment

**Build Configuration:**
- React Scripts with TypeScript support
- Hot module replacement for fast development
- Source maps for debugging

**Development Server:**
- Local development server on port 3000
- Proxy configuration for API calls
- Environment variable support for configuration

### 6.2. Production Deployment

**Docker Container:**
- Multi-stage build for size optimization
- Nginx server for static file serving
- Health checks for container orchestration

**Build Optimization:**
- Bundle analysis with webpack-bundle-analyzer
- Code splitting for optimal loading
- Asset optimization and compression

### 6.3. Environment Configuration

**Environment Variables:**
- `REACT_APP_API_URL`: API base URL configuration
- Build-time environment variable injection
- Container environment variable support

**Configuration Management:**
- Separate configurations for development and production
- API endpoint configuration via environment
- Feature flag support for gradual rollouts