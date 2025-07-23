/**
 * Auth utility functions
 */

/**
 * Get the current auth token from local storage
 */
export async function getAuthToken(): Promise<string | null> {
  try {
    // Get token from localStorage
    const token = localStorage.getItem('access_token');
    return token;
  } catch (error) {
    console.error('Failed to get auth token:', error);
    return null;
  }
}

/**
 * Set the auth token in local storage
 */
export function setAuthToken(token: string): void {
  localStorage.setItem('access_token', token);
}

/**
 * Remove the auth token from local storage
 */
export function removeAuthToken(): void {
  localStorage.removeItem('access_token');
}