import React from 'react';

interface LogoProps {
  className?: string;
  color?: string;
}

export const PaknSaveLogo: React.FC<LogoProps> = ({ className = "h-4 w-4", color = "#eab308" }) => {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      className={className}
      xmlns="http://www.w3.org/2000/svg"
    >
      {/* Stylized "P$" monogram */}
      <path
        d="M4 4H10C12.2091 4 14 5.79086 14 8C14 10.2091 12.2091 12 10 12H6V20H4V4ZM6 6V10H10C11.1046 10 12 9.10457 12 8C12 6.89543 11.1046 6 10 6H6Z"
        fill={color}
      />
      {/* Dollar sign for savings */}
      <path
        d="M18 3V5C16.3431 5 15 6.34315 15 8C15 9.65685 16.3431 11 18 11C19.6569 11 21 12.3431 21 14C21 15.6569 19.6569 17 18 17V19H17V17C15.3431 17 14 15.6569 14 14H16C16 14.5523 16.4477 15 17 15H18C18.5523 15 19 14.5523 19 14C19 13.4477 18.5523 13 18 13C16.3431 13 15 11.6569 15 10C15 8.34315 16.3431 7 18 7V5H19V7C20.6569 7 22 8.34315 22 10H20C20 9.44772 19.5523 9 19 9H18C17.4477 9 17 9.44772 17 10C17 10.5523 17.4477 11 18 11V13C19.6569 13 21 14.3431 21 16C21 17.6569 19.6569 19 18 19V21H17V19H18V3Z"
        fill={color}
        opacity="0.8"
      />
    </svg>
  );
};

export default React.memo(PaknSaveLogo);
