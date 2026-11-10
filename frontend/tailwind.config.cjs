// Tailwind configuration
module.exports = {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}"
  ],
  theme: {
    extend: {
      colors: {
        primary: "#3F51B5", // deep indigo
        secondary: "#2196F3", // blue
        accent: "#9C27B0", // purple
        cyan: "#00BCD4",
        success: "#4CAF50",
        warning: "#FFC107",
        error: "#F44336"
      }
    }
  },
  plugins: []
};
