# Tech Stack

## Backend
- **Framework**: FastAPI
- **Server**: Uvicorn
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Authentication**: JWT (JSON Web Tokens) with python-jose
- **Password Hashing**: bcrypt via passlib
- **Caching**: Redis with hiredis
- **Background Tasks**: Celery with Flower monitoring
- **Validation**: Pydantic
- **Environment Management**: python-dotenv
- **File Processing**: 
  - openpyxl (Excel files)
  - pandas (Data manipulation)
- **Date/Time**: python-dateutil
- **Database Drivers**: psycopg2-binary, asyncpg

## Frontend
- **Framework**: React 18.3.1 with TypeScript
- **Build Tool**: Vite
- **Routing**: React Router DOM
- **State Management**: Zustand
- **Data Fetching**: TanStack React Query with Axios
- **Form Handling**: React Hook Form with Zod validation
- **UI Components**: Radix UI primitives
- **Styling**: Tailwind CSS with tailwindcss-animate
- **Charts**: 
  - Chart.js with react-chartjs-2
  - Recharts
- **Icons**: Lucide React
- **Date Handling**: date-fns with react-day-picker
- **File Upload**: react-dropzone
- **Notifications**: react-hot-toast
- **Loading States**: react-loading-skeleton
- **File Processing**: xlsx for Excel file handling

## Development Tools
- **Linting**: ESLint with TypeScript ESLint
- **Styling**: PostCSS with Autoprefixer
- **Type Checking**: TypeScript
- **Code Quality**: React hooks and refresh plugins