import React from 'react';

interface LogoProps {
  className?: string;
  color?: string;
}

export const SuperLiquorLogo: React.FC<LogoProps> = ({ className = "h-4 w-4", color = "#ef4444" }) => {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      className={className}
      xmlns="http://www.w3.org/2000/svg"
    >
      {/* Stylized "SL" monogram */}
      <path
        d="M7 6C7 4.89543 7.89543 4 9 4H11C12.1046 4 13 4.89543 13 6C13 7.10457 12.1046 8 11 8H9V10H11C13.2091 10 15 8.20914 15 6C15 3.79086 13.2091 2 11 2H9C6.79086 2 5 3.79086 5 6V10C5 11.1046 5.89543 12 7 12H11C12.1046 12 13 12.8954 13 14C13 15.1046 12.1046 16 11 16H9C7.89543 16 7 15.1046 7 14H5C5 16.2091 6.79086 18 9 18H11C13.2091 18 15 16.2091 15 14C15 11.7909 13.2091 10 11 10H7V6Z"
        fill={color}
      />
      <path
        d="M17 4H19V18H23V20H17V4Z"
        fill={color}
      />
    </svg>
  );
};

export default React.memo(SuperLiquorLogo);
