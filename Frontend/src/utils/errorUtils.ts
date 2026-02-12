/**
 * Extracts a user-friendly error message from various error response formats
 * Handles string errors, validation error arrays, and error objects
 */
export const extractErrorMessage = (error: any, defaultMessage: string = 'An error occurred'): string => {
  // Check if there's a response with detail
  if (error.response?.data?.detail) {
    const detail = error.response.data.detail
    
    // If detail is a string, clean it up and use it
    if (typeof detail === 'string') {
      return cleanErrorMessage(detail)
    }
    
    // If detail is an array of validation errors (Pydantic format), format them
    if (Array.isArray(detail)) {
      return detail.map((err: any) => {
        if (typeof err === 'string') return cleanErrorMessage(err)
        if (err.msg) return cleanErrorMessage(err.msg)
        if (err.message) return cleanErrorMessage(err.message)
        return 'Validation error'
      }).join(', ')
    }
    
    // If detail is an object, try to extract message
    if (typeof detail === 'object') {
      const message = detail.msg || detail.message || defaultMessage
      return cleanErrorMessage(message)
    }
  }
  
  // Fallback to error message or default
  return cleanErrorMessage(error.message || defaultMessage)
}

/**
 * Cleans up backend error messages to extract only user-friendly content
 * Removes technical prefixes and error codes
 */
const cleanErrorMessage = (message: string): string => {
  // Common patterns to clean up
  const patterns = [
    // Remove "Password verification error: 401: " prefix
    /^Password verification error:\s*\d+:\s*/i,
    // Remove "Database error: " prefix  
    /^Database error:\s*/i,
    // Remove "Authentication error: " prefix
    /^Authentication error:\s*/i,
    // Remove "Validation error: " prefix
    /^Validation error:\s*/i,
    // Remove HTTP status codes at the beginning
    /^\d{3}:\s*/,
    // Remove technical error prefixes
    /^Error:\s*/i,
    /^HTTPException:\s*/i,
    // Remove backend trace info patterns
    /\(.*?\)\s*$/,
  ]
  
  let cleanMessage = message.trim()
  
  // Apply all cleaning patterns
  patterns.forEach(pattern => {
    cleanMessage = cleanMessage.replace(pattern, '')
  })
  
  // If the message is now empty or too short, return a generic message
  if (!cleanMessage || cleanMessage.length < 3) {
    return 'An error occurred'
  }
  
  // Ensure the first letter is capitalized
  return cleanMessage.charAt(0).toUpperCase() + cleanMessage.slice(1)
}
