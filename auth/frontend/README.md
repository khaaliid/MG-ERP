# MG-ERP Auth Frontend

Admin dashboard for managing MG-ERP authentication and users.

## Features

- 🔐 User authentication with JWT
- 👥 User management dashboard
- 🎨 Modern UI with Tailwind CSS
- ⚡ Fast development with Vite
- 🐳 Docker support

## Development

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

## Environment Variables

Create a `.env` file based on `.env.example`:

```env
VITE_API_BASE_URL=http://localhost:8004/api/v1
```

## Docker Build

```bash
# Build image
docker build -t mg-auth-frontend:latest .

# Run container
docker run -p 3000:80 mg-auth-frontend:latest
```

## Project Structure

```
src/
├── components/       # Reusable components
│   └── ProtectedRoute.tsx
├── context/         # React context providers
│   └── AuthContext.tsx
├── pages/           # Page components
│   ├── Login.tsx
│   └── Dashboard.tsx
├── services/        # API services
│   └── apiService.ts
├── App.tsx          # Main app component
├── main.tsx         # Entry point
└── index.css        # Global styles
```

## Technology Stack

- React 18
- TypeScript
- Vite
- React Router
- Axios
- Tailwind CSS
- Nginx (production)
