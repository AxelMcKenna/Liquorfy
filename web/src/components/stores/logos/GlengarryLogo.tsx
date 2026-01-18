import React from 'react';

interface LogoProps {
  className?: string;
  color?: string;
}

export const GlengarryLogo: React.FC<LogoProps> = ({ className = "h-4 w-4", color = "#ec4899" }) => {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      className={className}
      xmlns="http://www.w3.org/2000/svg"
    >
      {/* Wine glass icon */}
      <path
        d="M11 2H13V4H17C17.5523 4 18 4.44772 18 5C18 8.31371 15.3137 11 12 11C8.68629 11 6 8.31371 6 5C6 4.44772 6.44772 4 7 4H11V2ZM8.25 6C8.67053 7.74163 10.1808 9 12 9C13.8192 9 15.3295 7.74163 15.75 6H8.25Z"
        fill={color}
      />
      <rect x="11" y="11" width="2" height="9" fill={color} />
      <rect x="8" y="20" width="8" height="2" rx="1" fill={color} />
    </svg>
  );
};

export default React.memo(GlengarryLogo);
