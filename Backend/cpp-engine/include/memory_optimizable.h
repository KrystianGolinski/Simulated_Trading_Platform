#pragma once

#include <cstddef>
#include <string>

/**
 * Interface for classes that support memory optimization.
 * Provides a standardized way to optimize memory usage across all services.
 */
class IMemoryOptimizable {
public:
    virtual ~IMemoryOptimizable() = default;
    
    /**
     * Optimizes memory usage by shrinking containers and clearing unused data.
     * Should be called periodically to reduce memory footprint.
     */
    virtual void optimizeMemory() = 0;
    
    /**
     * Returns the estimated memory usage in bytes.
     * Used for monitoring and optimization decisions.
     */
    virtual size_t getMemoryUsage() const = 0;
    
    /**
     * Returns a detailed memory usage report as a string.
     * Used for debugging and performance analysis.
     */
    virtual std::string getMemoryReport() const = 0;
};