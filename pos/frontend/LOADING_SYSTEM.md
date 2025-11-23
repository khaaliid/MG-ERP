# Loading System Implementation

## Overview
The POS system now includes a comprehensive loading screen system that automatically displays during all backend operations.

## Features
- ✅ Global loading overlay with transparent background
- ✅ Automatic loading states for all API calls
- ✅ Custom loading messages for different operations
- ✅ Support for custom transparent GIF animations
- ✅ Fallback SVG animation when no GIF is provided

## How It Works

### 1. Loading Context
- **File**: `src/contexts/LoadingContext.tsx`
- Manages global loading state across the entire application
- Provides methods to show/hide loading with custom messages

### 2. Enhanced API Service
- **File**: `src/services/enhancedApiService.ts`
- Wraps the original API service with automatic loading states
- Shows appropriate loading messages for each operation:
  - "Signing in..." for login
  - "Loading products..." for product fetching
  - "Processing sale..." for checkout
  - And many more...

### 3. Loading Screen Component
- **File**: `src/components/LoadingScreen.tsx`
- Displays the loading overlay with animation
- Supports custom GIF URLs or uses default SVG animation

## Adding Your Own Loading GIF

### Option 1: Replace the default animation
1. Place your transparent GIF in `public/` folder (e.g., `public/my-loading.gif`)
2. In `src/App.tsx`, update the LoadingScreen component:
```tsx
<LoadingScreen 
  gifUrl="/my-loading.gif"  // Your GIF path
/>
```

### Option 2: Use different GIFs for different contexts
You can customize the loading screen for specific operations by modifying the `enhancedApiService.ts` file.

## Current Loading Messages

| Operation | Message |
|-----------|---------|
| Login | "Signing in..." |
| Logout | "Signing out..." |
| Load Products | "Loading products..." |
| Search Products | "Searching products..." |
| Create Sale | "Processing sale..." |
| Load Sales History | "Loading sales history..." |
| Void Sale | "Voiding sale..." |
| Process Refund | "Processing refund..." |
| Generate Reports | "Generating sales report..." |
| System Health Check | "Checking system status..." |

## Technical Implementation

### Components Updated
- ✅ `App.tsx` - Added LoadingProvider and LoadingScreen
- ✅ `AuthContext.tsx` - Uses enhanced API service
- ✅ `POS.tsx` - Uses enhanced API service
- ✅ `SalesHistory.tsx` - Uses enhanced API service  
- ✅ `Reports.tsx` - Uses enhanced API service

### Loading States Handled
- ✅ Authentication (login/logout)
- ✅ Product loading and searching
- ✅ Category and brand loading
- ✅ Sale creation and processing
- ✅ Sales history retrieval
- ✅ Report generation
- ✅ Void and refund operations
- ✅ Health checks

## File Structure
```
src/
├── components/
│   ├── LoadingScreen.tsx      # Main loading overlay component
│   └── LoadingSpinner.tsx     # Reusable spinner component
├── contexts/
│   └── LoadingContext.tsx     # Global loading state management
├── services/
│   ├── apiService.ts          # Original API service
│   └── enhancedApiService.ts  # API service with loading states
└── App.tsx                    # Updated with loading integration

public/
└── loading.svg                # Default loading animation
```

## Usage Examples

### Manual Loading Control (if needed)
```tsx
import { useLoading } from '../contexts/LoadingContext';

const MyComponent = () => {
  const { showLoading, hideLoading } = useLoading();
  
  const handleCustomOperation = async () => {
    showLoading("Processing custom operation...");
    try {
      // Your async operation
      await customApiCall();
    } finally {
      hideLoading();
    }
  };
};
```

### Custom Loading Message
```tsx
// In enhancedApiService.ts
async customOperation(): Promise<any> {
  return this.withLoading(
    () => apiService.customOperation(),
    'Your custom loading message...'
  );
}
```

## Customization Options

### Loading Screen Styling
The loading screen can be customized in `LoadingScreen.tsx`:
- Background opacity
- Animation size and colors
- Message styling
- Positioning

### Custom Animations
- Place your GIF in the `public/` folder
- Update the `gifUrl` prop in `App.tsx`
- Ensure your GIF has a transparent background for best results

## Benefits
1. **Better UX**: Users see immediate feedback for all operations
2. **Consistent**: All API calls automatically show loading states
3. **Customizable**: Easy to add custom GIFs and messages
4. **Maintainable**: Centralized loading logic
5. **Professional**: Polished loading experience