#pragma once

#include <string>
#include <chrono>

/**
 * Date and time utility functions for the trading platform.
 * Provides standardised date formatting, validation, and current date retrieval.
 */

namespace DateTimeUtils {

/**
 * Get the current date in YYYY-MM-DD format.
 * @return Current date as a string
 */
std::string getCurrentDate();

/**
 * Validate if a date string is in the correct format (YYYY-MM-DD).
 * @param date The date string to validate
 * @return true if the date format is valid, false otherwise
 */
bool isValidDateFormat(const std::string& date);

/**
 * Format a date string, returning the original if valid or current date if invalid.
 * @param date The date string to format
 * @return Formatted date string
 */
std::string formatDate(const std::string& date);

/**
 * Convert a date string to a time_point for calculations.
 * @param date The date string in YYYY-MM-DD format
 * @return time_point representing the date
 */
std::chrono::system_clock::time_point stringToTimePoint(const std::string& date);

/**
 * Convert a time_point to a date string in YYYY-MM-DD format.
 * @param time_point The time_point to convert
 * @return Date string in YYYY-MM-DD format
 */
std::string timePointToString(const std::chrono::system_clock::time_point& time_point);

} // namespace DateTimeUtils