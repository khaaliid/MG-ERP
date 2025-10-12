# POS Frontend

This is the frontend for the MG-ERP Point of Sale (POS) system built with React and TypeScript.

## Features

- **Product Management**: Add, edit, and delete products with stock tracking
- **Sales Interface**: Modern POS interface with product search and cart management
- **Checkout System**: Support for multiple payment methods (cash, card, mobile)
- **Sales History**: View all sales with detailed transaction information
- **Real-time Stock Updates**: Automatic stock quantity updates after sales

## Tech Stack

- React 18
- TypeScript
- Tailwind CSS
- Vite (build tool)
- React Router

## Getting Started

### Prerequisites

- Node.js 18 or higher
- npm or yarn

### Installation

1. Install dependencies:
```bash
npm install
```

2. Start the development server:
```bash
npm run dev
```

The application will be available at `http://localhost:3001`

### Building for Production

```bash
npm run build
```

## API Configuration

The frontend is configured to connect to the POS backend API at `http://localhost:8001`. Make sure the backend server is running before using the application.

## Features Overview

### Main POS Interface (`/`)
- Product grid with search functionality
- Shopping cart with quantity management
- Real-time checkout process
- Payment method selection
- Change calculation for cash payments

### Product Management (`/products`)
- CRUD operations for products
- Stock quantity tracking
- Category management
- Barcode support

### Sales History (`/sales`)
- Complete sales transaction history
- Daily sales summary
- Detailed view of individual sales
- Payment method filtering

## Environment Variables

Create a `.env` file in the root directory if you need to configure different API endpoints:

```
VITE_API_URL=http://localhost:8001
```

## Contributing

1. Follow TypeScript best practices
2. Use Tailwind CSS for styling
3. Ensure responsive design for all components
4. Add proper error handling for API calls