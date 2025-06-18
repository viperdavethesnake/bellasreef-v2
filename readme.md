# Bella's Reef - Reef Tank Management System

A comprehensive reef tank management system for tracking and maintaining your aquarium's health and parameters.

## Project Structure

```
bellasreef-v2/
├── backend/               # Backend API server
│   ├── src/
│   │   ├── controllers/  # Route controllers
│   │   ├── models/      # Database models
│   │   ├── routes/      # API routes
│   │   ├── services/    # Business logic
│   │   ├── utils/       # Utility functions
│   │   ├── middleware/  # Custom middleware
│   │   ├── config/      # Configuration files
│   │   └── tests/       # Backend tests
│   └── docs/            # Backend documentation
│
└── frontend/            # React frontend application
    ├── src/
    │   ├── components/  # Reusable components
    │   ├── pages/      # Page components
    │   ├── services/   # API services
    │   ├── utils/      # Utility functions
    │   ├── hooks/      # Custom React hooks
    │   ├── styles/     # CSS and styling
    │   ├── assets/     # Static assets
    │   ├── context/    # React context
    │   └── tests/      # Frontend tests
```

## Setup Instructions

### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Create a .env file based on .env.example:
   ```bash
   cp .env.example .env
   ```

4. Start the development server:
   ```bash
   npm run dev
   ```

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Create a .env file based on .env.example:
   ```bash
   cp .env.example .env
   ```

4. Start the development server:
   ```bash
   npm run dev
   ```

## Features

- Tank parameter tracking (temperature, salinity, pH, etc.)
- Equipment monitoring and maintenance scheduling
- Livestock management
- Water change tracking
- Feeding schedule management
- Test result logging
- Maintenance task scheduling
- Data visualization and reporting

## Tech Stack

### Backend
- Node.js
- Express.js
- MongoDB
- JWT Authentication

### Frontend
- React
- Vite
- TailwindCSS
- Chart.js
- React Router

## Contributing

Please read our contributing guidelines before submitting pull requests.

## License

This project is licensed under the MIT License.

