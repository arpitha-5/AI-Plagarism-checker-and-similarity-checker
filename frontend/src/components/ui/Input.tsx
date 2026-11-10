import React from 'react';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label: string;
  error?: string;
}

export const Input: React.FC<InputProps> = ({ label, error, className = '', ...props }) => {
  const base = 'w-full rounded border p-2 focus:outline-none focus:ring-2 focus:ring-primary';
  return (
    <div className={`mb-4 ${className}`}>
      <label className="block text-sm font-medium mb-1 text-gray-700">{label}</label>
      <input className={`${base} ${error ? 'border-red-500' : 'border-gray-300'}`} {...props} />
      {error && <p className="mt-1 text-sm text-red-600">{error}</p>}
    </div>
  );
};
