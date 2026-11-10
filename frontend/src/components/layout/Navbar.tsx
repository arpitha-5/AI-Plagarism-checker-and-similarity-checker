import { Link } from 'react-router-dom';

export function Navbar() {
  return (
    <nav className="bg-white border-b border-gray-200 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16 items-center">
          <Link to="/" className="flex items-center space-x-2">
            <svg
              className="h-8 w-8 text-primary"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth={2}
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M12 2l9 5-9 5-9-5 9-5z" />
              <path d="M12 22V12" />
            </svg>
            <span className="text-xl font-semibold text-primary">PlagiarismAI</span>
          </Link>
          <div className="hidden md:flex space-x-4 items-center">
            <Link
              to="/"
              className="text-gray-700 hover:text-primary transition"
            >
              Home
            </Link>
            <Link
              to="/login"
              className="text-gray-700 hover:text-primary transition"
            >
              Login
            </Link>
            <Link
              to="/register"
              className="text-gray-700 hover:text-primary transition"
            >
              Register
            </Link>
            <Link
              to="/dashboard"
              className="px-4 py-2 bg-primary text-white rounded hover:bg-indigo-700 transition"
            >
              Dashboard
            </Link>
          </div>
          {/* Mobile menu placeholder */}
        </div>
      </div>
    </nav>
  );
}
