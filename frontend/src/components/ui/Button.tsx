import React from 'react';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline';
  loading?: boolean;
  children: React.ReactNode;
}

export const Button: React.FC<ButtonProps> = ({
  variant = 'primary',
  loading = false,
  className = '',
  disabled,
  children,
  ...props
}) => {
  const base = 'px-4 py-2 font-medium rounded transition disabled:opacity-50 disabled:cursor-not-allowed';
  const variants = {
    primary: 'bg-primary text-white hover:bg-indigo-700',
    secondary: 'bg-secondary text-white hover:bg-blue-600',
    outline: 'border border-primary text-primary hover:bg-primary/10',
  };

  return (
    <button
      className={`${base} ${variants[variant]} ${className}`}
      disabled={disabled || loading}
      {...props}
    >
      {loading ? (
        <svg className="animate-spin h-5 w-5 mr-2 inline" viewBox="0 0 24 24">
          <circle
            className="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            strokeWidth="4"
          ></circle>
          <path
            className="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8v8H4z"
          ></path>
        </svg>
      ) : null}
      {children}
    </button>
  );
};
