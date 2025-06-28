// Focused service for handling simulation status polling
export class PollingService {
  private pollingInterval?: NodeJS.Timeout;
  private pollingIntervalMs: number = 2000; // Default 2 seconds

  // Start polling with a callback function
  startPolling(pollFunction: () => Promise<void>, intervalMs?: number): void {
    this.stopPolling(); // Stop any existing polling
    
    const interval = intervalMs || this.pollingIntervalMs;
    this.pollingInterval = setInterval(async () => {
      try {
        await pollFunction();
      } catch (error) {
        console.error('Polling error:', error);
        // Continue polling even if one request fails
      }
    }, interval);
  }

  // Stop polling
  stopPolling(): void {
    if (this.pollingInterval) {
      clearInterval(this.pollingInterval);
      this.pollingInterval = undefined;
    }
  }

  // Check if currently polling
  isPolling(): boolean {
    return this.pollingInterval !== undefined;
  }

  // Set polling interval
  setPollingInterval(intervalMs: number): void {
    this.pollingIntervalMs = intervalMs;
  }

  // Get current polling interval
  getPollingInterval(): number {
    return this.pollingIntervalMs;
  }

  // Cleanup
  cleanup(): void {
    this.stopPolling();
  }
}

export const pollingService = new PollingService();