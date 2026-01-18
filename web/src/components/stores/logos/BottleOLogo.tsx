import React from 'react';

interface LogoProps {
  className?: string;
  color?: string;
}

export const BottleOLogo: React.FC<LogoProps> = ({ className = "h-4 w-4", color = "#f97316" }) => {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      className={className}
      xmlns="http://www.w3.org/2000/svg"
    >
      {/* Bottle icon */}
      <path
        d="M10 2H14V4H15C15.5523 4 16 4.44772 16 5V7C16 7.55228 15.5523 8 15 8H15.5C16.8807 8 18 9.11929 18 10.5V20C18 21.1046 17.1046 22 16 22H8C6.89543 22 6 21.1046 6 20V10.5C6 9.11929 7.11929 8 8.5 8H9C8.44772 8 8 7.55228 8 7V5C8 4.44772 8.44772 4 9 4H10V2ZM10 4V6H14V4H10ZM8.5 10C8.22386 10 8 10.2239 8 10.5V20H16V10.5C16 10.2239 15.7761 10 15.5 10H8.5Z"
        fill={color}
      />
      {/* Circle for "O" */}
      <circle cx="19" cy="5" r="2.5" stroke={color} strokeWidth="1.5" fill="none" />
    </svg>
  );
};

export default React.memo(BottleOLogo);
